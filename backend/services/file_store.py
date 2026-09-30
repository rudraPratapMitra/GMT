"""Staging store for ECC_DATA / S4_DATA.

Single-run mode: each folder holds at most one workbook. Writing clears
the folder first so stale files cannot leak across runs.
"""
import io
import json
from pathlib import Path

import openpyxl

from backend.config import ECC_DATA_DIR, S4_DATA_DIR
from backend.services.ar_processor import clean_date

# Where rows removed via remove_ecc_rows() are kept for download, in the
# same column layout as the ECC staging file. Cleared alongside ECC_DATA
# whenever a fresh ECC fetch is staged (see save_ecc_workbook) -- it's
# scoped to "rows deleted from the currently staged ECC file", not a
# permanent log.
DELETED_DATA_DIR = Path("DELETED_DATA")
DELETED_ROWS_FILENAME = "Deleted_ECC_Rows.xlsx"

# Where warned rows from the last /process run are staged as an Excel
# download. Unlike DELETED_DATA (an audit trail across the session),
# this reflects only the *latest* process run -- a re-process (with or
# without deletions) overwrites it, since the warning set may change.
WARNINGS_DATA_DIR = Path("WARNINGS_DATA")
WARNINGS_ROWS_FILENAME = "Warning_Rows.xlsx"

# S/4 fields written as datetime.date objects by ar_processor.transform_record().
# json.dumps(..., default=str) stringifies them to ISO ("2026-04-08") when the
# sidecar is written; load_s4_rows() must reparse them back into date objects
# or _SapJsonEncoder never converts them to OData's /Date(ms)/ format and SAP
# rejects the push with CX_SY_CONVERSION_NO_DATE_TIME.
S4_DATE_FIELDS = ("BLDAT", "ZFBDT")


def _ensure(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _clear(folder: Path) -> None:
    _ensure(folder)
    for entry in folder.iterdir():
        if entry.is_file():
            entry.unlink()


def _latest(folder: Path) -> Path | None:
    _ensure(folder)
    files = [p for p in folder.iterdir()
             if p.is_file() and p.suffix.lower() in (".xlsx", ".xls")]
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


# --- ECC side --------------------------------------------------------------

def save_ecc_workbook(buffer: io.BytesIO, filename: str) -> Path:
    _clear(ECC_DATA_DIR)
    _clear(DELETED_DATA_DIR)   # a fresh fetch starts a new "session"
    _clear(WARNINGS_DATA_DIR)  # and invalidates the previous run's warnings
    path = _ensure(ECC_DATA_DIR) / filename
    path.write_bytes(buffer.getvalue())
    return path


def latest_ecc_file() -> Path | None:
    return _latest(ECC_DATA_DIR)


def read_ecc_workbook(path: Path) -> list[dict]:
    """Read the staged ECC Excel back into list-of-dicts for the processor."""
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return []
    headers = [str(h) if h is not None else "" for h in rows[0]]
    return [dict(zip(headers, row)) for row in rows[1:]]


def remove_ecc_rows(record_indices: list[int]) -> Path:
    """
    Deletes specific data rows from the currently staged ECC workbook, in
    place, and returns its path. The removed rows' original values are
    kept -- in the same column layout as the ECC file -- in the
    DELETED_DATA audit workbook (see _append_deleted_rows).

    `record_indices` are 1-based positions among the *data* rows.
    """
    path = latest_ecc_file()
    if path is None:
        raise FileNotFoundError("No ECC file staged.")
    if not record_indices:
        return path

    wb = openpyxl.load_workbook(path)
    ws = wb.active
    headers = [cell.value for cell in ws[1]]

    excel_rows = sorted({idx + 1 for idx in record_indices}, reverse=True)
    deleted_values = []
    for excel_row in excel_rows:
        values = [ws.cell(row=excel_row, column=col).value
                  for col in range(1, ws.max_column + 1)]
        deleted_values.append(values)
        ws.delete_rows(excel_row)

    wb.save(path)

    deleted_values.reverse()
    _append_deleted_rows(headers, deleted_values)
    return path


def _append_deleted_rows(headers, rows) -> Path:
    """Appends rows to the running 'deleted from ECC' workbook for the
    current staging session."""
    _ensure(DELETED_DATA_DIR)
    dest = DELETED_DATA_DIR / DELETED_ROWS_FILENAME

    if dest.exists():
        wb = openpyxl.load_workbook(dest)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Deleted_Rows"
        ws.append(headers)

    for row in rows:
        ws.append(row)

    wb.save(dest)
    return dest


def latest_deleted_rows_file() -> Path | None:
    path = DELETED_DATA_DIR / DELETED_ROWS_FILENAME
    return path if path.exists() else None


# --- Warning rows (Excel, per /process run) --------------------------------

def save_warning_rows(headers: list, rows: list[list]) -> Path:
    """
    Writes the warned rows (original ECC values, same column layout as the
    staging file) to WARNINGS_DATA/Warning_Rows.xlsx. Overwrites each run,
    since the warning set is a snapshot of the latest /process.
    """
    _clear(WARNINGS_DATA_DIR)
    _ensure(WARNINGS_DATA_DIR)
    dest = WARNINGS_DATA_DIR / WARNINGS_ROWS_FILENAME

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Warning_Rows"
    if headers:
        ws.append(headers)
    for row in rows:
        ws.append(row)

    wb.save(dest)
    return dest


def latest_warning_rows_file() -> Path | None:
    path = WARNINGS_DATA_DIR / WARNINGS_ROWS_FILENAME
    return path if path.exists() else None


def clear_warning_rows() -> None:
    """Called when the current process run produced zero warnings, so a
    stale file from a previous run can't be downloaded."""
    _clear(WARNINGS_DATA_DIR)


# --- S/4 side --------------------------------------------------------------

def save_s4_workbook(buffer: io.BytesIO, filename: str,
                     s4_rows: list, warnings: list) -> Path:
    """Write the LTMC workbook plus JSON sidecars holding the exact rows
    the OData push would send. Sidecars are retained even though the push
    is disabled -- load_s4_rows()/load_warnings() remain useful for any
    future re-enable or offline inspection."""
    _clear(S4_DATA_DIR)
    folder = _ensure(S4_DATA_DIR)
    path = folder / filename
    path.write_bytes(buffer.getvalue())
    (folder / "_s4_rows.json").write_text(json.dumps(s4_rows, default=str))
    (folder / "_warnings.json").write_text(json.dumps(warnings, default=str))
    return path


def latest_s4_file() -> Path | None:
    return _latest(S4_DATA_DIR)


def load_s4_rows() -> list[dict]:
    """Read the staged S/4 rows back from the JSON sidecar."""
    sidecar = S4_DATA_DIR / "_s4_rows.json"
    if not sidecar.exists():
        return []

    rows = json.loads(sidecar.read_text())
    for row in rows:
        for field in S4_DATE_FIELDS:
            if row.get(field):
                row[field] = clean_date(row[field])
    return rows


def load_warnings() -> list[dict]:
    sidecar = S4_DATA_DIR / "_warnings.json"
    return json.loads(sidecar.read_text()) if sidecar.exists() else []