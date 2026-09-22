"""
ECC -> S/4HANA mappings for the AR open-items migration (demo scope).

Same shape as the previous mappings module: plain dicts, plus small
``get_s4_ar_*`` getters that the processor calls. Every getter returns an
empty string when there is no S/4 value, and the processor turns that into a
warning; nothing is guessed or defaulted here.

Lookup keys are normalised before matching (see ``_normalize_key``), so
"0002" / "2" and "0000100000" / "100000" all resolve to the same entry. This
avoids the usual SAP leading-zero mismatch between OData, Excel and the
internal ALPHA format.
"""

# ---------------------------------------------------------------------------
# Company Code            ECC -> S/4
# ---------------------------------------------------------------------------
COMPANY_CODE_MAPPING = {
    "US01": "1000",
}

# ---------------------------------------------------------------------------
# Payment Terms           ECC -> S/4
# ---------------------------------------------------------------------------
AR_PAYMENT_TERMS_MAPPING = {
    "0002": "Z001",
    "0003": "Z002",
    "0004": "Z003",
    "0006": "Z004",
}

# ---------------------------------------------------------------------------
# Customers               ECC customer -> S/4 business partner
# ---------------------------------------------------------------------------
AR_CUSTOMER_MAPPING = {
    "100000": "10000131",
    "100001": "10000132",
    "100002": "10000133",
    "100003": "10000134",
}

# ---------------------------------------------------------------------------
# Document Type           hardcoded: every S/4 row is loaded as UE,
#                         whatever the ECC document type was.
# ---------------------------------------------------------------------------
AR_DOCUMENT_TYPE = "UE"


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def _normalize_key(value):
    """
    Canonical form used for both the dict keys and the incoming ECC value:
    stripped, upper-cased, and - for purely numeric values - without leading
    zeros. Blank / None / NaN become "".
    """
    if value is None:
        return ""
    if isinstance(value, float):
        if value != value:  # NaN
            return ""
        if value.is_integer():
            value = int(value)

    key = str(value).strip().upper()
    if key.isdigit():
        key = key.lstrip("0") or "0"
    return key


def _build_lookup(mapping):
    return {_normalize_key(ecc): s4 for ecc, s4 in mapping.items()}


_COMPANY_CODE_LOOKUP = _build_lookup(COMPANY_CODE_MAPPING)
_PAYMENT_TERMS_LOOKUP = _build_lookup(AR_PAYMENT_TERMS_MAPPING)
_CUSTOMER_LOOKUP = _build_lookup(AR_CUSTOMER_MAPPING)


def get_s4_ar_company_code(ecc_company_code):
    return _COMPANY_CODE_LOOKUP.get(_normalize_key(ecc_company_code), "")


def get_s4_ar_payment_terms(ecc_payment_terms):
    return _PAYMENT_TERMS_LOOKUP.get(_normalize_key(ecc_payment_terms), "")


def get_s4_ar_customer(ecc_customer):
    return _CUSTOMER_LOOKUP.get(_normalize_key(ecc_customer), "")


def get_s4_ar_document_type(ecc_document_type=None):
    """Always UE - the ECC document type is intentionally ignored."""
    return AR_DOCUMENT_TYPE
