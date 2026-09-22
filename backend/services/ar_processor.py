# fico/ar_processor.py
"""
AR open-items processor: ECC (BSID) -> S/4HANA (LTMC "Customer Open Items").

Input  : list of dicts, exactly what /ar/ecc_data returns. Field names are
         matched case-insensitively (SAP sends "Bukrs"; BSID name is BUKRS).
Output : the S/4 rows, a list of warnings, and the populated LTMC workbook.

The work is split in two so the S/4 push (not built yet) can reuse step 1:

    1. transform_ecc_records()  -> s4_rows, warnings   (pure, no Excel)
    2. build_s4_workbook()      -> BytesIO             (template + rows)

Field logic (no conditional logic beyond what is listed here):

    BUKRS   company-code mapping
    KUNNR   customer mapping
    BLART   hardcoded UE
    BLDAT   date-cleaned
    SGTXT   string-cleaned
    WAERS   direct
    WRBTR   amount, sign from SHKZG  (S -> +, H -> -)
    MWSKZ   derived from the S/4 company code (1000/1001 -> I0, 1200 -> Z0)
    ZTERM   payment-terms mapping
    ZFBDT   date-cleaned
    ZBD1T / ZBD1P / ZBD2T / ZBD2P / ZBD3T   direct (percentages as numbers)
    SKFBT   amount, sign from SHKZG
    KKBER   S/4 company code
    XBLNR   ECC document number (BELNR)  - see XBLNR_SOURCE_FIELD
    XREF1   ECC document number (BELNR)  - see XREF1_SOURCE_FIELD
    ZUONR   direct
    BL      reason code (RSTGR) via REASON_CODE_MAPPING, written to Excel
            column BL (64), which sits outside the standard 63-column template
"""

import datetime
import io
import re
from copy import copy
from dataclasses import dataclass

import openpyxl
from openpyxl.styles import Font

from ..models import mappings


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

TEMPLATE_SHEET = "Customer Open Items"

TECHNICAL_NAME_ROW = 5   # technical field names (BUKRS, XBLNR, ...)
HEADER_ROW = 9           # LTMC repeats the technical names here; data follows

REASON_CODE_COLUMN = 64  # Excel column "BL"
REASON_CODE_HEADER = "BL"

# ECC field copied into S/4 XBLNR / XREF1.
# BSID.XBLNR and BSID.XREF1 are empty in the current extract, and XBLNR is
# mandatory in the template, so both are taken from the ECC document number
# (the old processor's behaviour for non-RV / non-DZ documents).
# To map them literally instead, change these to "XBLNR" / "XREF1".
XBLNR_SOURCE_FIELD = "BELNR"
XREF1_SOURCE_FIELD = "BELNR"

REASON_CODE_MAPPING = {
    "DIC": "048",
    "FRW": "031",
    "PEC": "021",
    "PRC": "024",
    "SSC": "036",
    "UDC": "001",
    "UPC": "011",
}

# Master switch for the two mandatory-field checks below (currently OFF):
#   - validate_ecc_records(): raises if the payload lacks a field the processor reads
#   - transform_record():     warns when a mandatory S/4 field is empty after mapping
# Set to True to turn both back on. Everything else (unmapped values, bad dates,
# bad debit/credit indicator, empty payload) is still checked either way.
CHECK_MANDATORY_FIELDS = False

# S/4 fields that must be non-empty on every row; otherwise a warning is raised.
MANDATORY_FIELDS = [
    "BUKRS",   # Company Code
    "KUNNR",   # Customer
    "BLART",   # Document Type
    "BLDAT",   # Document Date
    "WAERS",   # Currency
    "WRBTR",   # Amount
    "MWSKZ",   # Tax Code
    "XBLNR",   # Reference Document Number
]

# ECC (BSID) fields the processor reads. A key missing from *every* record
# means the OData service is not exposing it -> fail loudly rather than
# silently emitting blank columns.
REQUIRED_ECC_FIELDS = sorted({
    "BUKRS", "KUNNR", "BELNR", "BLDAT", "SGTXT", "WAERS", "SHKZG", "WRBTR",
    "ZTERM", "ZFBDT", "ZBD1T", "ZBD1P", "ZBD2T", "ZBD2P", "ZBD3T", "SKFBT",
    "ZUONR", "RSTGR", XBLNR_SOURCE_FIELD, XREF1_SOURCE_FIELD,
})

# Template columns the processor fills (BL is handled separately).
S4_TEMPLATE_FIELDS = [
    "BUKRS", "XBLNR", "KUNNR", "BLART", "BLDAT", "SGTXT", "WAERS", "WRBTR",
    "MWSKZ", "ZTERM", "ZFBDT", "ZBD1T", "ZBD1P", "ZBD2T", "ZBD2P", "ZBD3T",
    "SKFBT", "KKBER", "ZUONR", "XREF1",
]


class EccDataError(ValueError):
    """The ECC payload is empty or is missing fields the processor needs."""


class TemplateError(RuntimeError):
    """The S/4 template does not have the expected layout."""


@dataclass
class ARProcessResult:
    output: io.BytesIO   # populated LTMC workbook
    s4_rows: list        # transformed rows (dicts keyed by S/4 field)
    warnings: list       # empty list => safe to push to S/4


# ---------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------

def _is_blank(value):
    if value is None:
        return True
    if isinstance(value, float) and value != value:  # NaN
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def clean_string(value):
    if _is_blank(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def clean_float(value, default=None):
    if _is_blank(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


_ODATA_DATE = re.compile(r"^/Date\((-?\d+)(?:[+-]\d+)?\)/$")
_INITIAL_DATES = {"00/00/0000", "00.00.0000", "0000-00-00", "00000000", "NAT"}
_DATE_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%d.%m.%Y",
    "%Y%m%d",
)


def clean_date(value):
    """
    Returns a datetime.date, or None for blank / SAP-initial dates.
    Raises ValueError if the value is present but cannot be parsed.

    Handles OData V2 "/Date(1775606400000)/", ISO strings, YYYYMMDD,
    dd.mm.yyyy, and real date/datetime objects.
    """
    if _is_blank(value):
        return None

    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value

    text = str(value).strip()
    if text.upper() in _INITIAL_DATES:
        return None

    match = _ODATA_DATE.match(text)
    if match:
        millis = int(match.group(1))
        moment = datetime.datetime(1970, 1, 1) + datetime.timedelta(
            milliseconds=millis
        )
        return moment.date()

    for date_format in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(text, date_format).date()
        except ValueError:
            continue

    raise ValueError(f"unrecognised date '{text}'")


def normalize_amount(amount, debit_credit_indicator):
    """
    S -> positive, H -> negative. Positive values are written as 500, not '+500'.
    An unknown indicator leaves the amount positive (the caller raises a warning).
    """
    amount = clean_float(amount)
    if amount is None:
        return None

    amount = abs(amount)
    indicator = clean_string(debit_credit_indicator).upper()

    if indicator == "H":
        return -amount
    return amount


def get_reason_code(reason_code):
    return REASON_CODE_MAPPING.get(clean_string(reason_code).upper(), "")


def get_tax_code(s4_company_code):
    """ECC tax code is NOT used; it is derived from the S/4 company code."""
    if s4_company_code in ("1000", "1001"):
        return "I0"
    if s4_company_code == "1200":
        return "Z0"
    return ""


# ---------------------------------------------------------------------
# Step 1 - transformation (ECC records -> S/4 rows + warnings)
# ---------------------------------------------------------------------

def transform_record(record, index):
    """
    Transforms one ECC record. `index` is the 1-based position of the record
    in the ECC payload, used to point warnings at the right row.
    """
    warnings = []
    document = clean_string(record.get("BELNR"))

    def warn(field, code, message):
        warnings.append({
            "record": index,
            "document": document,
            "field": field,
            "code": code,
            "message": message,
        })

    # --- mapped fields -------------------------------------------------
    ecc_company = clean_string(record.get("BUKRS"))
    s4_company = mappings.get_s4_ar_company_code(ecc_company)
    if ecc_company and not s4_company:
        warn("BUKRS", "NO_MAPPING",
             f"No S/4 company code mapping for ECC company code '{ecc_company}'.")

    ecc_customer = clean_string(record.get("KUNNR"))
    s4_customer = mappings.get_s4_ar_customer(ecc_customer)
    if ecc_customer and not s4_customer:
        warn("KUNNR", "NO_MAPPING",
             f"No S/4 business partner mapping for ECC customer '{ecc_customer}'.")

    ecc_terms = clean_string(record.get("ZTERM"))
    s4_terms = mappings.get_s4_ar_payment_terms(ecc_terms)
    if ecc_terms and not s4_terms:
        warn("ZTERM", "NO_MAPPING",
             f"No S/4 payment terms mapping for ECC terms '{ecc_terms}'.")

    ecc_reason = clean_string(record.get("RSTGR"))
    reason_code = get_reason_code(ecc_reason)
    if ecc_reason and not reason_code:
        warn("BL", "NO_MAPPING",
             f"No reason code mapping for ECC reason code '{ecc_reason}'.")

    # --- dates ---------------------------------------------------------
    dates = {}
    for field in ("BLDAT", "ZFBDT"):
        try:
            dates[field] = clean_date(record.get(field))
        except ValueError as error:
            dates[field] = None
            warn(field, "INVALID_DATE", f"{field}: {error}.")

    # --- amounts (sign from debit/credit indicator) --------------------
    indicator = clean_string(record.get("SHKZG")).upper()
    if indicator not in ("S", "H"):
        warn("SHKZG", "INVALID_INDICATOR",
             f"Debit/Credit indicator is '{indicator}', expected 'S' or 'H'; "
             "amounts were left positive.")

    row = {
        "BUKRS": s4_company,
        "XBLNR": clean_string(record.get(XBLNR_SOURCE_FIELD)),
        "KUNNR": s4_customer,
        "BLART": mappings.get_s4_ar_document_type(record.get("BLART")),
        "BLDAT": dates["BLDAT"],
        "SGTXT": clean_string(record.get("SGTXT")),
        "WAERS": clean_string(record.get("WAERS")),
        "WRBTR": normalize_amount(record.get("WRBTR"), indicator),
        "MWSKZ": get_tax_code(s4_company),
        "ZTERM": s4_terms,
        "ZFBDT": dates["ZFBDT"],
        "ZBD1T": clean_string(record.get("ZBD1T")),
        "ZBD1P": clean_float(record.get("ZBD1P")),
        "ZBD2T": clean_string(record.get("ZBD2T")),
        "ZBD2P": clean_float(record.get("ZBD2P")),
        "ZBD3T": clean_string(record.get("ZBD3T")),
        "SKFBT": normalize_amount(record.get("SKFBT"), indicator),
        "KKBER": s4_company,
        "ZUONR": clean_string(record.get("ZUONR")),
        "XREF1": clean_string(record.get(XREF1_SOURCE_FIELD)),
        "BL": reason_code,
    }

    # --- mandatory-field check ----------------------------------------
    # Skip fields already flagged above (e.g. an unmapped customer would
    # otherwise be reported twice).
    if CHECK_MANDATORY_FIELDS:
        already_flagged = {w["field"] for w in warnings}
        for field in MANDATORY_FIELDS:
            if field in already_flagged:
                continue
            if _is_blank(row[field]):
                warn(field, "MISSING_MANDATORY",
                     f"Mandatory field {field} is empty after transformation.")

    return row, warnings


def normalize_records(records):
    """
    Upper-cases every field name. The SAP OData service returns Title-case
    properties ("Bukrs", "Kunnr", "Belnr"), while the processor and mappings
    use the BSID technical names ("BUKRS", ...). Also does the structural
    checks that always apply: a non-empty list of objects.
    """
    if not isinstance(records, list) or not records:
        raise EccDataError("There are no ECC records to process.")

    normalized = []
    for record in records:
        if not isinstance(record, dict):
            raise EccDataError("Each ECC record must be an object of field/value pairs.")
        normalized.append({str(key).upper(): value for key, value in record.items()})
    return normalized


def validate_ecc_records(records):
    """`records` must already be normalized. Only active when CHECK_MANDATORY_FIELDS."""
    if not CHECK_MANDATORY_FIELDS:
        return

    present = set()
    for record in records:
        present.update(record.keys())

    missing = [field for field in REQUIRED_ECC_FIELDS if field not in present]
    if missing:
        raise EccDataError(
            "The ECC data is missing required field(s): " + ", ".join(missing) + "."
        )


def transform_ecc_records(records):
    """ECC records -> (s4_rows, warnings). Pure; touches no files."""
    records = normalize_records(records)
    validate_ecc_records(records)

    s4_rows, warnings = [], []
    for index, record in enumerate(records, start=1):
        row, row_warnings = transform_record(record, index)
        s4_rows.append(row)
        warnings.extend(row_warnings)
    return s4_rows, warnings


# ---------------------------------------------------------------------
# Step 2 - Excel output (populate the LTMC template)
# ---------------------------------------------------------------------

def _detect_data_start_row(ws, technical_columns):
    """
    In this template row 9 repeats the technical names as a header row, so
    data starts at row 10. Older layouts start data at row 9.
    """
    repeats = sum(
        1 for name, col in technical_columns.items()
        if clean_string(ws.cell(row=HEADER_ROW, column=col).value) == name
    )
    return HEADER_ROW + 1 if repeats >= len(technical_columns) / 2 else HEADER_ROW


def build_s4_workbook(s4_rows, warnings, template_path):
    wb = openpyxl.load_workbook(template_path)
    ws = wb[TEMPLATE_SHEET] if TEMPLATE_SHEET in wb.sheetnames else wb[wb.sheetnames[0]]

    technical_columns = {}
    for col in range(1, ws.max_column + 1):
        name = clean_string(ws.cell(row=TECHNICAL_NAME_ROW, column=col).value)
        if name:
            technical_columns[name] = col

    missing = [f for f in S4_TEMPLATE_FIELDS if f not in technical_columns]
    if missing:
        raise TemplateError(
            f"Template '{ws.title}' has no column(s) for: {', '.join(missing)}. "
            f"Technical names are expected in row {TECHNICAL_NAME_ROW}."
        )

    data_start_row = _detect_data_start_row(ws, technical_columns)
    last_col = max(REASON_CODE_COLUMN, ws.max_column)

    # Snapshot the look of an (empty) data row and the per-column number
    # formats from the header row, then wipe whatever data is in the template.
    row_style = {
        col: copy(ws.cell(row=data_start_row, column=col)._style)
        for col in range(1, last_col + 1)
    }
    number_format = {
        col: ws.cell(row=HEADER_ROW, column=col).number_format
        for col in range(1, last_col + 1)
    }
    if ws.max_row >= data_start_row:
        ws.delete_rows(data_start_row, ws.max_row - data_start_row + 1)

    # Label the extra reason-code column so it is not header-less.
    last_template_col = max(technical_columns.values())
    for header_row in (TECHNICAL_NAME_ROW, HEADER_ROW):
        cell = ws.cell(row=header_row, column=REASON_CODE_COLUMN)
        cell._style = copy(ws.cell(row=header_row, column=last_template_col)._style)
        cell.value = REASON_CODE_HEADER
    row_style[REASON_CODE_COLUMN] = row_style[last_template_col]
    number_format[REASON_CODE_COLUMN] = "@"

    column_for = dict(technical_columns)
    column_for["BL"] = REASON_CODE_COLUMN

    for offset, s4_row in enumerate(s4_rows):
        excel_row = data_start_row + offset
        for col in range(1, last_col + 1):
            cell = ws.cell(row=excel_row, column=col)
            cell._style = copy(row_style[col])
            cell.number_format = number_format[col]
        for field, value in s4_row.items():
            ws.cell(row=excel_row, column=column_for[field]).value = (
                None if value == "" else value
            )

    if warnings:
        _add_warnings_sheet(wb, warnings, data_start_row)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def _add_warnings_sheet(wb, warnings, data_start_row):
    sheet = wb.create_sheet("Warnings")
    headers = ["ECC record #", "Output row", "ECC document", "Field", "Code", "Message"]
    sheet.append(headers)
    for w in warnings:
        sheet.append([
            w["record"],
            data_start_row + w["record"] - 1,
            w["document"],
            w["field"],
            w["code"],
            w["message"],
        ])
    for col, width in zip("ABCDEF", (14, 12, 16, 10, 20, 90)):
        sheet.column_dimensions[col].width = width
    for cell in sheet[1]:
        cell.font = Font(bold=True)


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

def process_ar_records(records, template_path):
    """
    Transforms ECC AR records to S/4 and populates the LTMC template.

    Raises EccDataError (bad input) or TemplateError (bad template).
    `result.warnings` empty => the rows are clean and can be pushed to S/4.
    """
    s4_rows, warnings = transform_ecc_records(records)
    output = build_s4_workbook(s4_rows, warnings, template_path)
    return ARProcessResult(output=output, s4_rows=s4_rows, warnings=warnings)