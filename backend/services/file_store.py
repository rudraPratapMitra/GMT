"""Staging store for ECC_DATA / S4_DATA.

Single-run mode: each folder holds at most one workbook. Writing clears
the folder first so stale files cannot leak across runs.
"""
import io
import json
from pathlib import Path

import openpyxl

from backend.config import ECC_DATA_DIR, S4_DATA_DIR


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


# --- S/4 side --------------------------------------------------------------

def save_s4_workbook(buffer: io.BytesIO, filename: str,
                     s4_rows: list, warnings: list) -> Path:
    """Write the LTMC workbook plus JSON sidecars holding the exact rows
    the OData push will send. Sidecars avoid re-parsing the template layout
    (row 5 = technical names, row 9 = headers, row 10 = data) at load time."""
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
    sidecar = S4_DATA_DIR / "_s4_rows.json"
    return json.loads(sidecar.read_text()) if sidecar.exists() else []


def load_warnings() -> list[dict]:
    sidecar = S4_DATA_DIR / "_warnings.json"
    return json.loads(sidecar.read_text()) if sidecar.exists() else []