import io
import json
import os
from datetime import datetime
from pathlib import Path

import datetime as _dt
import openpyxl
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from requests.auth import HTTPBasicAuth

from backend.models.bsid_odata import BSID_TO_ODATA
from backend.services import file_store
from backend.config import AR_TEMPLATE_PATH
from backend.services.ar_processor import (
    EccDataError, TemplateError, process_ar_records,
)
from backend.services.ar_validate import validate_ar_files

# ---------------------------------------------------------------------------
# OData V2 date handling
# ---------------------------------------------------------------------------

def _date_to_odata_v2(value):
    """
    SAP Gateway's OData V2 wire format for Edm.DateTime is /Date(ms)/, where
    ms is milliseconds since 1970-01-01 00:00:00 UTC. Dates are treated as
    midnight UTC.
    """
    epoch = _dt.datetime(1970, 1, 1, tzinfo=_dt.timezone.utc)

    if isinstance(value, _dt.datetime):
        moment = value if value.tzinfo else value.replace(tzinfo=_dt.timezone.utc)
    elif isinstance(value, _dt.date):
        moment = _dt.datetime(value.year, value.month, value.day,
                              tzinfo=_dt.timezone.utc)
    else:
        raise TypeError(f"not a date: {value!r}")

    millis = int((moment - epoch).total_seconds() * 1000)
    return f"/Date({millis})/"


class _SapJsonEncoder(json.JSONEncoder):
    """Serializes dates the way SAP Gateway's OData V2 runtime expects."""
    def default(self, obj):
        if isinstance(obj, (_dt.date, _dt.datetime)):
            return _date_to_odata_v2(obj)
        return super().default(obj)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()
router = APIRouter()

# ECC source (BSID) — used only by GET /ar/ecc_data
ODATA_URL = (
    "http://ec2-54-158-63-191.compute-1.amazonaws.com:8080/"
    "sap/opu/odata/SAP/Z_BSID_ODATA_AR1_SRV/ZBSIDItemSet"
)

SAP_USERNAME = os.getenv("SAP_USERNAME")
SAP_PASSWORD = os.getenv("SAP_PASSWORD")

# S/4 target — the custom OData service that writes into ZBSID_DEMO_1
S4_SERVICE_URL = "http://ec2-52-5-159-197.compute-1.amazonaws.com:8080/sap/opu/odata/SAP/ZAR_OPEN_ITEMS_SRV"
S4_ENTITY_SET  = "ZBSID_S4itemsSet"


# Maps the UPPERCASE field names produced by ar_processor.py to the
# camelCase property names SEGW generates for the ZBSID_S4items entity type.

def _augment_key_fields(s4_row):
    """
    ZBSID_DEMO_1 inherits BSID's primary key:
        BUKRS, KUNNR, UMSKS, UMSKZ, AUGDT, AUGBL, ZUONR, GJAHR, BELNR, BUZEI

    The processor emits BUKRS, KUNNR and occasionally ZUONR. Without BELNR,
    GJAHR and BUZEI every row for the same customer collapses to the same
    key, so only the first insert per customer succeeds and the rest get
    'Duplicate resource'. This helper derives the missing key fields from
    data already present in the row.
    """
    row = dict(s4_row)

    # BELNR — the ECC document number. ar_processor stores it in XBLNR
    # (XBLNR_SOURCE_FIELD = "BELNR"). Reuse it as the key field.
    if not row.get("BELNR"):
        row["BELNR"] = row.get("XBLNR", "")

    # GJAHR — fiscal year. Derive from BLDAT if present.
    if not row.get("GJAHR"):
        bldat = row.get("BLDAT")
        if isinstance(bldat, (_dt.date, _dt.datetime)):
            row["GJAHR"] = f"{bldat.year:04d}"
        elif bldat:
            row["GJAHR"] = str(bldat)[:4]

    # BUZEI — line item number. Open items are single-line documents.
    if not row.get("BUZEI"):
        row["BUZEI"] = "1"

    return row


def _to_odata_payload(s4_row):
    """Translate UPPERCASE processor keys into the camelCase OData property
    names SEGW generated. Any key not in BSID_TO_ODATA is skipped."""
    payload = {}
    for key, value in s4_row.items():
        odata_name = BSID_TO_ODATA.get(key)
        if odata_name is None:
            continue          # e.g. 'BL' — not an entity property
        if value == "" or value is None:
            continue          # omit blanks; gateway treats missing as initial

        # SAP Gateway V2 wants Edm.Decimal values as JSON strings formatted
        # to the scale declared in SEGW. Your model declares scale=3 for
        # Dmbtr and Wrbtr, so we emit exactly 3 decimal places.
        if isinstance(value, float):
            value = f"{value:.3f}"

        payload[odata_name] = value
    return payload
def _build_ecc_workbook(records: list[dict]) -> io.BytesIO:
    """Plain single-sheet workbook of the raw ECC rows. No template.

    Skips OData annotations (__metadata) — the processor never reads them
    and openpyxl cannot write a dict into a cell."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ECC_DATA"

    if records:
        # Column order from the first record's keys, minus OData noise.
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
    # dicts, lists, and anything else openpyxl can't serialize
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

    # NEW: stage as Excel in ECC_DATA/
    buffer = _build_ecc_workbook(results)
    filename = f"ECC_AR_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    file_store.save_ecc_workbook(buffer, filename)

    return {
        "status": "ok",
        "file": filename,
        "record_count": len(results),
        "records": results,   # drop this line if the UI no longer needs the rows
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

    return {
        "status": "ok",
        "file": filename,
        "row_count": len(result.s4_rows),
        "warning_count": len(result.warnings),
    }

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

@router.post("/load-to-s4")
def load_to_s4():
    if file_store.latest_s4_file() is None:
        raise HTTPException(409, "No S/4 staging file. Run process first.")

    s4_rows = file_store.load_s4_rows()
    if not s4_rows:
        raise HTTPException(409, "No staged S/4 rows found.")

    warnings = file_store.load_warnings()
    if warnings:
        raise HTTPException(
            status_code=409,
            detail=f"Refusing to load: {len(warnings)} transform warning(s) present.",
        )

    return push_to_s4(s4_rows)


def push_to_s4(s4_rows):
    auth = HTTPBasicAuth(SAP_USERNAME, SAP_PASSWORD)
    session = requests.Session()
    session.auth = auth
    session.verify = False

    # 1. Fetch CSRF token from the SERVICE ROOT
    try:
        r = session.get(
            S4_SERVICE_URL,                           # ← root, not entity set
            headers={"x-csrf-token": "Fetch", "Accept": "application/json"},
            timeout=30,
        )
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"CSRF fetch failed: {e}"}

    csrf_token = r.headers.get("x-csrf-token")
    if not csrf_token:
        return {"status": "error",
                "message": "No CSRF token returned. Check auth and service registration."}

    headers = {
        "x-csrf-token": csrf_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # 2. POST each row to the entity set
    success, errors = 0, []

    for index, row in enumerate(s4_rows):
        # Augment the row with BELNR / GJAHR / BUZEI so the primary key is
        # unique per row. See _augment_key_fields docstring.
        augmented = _augment_key_fields(row)
        payload = _to_odata_payload(augmented)
        body = json.dumps(payload, cls=_SapJsonEncoder)

        # ---- LOGGING: print the first payload in full -----------------
        if index == 0:
            print()
            print("=" * 70)
            print("FIRST PAYLOAD SENT TO S/4")
            print("=" * 70)
            print(f"POST URL: {S4_SERVICE_URL}/{S4_ENTITY_SET}")
            print(f"CSRF token (first 20 chars): {csrf_token[:20]}...")
            print("-" * 70)
            print(json.dumps(payload, cls=_SapJsonEncoder, indent=2))
            print("-" * 70)
            print(f"Raw body length: {len(body)} bytes")
            print("=" * 70)
            print()

        try:
            resp = session.post(
                f"{S4_SERVICE_URL}/{S4_ENTITY_SET}",
                headers=headers,
                data=body,
                timeout=90,       # raised from 30; SAP cold start can be slow
            )
            if resp.status_code == 201:
                success += 1
            else:
                errors.append({
                    "status": resp.status_code,
                    "body": resp.text[:500],
                    "row_belnr": row.get("XBLNR"),
                })
                # ---- LOGGING: show the first failure response ---------
                if len(errors) == 1:
                    print("=" * 70)
                    print("FIRST FAILURE RESPONSE")
                    print("=" * 70)
                    print(f"Status: {resp.status_code}")
                    print(f"Body: {resp.text[:1000]}")
                    print("=" * 70)
        except requests.exceptions.RequestException as e:
            errors.append({"error": str(e), "row_belnr": row.get("XBLNR")})

    return {
        "status": "success" if not errors else "partial_success",
        "success_count": success,
        "error_count": len(errors),
        "errors": errors,
    }