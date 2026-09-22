"""
Field-name translation for AR validation.

ECC extract (ECC_DATA/*.xlsx) writes human-readable column headers
("Company Code", "Debit/Credit ind", "Payment terms", ...). The
validation checks use canonical names. Only two differ; both are
normalized here.

S/4 template (S4_DATA/*.xlsx) already carries technical names in
row 5 (BUKRS, XBLNR, KUNNR, ...), so no aliasing is needed on that
side. S4_FIELDS below is the single place those names live, so a
template change touches one file.

Imports: none. Pure data.
"""

# ---------------------------------------------------------------------------
# ECC extract -> canonical names used by checks
# Keys are lower-cased for case-insensitive lookup (see _rename_ecc_columns).
# ---------------------------------------------------------------------------

ECC_COLUMN_ALIASES = {
    "debit/credit ind": "Debit/Credit Ind.",
    "payment terms":    "Terms of Payment",
    # Add more if the extract's header changes.
}


# ---------------------------------------------------------------------------
# S/4 template technical names (row 5)
# ---------------------------------------------------------------------------

S4_FIELDS = {
    "COMPANY_CODE":         "BUKRS",
    "DOCUMENT_NUMBER":      "XBLNR",
    "LINE_ITEM":            "DOCLN",
    "CUSTOMER":             "KUNNR",
    "DOCUMENT_TYPE":        "BLART",
    "DOCUMENT_DATE":        "BLDAT",
    "CURRENCY":             "WAERS",
    "AMOUNT":               "WRBTR",
    "TAX_CODE":             "MWSKZ",
    "PAYMENT_TERMS":        "ZTERM",
    "BASELINE_DATE":        "ZFBDT",
    "DISCOUNT_DAYS_1":      "ZBD1T",
    "DISCOUNT_PCT_1":       "ZBD1P",
    "DISCOUNT_DAYS_2":      "ZBD2T",
    "DISCOUNT_PCT_2":       "ZBD2P",
    "NET_DUE_DAYS":         "ZBD3T",
    "DISCOUNT_BASE_AMT":    "SKFBT",
    "CREDIT_CONTROL_AREA":  "KKBER",
    "ASSIGNMENT":           "ZUONR",
    "REFERENCE_KEY_1":      "XREF1",
    "REASON_CODE":          "BL",
}