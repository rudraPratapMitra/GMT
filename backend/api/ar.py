import io
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.services import file_store
from backend.config import AR_TEMPLATE_PATH
from backend.services.ar_processor import (
    EccDataError, TemplateError, process_ar_records,
)
from backend.services.ar_validate import validate_ar_files
from backend.services.report_generator import generate_ar_validation_report
from backend.services.validation_workbook import build_validation_workbook

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()
router = APIRouter()

# ECC source (BSID) -- used only by GET /ar/ecc_data
ODATA_URL = (
    "http://ec2-54-158-63-191.compute-1.amazonaws.com:8080/"
    "sap/opu/odata/SAP/Z_BSID_ODATA_AR1_SRV/ZBSIDItemSet"
)

SAP_USERNAME = os.getenv("SAP_USERNAME")
SAP_PASSWORD = os.getenv("SAP_PASSWORD")

REPORTS_DIR = Path("reports")


class DeleteMismatchesPayload(BaseModel):
    # 1-based "record" numbers from a /process response's
    # currency_mismatches, unchanged -- see file_store.remove_ecc_rows().
    record_indices: list[int]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_ecc_workbook(records: list[dict]) -> io.BytesIO:
    """Plain single-sheet workbook of the raw ECC rows. No template."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ECC_DATA"

    if records:
        headers = [k for k in records[0].keys() if k != "__metadata"]
        ws.append(headers)
        for rec in records:
            ws.append([_excel_safe(rec.get(h)) for h in headers])

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return out


def _excel_safe(value):
    """Coerce a value into something openpyxl can write."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _file_info(path: Path | None):
    if path is None:
        return None
    stat = path.stat()
    return {
        "name": path.name,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


_ODATA_DATE_RE = re.compile(r"^/Date\((-?\d+)(?:[+-]\d+)?\)/$")


def _warning_cell(value):
    """
    Like _excel_safe, but turns SAP OData V2 dates ("/Date(1781136000000)/",
    milliseconds since 1970-01-01 UTC) into real Excel dates so the
    warning-rows file is readable. Everything else is passed through.
    """
    if isinstance(value, str):
        m = _ODATA_DATE_RE.match(value.strip())
        if m:
            try:
                return datetime.fromtimestamp(int(m.group(1)) / 1000, tz=timezone.utc).date()
            except (OverflowError, OSError, ValueError):
                return value
    return _excel_safe(value)


def _write_warning_rows_excel(records: list[dict], warnings: list[dict]) -> None:
    """
    Persist the raw ECC rows that carried a warning to
    WARNINGS_DATA/Warning_Rows.xlsx. Reuses the warning["raw"] snapshot
    written by ar_processor.transform_record, so we don't have to re-index
    the ECC workbook.
    """
    if not warnings:
        file_store.clear_warning_rows()
        return

    # Column order comes from the first record's keys, same as the ECC
    # staging file. __metadata is OData noise -- skip it, matching
    # _build_ecc_workbook().
    headers = [k for k in records[0].keys() if k != "__metadata"] if records else []

    # w["raw"] is the *normalized* record (UPPER-CASE keys) while `headers`
    # keep the staging file's original case, so a plain raw.get(h) returned
    # None for every column and produced blank rows. Look up by the record
    # index in the original records instead (fall back to a case-insensitive
    # raw lookup).
    by_record: dict[int, list] = {}
    for w in warnings:
        by_record.setdefault(w.get("record"), []).append(w)

    headers = headers + ["ECC record #", "Warning fields", "Warning messages"]
    rows = []
    for rec_no in sorted(k for k in by_record if k is not None):
        ws_list = by_record[rec_no]
        if 1 <= rec_no <= len(records):
            source = records[rec_no - 1]
        else:
            source = {str(k).upper(): v for k, v in ws_list[0].get("raw", {}).items()}
        source_ci = {str(k).upper(): v for k, v in source.items()}
        rows.append(
            [_warning_cell(source_ci.get(h.upper())) for h in headers[:-3]]
            + [
                rec_no,
                ", ".join(w["field"] for w in ws_list),
                " | ".join(w["message"] for w in ws_list),
            ]
        )

    file_store.save_warning_rows(headers, rows)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/ecc_data")
def get_ar_data():
    try:
        response = requests.get(
            ODATA_URL,
            headers={"Accept": "application/json"},
            auth=(SAP_USERNAME, SAP_PASSWORD),
            params={"$format": "json"},
            verify=False,
            timeout=120,
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="SAP request timed out")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"SAP connection failed: {e}")

    if not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"SAP returned {response.status_code}: {response.text[:200]}",
        )

    try:
        results = response.json()["d"]["results"]
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected SAP response shape: {e}",
        )

    buffer = _build_ecc_workbook(results)
    filename = f"ECC_AR_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    file_store.save_ecc_workbook(buffer, filename)

    return {
        "status": "ok",
        "file": filename,
        "record_count": len(results),
        "records": results,
    }


@router.post("/process")
def process_ar():
    ecc_path = file_store.latest_ecc_file()
    if ecc_path is None:
        raise HTTPException(409, "No ECC file staged. Run fetch first.")

    try:
        records = file_store.read_ecc_workbook(ecc_path)
    except Exception as e:
        raise HTTPException(500, f"Could not read staged ECC file: {e}")

    try:
        result = process_ar_records(records, AR_TEMPLATE_PATH)
    except EccDataError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except TemplateError as e:
        raise HTTPException(status_code=500, detail=f"S/4 template problem: {e}")

    filename = f"AR_S4_Load_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    file_store.save_s4_workbook(
        result.output, filename, result.s4_rows, result.warnings,
    )

    # Warning rows are downloaded as an Excel, not removed from ECC.
    _write_warning_rows_excel(records, result.warnings)

    return {
        "status": "ok",
        "file": filename,
        "row_count": len(result.s4_rows),
        "warning_count": len(result.warnings),
        "currency_mismatches": result.currency_mismatches,
        "deleted_rows_available": file_store.latest_deleted_rows_file() is not None,
        "warning_rows_available": file_store.latest_warning_rows_file() is not None,
        "s4_download_url": "/ar/process/download-s4",
    }


@router.get("/process/download-s4")
def download_s4_workbook():
    """Returns the most recently generated S/4 LTMC workbook."""
    path = file_store.latest_s4_file()
    if path is None:
        raise HTTPException(404, "No S/4 workbook has been generated yet.")
    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        filename=path.name,
    )


@router.get("/process/warning-rows")
def download_warning_rows():
    """Downloads the rows that carried a transform warning, as Excel."""
    path = file_store.latest_warning_rows_file()
    if path is None:
        raise HTTPException(404, "No warning rows exist for the current run.")
    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        filename=path.name,
    )


@router.post("/process/delete-mismatches")
def delete_mismatches_and_process(payload: DeleteMismatchesPayload):
    """
    Removes the given rows from the staged ECC workbook, then reprocesses
    from scratch. NOTE: with the new policy, warnings no longer force a
    delete -- this endpoint remains available only for an explicit,
    user-initiated removal of currency exceptions.
    """
    if not payload.record_indices:
        raise HTTPException(400, "No rows to delete were provided.")

    try:
        file_store.remove_ecc_rows(payload.record_indices)
    except FileNotFoundError as e:
        raise HTTPException(409, str(e))

    return process_ar()


@router.get("/process/deleted-rows")
def download_deleted_rows():
    """Every row removed via Delete & Process during the current session."""
    path = file_store.latest_deleted_rows_file()
    if path is None:
        raise HTTPException(404, "No rows have been deleted in this session yet.")
    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        filename=path.name,
    )


@router.get("/validate/latest")
def validate_latest():
    return {
        "ecc": _file_info(file_store.latest_ecc_file()),
        "s4":  _file_info(file_store.latest_s4_file()),
    }


@router.post("/validate")
def run_validation():
    ecc_path = file_store.latest_ecc_file()
    s4_path  = file_store.latest_s4_file()
    if ecc_path is None or s4_path is None:
        raise HTTPException(409, "Both ECC and S/4 staging files are required.")

    try:
        report = validate_ar_files(str(ecc_path), str(s4_path))
    except ValueError as e:
        raise HTTPException(422, str(e))

    return report


@router.get("/validate/report")
def download_validation_report():
    """Re-runs validation against the currently staged ECC/S/4 files and
    returns a freshly generated PDF report."""
    ecc_path = file_store.latest_ecc_file()
    s4_path  = file_store.latest_s4_file()
    if ecc_path is None or s4_path is None:
        raise HTTPException(409, "Both ECC and S/4 staging files are required.")

    try:
        report_payload = validate_ar_files(str(ecc_path), str(s4_path))
    except ValueError as e:
        raise HTTPException(422, str(e))

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"AR_Validation_Report_{datetime.now():%Y%m%d_%H%M%S}.pdf"

    try:
        pdf_path = generate_ar_validation_report(
            report_payload,
            output_path=output_path,
            source_file_name=ecc_path.name,
            target_file_name=s4_path.name,
        )
    except Exception as e:
        raise HTTPException(500, f"Report generation failed: {e}")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=Path(pdf_path).name,
    )


@router.get("/validate/report-excel")
def download_validation_excel():
    """
    Validation Excel: the S/4 workbook as generated by /process, with the ECC
    source value placed right after each mapped S/4 column (company code,
    customer, document type, payment terms). Companion to the PDF report.
    """
    ecc_path = file_store.latest_ecc_file()
    s4_path  = file_store.latest_s4_file()
    if ecc_path is None or s4_path is None:
        raise HTTPException(409, "Both ECC and S/4 staging files are required.")

    try:
        records = file_store.read_ecc_workbook(ecc_path)
        buffer = build_validation_workbook(s4_path, records)
    except ValueError as e:
        raise HTTPException(409, str(e))
    except Exception as e:
        raise HTTPException(500, f"Validation Excel generation failed: {e}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"AR_Validation_Data_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    output_path.write_bytes(buffer.getvalue())

    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=output_path.name,
    )


@router.post("/load-to-s4")
def load_to_s4():
    """
    Direct load to S/4 has been disabled. The LTMC workbook produced by
    /process is now the deliverable -- download it from
    GET /ar/process/download-s4.
    """
    raise HTTPException(
        status_code=410,
        detail=(
            "Direct S/4 loading has been disabled. Download the generated "
            "LTMC workbook from GET /ar/process/download-s4 and load it "
            "through the standard S/4 import process."
        ),
    )