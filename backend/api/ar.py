# # from fastapi import APIRouter, HTTPException
# # from fastapi.responses import JSONResponse
# # import os
# # import requests
# # from dotenv import load_dotenv

# import json
# import os
# from datetime import datetime
# from typing import Any, Dict, List

# import datetime as _dt
# import requests
# from dotenv import load_dotenv
# from fastapi import APIRouter, HTTPException
# from fastapi.responses import JSONResponse, StreamingResponse
# from pydantic import BaseModel
# from requests import Request
# from requests.auth import HTTPBasicAuth

# from config import AR_TEMPLATE_PATH
# from api.ar_processor import EccDataError, TemplateError, process_ar_records


# # ---------------------------------------------------------------------------
# # OData V2 date handling
# # ---------------------------------------------------------------------------

# def _date_to_odata_v2(value):
#     """
#     SAP Gateway's OData V2 wire format for Edm.DateTime is /Date(ms)/, where
#     ms is milliseconds since 1970-01-01 00:00:00 UTC. Dates are treated as
#     midnight UTC.
#     """
#     epoch = _dt.datetime(1970, 1, 1, tzinfo=_dt.timezone.utc)

#     if isinstance(value, _dt.datetime):
#         moment = value if value.tzinfo else value.replace(tzinfo=_dt.timezone.utc)
#     elif isinstance(value, _dt.date):
#         moment = _dt.datetime(value.year, value.month, value.day,
#                               tzinfo=_dt.timezone.utc)
#     else:
#         raise TypeError(f"not a date: {value!r}")

#     millis = int((moment - epoch).total_seconds() * 1000)
#     return f"/Date({millis})/"


# class _SapJsonEncoder(json.JSONEncoder):
#     """Serializes dates the way SAP Gateway's OData V2 runtime expects."""
#     def default(self, obj):
#         if isinstance(obj, (_dt.date, _dt.datetime)):
#             return _date_to_odata_v2(obj)
#         return super().default(obj)


# # ---------------------------------------------------------------------------
# # Configuration
# # ---------------------------------------------------------------------------

# load_dotenv()
# router = APIRouter()

# # ECC source (BSID) — used only by GET /ar/ecc_data
# ODATA_URL = (
#     "http://ec2-54-158-63-191.compute-1.amazonaws.com:8080/"
#     "sap/opu/odata/SAP/Z_BSID_ODATA_AR1_SRV/ZBSIDItemSet"
# )

# SAP_USERNAME = os.getenv("SAP_USERNAME")
# SAP_PASSWORD = os.getenv("SAP_PASSWORD")

# # S/4 target — the custom OData service that writes into ZBSID_DEMO_1
# S4_SERVICE_URL = "http://ec2-52-5-159-197.compute-1.amazonaws.com:8080/sap/opu/odata/SAP/ZAR_OPEN_ITEMS_SRV"
# S4_ENTITY_SET  = "ZBSID_S4itemsSet"


# # Maps the UPPERCASE field names produced by ar_processor.py to the
# # camelCase property names SEGW generates for the ZBSID_S4items entity type.
# BSID_TO_ODATA = {
#     # --- Key fields -------------------------------------------------
#     "MANDT":   "Mandt",
#     "BUKRS":   "Bukrs",
#     "KUNNR":   "Kunnr",
#     "UMSKS":   "Umsks",
#     "UMSKZ":   "Umskz",
#     "AUGDT":   "Augdt",
#     "AUGBL":   "Augbl",
#     "ZUONR":   "Zuonr",
#     "GJAHR":   "Gjahr",
#     "BELNR":   "Belnr",
#     "BUZEI":   "Buzei",
#     "BUDAT":   "Budat",
#     "BLDAT":   "Bldat",
#     "CPUDT":   "Cpudt",
#     "WAERS":   "Waers",
#     "XBLNR":   "Xblnr",
#     "BLART":   "Blart",
#     "MONAT":   "Monat",
#     "BSCHL":   "Bschl",
#     "ZUMSK":   "Zumsk",
#     "SHKZG":   "Shkzg",
#     "GSBER":   "Gsber",
#     "MWSKZ":   "Mwskz",
#     "DMBTR":   "Dmbtr",
#     "WRBTR":   "Wrbtr",
#     "MWSTS":   "Mwsts",
#     "WMWST":   "Wmwst",
#     "BDIFF":   "Bdiff",
#     "BDIF2":   "Bdif2",
#     "SGTXT":   "Sgtxt",
#     "PROJN":   "Projn",
#     "AUFNR":   "Aufnr",
#     "ANLN1":   "Anln1",
#     "ANLN2":   "Anln2",
#     "SAKNR":   "Saknr",
#     "HKONT":   "Hkont",
#     "FKONT":   "Fkont",
#     "FILKD":   "Filkd",
#     "ZFBDT":   "Zfbdt",
#     "ZTERM":   "Zterm",
#     "ZBD1T":   "Zbd1t",
#     "ZBD2T":   "Zbd2t",
#     "ZBD3T":   "Zbd3t",
#     "ZBD1P":   "Zbd1p",
#     "ZBD2P":   "Zbd2p",
#     "SKFBT":   "Skfbt",
#     "SKNTO":   "Sknto",
#     "WSKTO":   "Wskto",
#     "ZLSCH":   "Zlsch",
#     "ZLSPR":   "Zlspr",
#     "ZBFIX":   "Zbfix",
#     "HBKID":   "Hbkid",
#     "BVTYP":   "Bvtyp",
#     "REBZG":   "Rebzg",
#     "REBZJ":   "Rebzj",
#     "REBZZ":   "Rebzz",
#     "SAMNR":   "Samnr",
#     "ANFBN":   "Anfbn",
#     "ANFBJ":   "Anfbj",
#     "ANFBU":   "Anfbu",
#     "ANFAE":   "Anfae",
#     "MANSP":   "Mansp",
#     "MSCHL":   "Mschl",
#     "MADAT":   "Madat",
#     "MANST":   "Manst",
#     "MABER":   "Maber",
#     "XNETB":   "Xnetb",
#     "XANET":   "Xanet",
#     "XCPDD":   "Xcpdd",
#     "XINVE":   "Xinve",
#     "XZAHL":   "Xzahl",
#     "MWSK1":   "Mwsk1",
#     "DMBT1":   "Dmbt1",
#     "WRBT1":   "Wrbt1",
#     "MWSK2":   "Mwsk2",
#     "DMBT2":   "Dmbt2",
#     "WRBT2":   "Wrbt2",
#     "MWSK3":   "Mwsk3",
#     "DMBT3":   "Dmbt3",
#     "WRBT3":   "Wrbt3",
#     "BSTAT":   "Bstat",
#     "VBUND":   "Vbund",
#     "VBELN":   "Vbeln",
#     "REBZT":   "Rebzt",
#     "INFAE":   "Infae",
#     "STCEG":   "Stceg",
#     "EGBLD":   "Egbld",
#     "EGLLD":   "Egld",
#     "RSTGR":   "Rstgr",
#     "XNOZA":   "Xnoza",
#     "VERTT":   "Vertt",
#     "VERTN":   "Vertn",
#     "VBEWA":   "Vbewa",
#     "WVERW":   "Wverw",
#     "PROJK":   "Projk",
#     "FIPOS":   "Fipos",
#     "NPLNR":   "Nplnr",
#     "AUFPL":   "Aufpl",
#     "APLZL":   "Aplzl",
#     "XEGDR":   "Xegdr",
#     "DMBE2":   "Dmbe2",
#     "DMBE3":   "Dmbe3",
#     "DMB21":   "Dmb21",
#     "DMB22":   "Dmb22",
#     "DMB23":   "Dmb23",
#     "DMB31":   "Dmb31",
#     "DMB32":   "Dmb32",
#     "DMB33":   "Dmb33",
#     "BDIF3":   "Bdif3",
#     "XRAGL":   "Xragl",
#     "UZAWE":   "Uzawe",
#     "XSTOV":   "Xstov",
#     "MWST2":   "Mwst2",
#     "MWST3":   "Mwst3",
#     "SKNT2":   "Sknt2",
#     "SKNT3":   "Sknt3",
#     "XREF1":   "Xref1",
#     "XREF2":   "Xref2",
#     "XARCH":   "Xarch",
#     "PSWSL":   "Pswsl",
#     "PSWBT":   "Pswbt",
#     "LZBKZ":   "Lzbkz",
#     "LANDL":   "Landl",
#     "IMKEY":   "Imkey",
#     "VBEL2":   "Vbel2",
#     "VPOS2":   "Vpos2",
#     "POSN2":   "Posn2",
#     "ETEN2":   "Eten2",
#     "FISTL":   "Fistl",
#     "GEBER":   "Geber",
#     "DABRZ":   "Dabrz",
#     "XNEGP":   "Xnegp",
#     "KOSTL":   "Kostl",
#     "RFZEI":   "Rfzei",
#     "KKBER":   "Kkber",
#     "EMPFB":   "Empfb",
#     "PRCTR":   "Prctr",
#     "XREF3":   "Xref3",
#     "QSSKZ":   "Qsskz",
#     "ZINKZ":   "Zinkz",
#     "DTWS1":   "Dtws1",
#     "DTWS2":   "Dtws2",
#     "DTWS3":   "Dtws3",
#     "DTWS4":   "Dtws4",
#     "XPYPR":   "Xpypr",
#     "KIDNO":   "Kidno",
#     "ABSBT":   "Absbt",
#     "CCBTC":   "Ccbtc",
#     "PYCUR":   "Pycur",
#     "PYAMT":   "Pyamt",
#     "BUPLA":   "Bupla",
#     "SECCO":   "Secco",
#     "CESSION_KZ": "CessionKz",
#     "PPDIFF":  "Ppdiff",
#     "PPDIF2":  "Ppdif2",
#     "PPDIF3":  "Ppdif3",
#     "KBLNR":   "Kblnr",
#     "KBLPOS":  "Kblpos",
#     "GRANT_NBR": "GrantNbr",
#     "GMVKZ":   "Gmvkz",
#     "SRTYPE":  "Srtype",
#     "LOTKZ":   "Lotkz",
#     "FKBER":   "Fkber",
#     "INTRENO": "Intreno",
#     "PPRCT":   "Pprct",
#     "BUZID":   "Buzid",
#     "AUGGJ":   "Auggj",
#     "BUDGET_PD": "BudgetPd",
#     "PAYS_PROV": "PaysProv",
#     "PAYS_TRAN": "PaysTran",
#     "MNDID":   "Mndid",
#     "KONTT":   "Kontt",
#     "KONTL":   "Kontl",
#     "UEBGDAT": "Uebgdat",
#     "VNAME":   "Vname",
#     "EGRUP":   "Egrupp",
#     "BTYPE":   "Btype",
#     "PROPMANO": "Propmano",
#     # --- Additional fields from the SEGW model ---------------------
#     "TAX_COUNTRY": "TaxCountry",
#     "TXDAT_FROM":  "TxdatFrom",
#     "FCSL":        "Fcsl",
#     "RFCURR":      "Rfccur",
# }


# def _to_odata_payload(s4_row):
#     """Translate UPPERCASE processor keys into the camelCase OData property
#     names SEGW generated. Any key not in BSID_TO_ODATA is skipped."""
#     payload = {}
#     for key, value in s4_row.items():
#         odata_name = BSID_TO_ODATA.get(key)
#         if odata_name is None:
#             continue          # e.g. 'BL' — not an entity property
#         if value == "" or value is None:
#             continue          # omit blanks; gateway treats missing as initial

#         # SAP Gateway V2 wants Edm.Decimal values as JSON strings formatted
#         # to the scale declared in SEGW. Your model declares scale=3 for
#         # Dmbtr and Wrbtr, so we emit exactly 3 decimal places.
#         if isinstance(value, float):
#             value = f"{value:.3f}"

#         payload[odata_name] = value
#     return payload


# # ---------------------------------------------------------------------------
# # Endpoints
# # ---------------------------------------------------------------------------

# @router.get("/ecc_data")
# def get_ar_data():
#     try:
#         response = requests.get(
#             ODATA_URL,
#             headers={"Accept": "application/json"},
#             auth=(SAP_USERNAME, SAP_PASSWORD),
#             params={"$format": "json"},
#             verify=False,
#             timeout=120,
#         )
#     except requests.exceptions.Timeout:
#         raise HTTPException(status_code=504, detail="SAP request timed out")
#     except requests.exceptions.RequestException as e:
#         raise HTTPException(status_code=502, detail=f"SAP connection failed: {e}")

#     if not response.ok:
#         raise HTTPException(
#             status_code=response.status_code,
#             detail=f"SAP returned {response.status_code}: {response.text[:200]}",
#         )

#     try:
#         json_data = response.json()
#         results = json_data["d"]["results"]
#     except (ValueError, KeyError) as e:
#         raise HTTPException(
#             status_code=502,
#             detail=f"Unexpected SAP response shape: {e}",
#         )

#     return results


# XLSX_MEDIA_TYPE = (
#     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# )


# class ProcessRequest(BaseModel):
#     # The ECC rows the frontend already holds from GET /ar/ecc_data.
#     # SAP is NOT called again here.
#     records: List[Dict[str, Any]]


# @router.post("/process")
# def process_ar(payload: ProcessRequest):
#     """
#     Transforms the posted ECC AR rows to S/4, pushes them to the custom
#     OData service, and returns the populated LTMC workbook as a download.
#     """
#     try:
#         result = process_ar_records(payload.records, AR_TEMPLATE_PATH)
#     except EccDataError as e:
#         raise HTTPException(status_code=422, detail=str(e))
#     except TemplateError as e:
#         raise HTTPException(status_code=500, detail=f"S/4 template problem: {e}")

#     # Push to S/4 and capture the result
#     push_result = {"status": "skipped", "message": "No rows to push."}
#     if result.s4_rows:
#         if not result.warnings:
#             # Only push if there are no warnings (i.e., data is clean)
#             push_result = push_to_s4(result.s4_rows)
#         else:
#             push_result["message"] = "Skipped push due to transformation warnings."

#     # Log the push summary to the console
#     print()
#     print("=" * 70)
#     print("S/4 PUSH SUMMARY")
#     print("=" * 70)
#     print(json.dumps(push_result, indent=2, default=str))
#     print("=" * 70)
#     print()

#     # The filename is generated with a timestamp
#     filename = f"AR_S4_Load_{datetime.now():%Y%m%d_%H%M%S}.xlsx"

#     # Add push result to the response headers for visibility
#     response_headers = {
#         "Content-Disposition": f'attachment; filename="{filename}"',
#         "X-Record-Count": str(len(result.s4_rows)),
#         "X-Warning-Count": str(len(result.warnings)),
#         "X-S4-Push-Status": push_result.get("status", "unknown"),
#     }
#     if push_result.get("success_count") is not None:
#         response_headers["X-S4-Push-Success"] = str(push_result["success_count"])
#     if push_result.get("error_count") is not None:
#         response_headers["X-S4-Push-Errors"] = str(push_result["error_count"])

#     return StreamingResponse(
#         result.output,
#         media_type=XLSX_MEDIA_TYPE,
#         headers=response_headers,
#     )


# def push_to_s4(s4_rows):
#     auth = HTTPBasicAuth(SAP_USERNAME, SAP_PASSWORD)
#     session = requests.Session()
#     session.auth = auth
#     session.verify = False

#     # 1. Fetch CSRF token from the SERVICE ROOT
#     try:
#         r = session.get(
#             S4_SERVICE_URL,                           # ← root, not entity set
#             headers={"x-csrf-token": "Fetch", "Accept": "application/json"},
#             timeout=30,
#         )
#         r.raise_for_status()
#     except requests.exceptions.RequestException as e:
#         return {"status": "error", "message": f"CSRF fetch failed: {e}"}

#     csrf_token = r.headers.get("x-csrf-token")
#     if not csrf_token:
#         return {"status": "error",
#                 "message": "No CSRF token returned. Check auth and service registration."}

#     headers = {
#         "x-csrf-token": csrf_token,
#         "Content-Type": "application/json",
#         "Accept": "application/json",
#     }

#     # 2. POST each row to the entity set
#     success, errors = 0, []

#     for index, row in enumerate(s4_rows):
#         payload = _to_odata_payload(row)
#         body = json.dumps(payload, cls=_SapJsonEncoder)

#         # ---- LOGGING: print the first payload in full -----------------
#         if index == 0:
#             print()
#             print("=" * 70)
#             print("FIRST PAYLOAD SENT TO S/4")
#             print("=" * 70)
#             print(f"POST URL: {S4_SERVICE_URL}/{S4_ENTITY_SET}")
#             print(f"CSRF token (first 20 chars): {csrf_token[:20]}...")
#             print("-" * 70)
#             print(json.dumps(payload, cls=_SapJsonEncoder, indent=2))
#             print("-" * 70)
#             print(f"Raw body length: {len(body)} bytes")
#             print("=" * 70)
#             print()

#         try:
#             resp = session.post(
#                 f"{S4_SERVICE_URL}/{S4_ENTITY_SET}",
#                 headers=headers,
#                 data=body,
#                 timeout=30,
#             )
#             if resp.status_code == 201:
#                 success += 1
#             else:
#                 errors.append({
#                     "status": resp.status_code,
#                     "body": resp.text[:500],
#                     "row_belnr": row.get("XBLNR"),
#                 })
#                 # ---- LOGGING: show the first failure response ---------
#                 if len(errors) == 1:
#                     print("=" * 70)
#                     print("FIRST FAILURE RESPONSE")
#                     print("=" * 70)
#                     print(f"Status: {resp.status_code}")
#                     print(f"Body: {resp.text[:1000]}")
#                     print("=" * 70)
#         except requests.exceptions.RequestException as e:
#             errors.append({"error": str(e), "row_belnr": row.get("XBLNR")})

#     return {
#         "status": "success" if not errors else "partial_success",
#         "success_count": success,
#         "error_count": len(errors),
#         "errors": errors,
#     }

# from fastapi import APIRouter, HTTPException
# from fastapi.responses import JSONResponse
# import os
# import requests
# from dotenv import load_dotenv

import json
import os
from datetime import datetime
from typing import Any, Dict, List

import datetime as _dt
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from requests import Request
from requests.auth import HTTPBasicAuth

from config import AR_TEMPLATE_PATH
from api.ar_processor import EccDataError, TemplateError, process_ar_records


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
BSID_TO_ODATA = {
    # --- Key fields -------------------------------------------------
    "MANDT":   "Mandt",
    "BUKRS":   "Bukrs",
    "KUNNR":   "Kunnr",
    "UMSKS":   "Umsks",
    "UMSKZ":   "Umskz",
    "AUGDT":   "Augdt",
    "AUGBL":   "Augbl",
    "ZUONR":   "Zuonr",
    "GJAHR":   "Gjahr",
    "BELNR":   "Belnr",
    "BUZEI":   "Buzei",
    "BUDAT":   "Budat",
    "BLDAT":   "Bldat",
    "CPUDT":   "Cpudt",
    "WAERS":   "Waers",
    "XBLNR":   "Xblnr",
    "BLART":   "Blart",
    "MONAT":   "Monat",
    "BSCHL":   "Bschl",
    "ZUMSK":   "Zumsk",
    "SHKZG":   "Shkzg",
    "GSBER":   "Gsber",
    "MWSKZ":   "Mwskz",
    "DMBTR":   "Dmbtr",
    "WRBTR":   "Wrbtr",
    "MWSTS":   "Mwsts",
    "WMWST":   "Wmwst",
    "BDIFF":   "Bdiff",
    "BDIF2":   "Bdif2",
    "SGTXT":   "Sgtxt",
    "PROJN":   "Projn",
    "AUFNR":   "Aufnr",
    "ANLN1":   "Anln1",
    "ANLN2":   "Anln2",
    "SAKNR":   "Saknr",
    "HKONT":   "Hkont",
    "FKONT":   "Fkont",
    "FILKD":   "Filkd",
    "ZFBDT":   "Zfbdt",
    "ZTERM":   "Zterm",
    "ZBD1T":   "Zbd1t",
    "ZBD2T":   "Zbd2t",
    "ZBD3T":   "Zbd3t",
    "ZBD1P":   "Zbd1p",
    "ZBD2P":   "Zbd2p",
    "SKFBT":   "Skfbt",
    "SKNTO":   "Sknto",
    "WSKTO":   "Wskto",
    "ZLSCH":   "Zlsch",
    "ZLSPR":   "Zlspr",
    "ZBFIX":   "Zbfix",
    "HBKID":   "Hbkid",
    "BVTYP":   "Bvtyp",
    "REBZG":   "Rebzg",
    "REBZJ":   "Rebzj",
    "REBZZ":   "Rebzz",
    "SAMNR":   "Samnr",
    "ANFBN":   "Anfbn",
    "ANFBJ":   "Anfbj",
    "ANFBU":   "Anfbu",
    "ANFAE":   "Anfae",
    "MANSP":   "Mansp",
    "MSCHL":   "Mschl",
    "MADAT":   "Madat",
    "MANST":   "Manst",
    "MABER":   "Maber",
    "XNETB":   "Xnetb",
    "XANET":   "Xanet",
    "XCPDD":   "Xcpdd",
    "XINVE":   "Xinve",
    "XZAHL":   "Xzahl",
    "MWSK1":   "Mwsk1",
    "DMBT1":   "Dmbt1",
    "WRBT1":   "Wrbt1",
    "MWSK2":   "Mwsk2",
    "DMBT2":   "Dmbt2",
    "WRBT2":   "Wrbt2",
    "MWSK3":   "Mwsk3",
    "DMBT3":   "Dmbt3",
    "WRBT3":   "Wrbt3",
    "BSTAT":   "Bstat",
    "VBUND":   "Vbund",
    "VBELN":   "Vbeln",
    "REBZT":   "Rebzt",
    "INFAE":   "Infae",
    "STCEG":   "Stceg",
    "EGBLD":   "Egbld",
    "EGLLD":   "Egld",
    "RSTGR":   "Rstgr",
    "XNOZA":   "Xnoza",
    "VERTT":   "Vertt",
    "VERTN":   "Vertn",
    "VBEWA":   "Vbewa",
    "WVERW":   "Wverw",
    "PROJK":   "Projk",
    "FIPOS":   "Fipos",
    "NPLNR":   "Nplnr",
    "AUFPL":   "Aufpl",
    "APLZL":   "Aplzl",
    "XEGDR":   "Xegdr",
    "DMBE2":   "Dmbe2",
    "DMBE3":   "Dmbe3",
    "DMB21":   "Dmb21",
    "DMB22":   "Dmb22",
    "DMB23":   "Dmb23",
    "DMB31":   "Dmb31",
    "DMB32":   "Dmb32",
    "DMB33":   "Dmb33",
    "BDIF3":   "Bdif3",
    "XRAGL":   "Xragl",
    "UZAWE":   "Uzawe",
    "XSTOV":   "Xstov",
    "MWST2":   "Mwst2",
    "MWST3":   "Mwst3",
    "SKNT2":   "Sknt2",
    "SKNT3":   "Sknt3",
    "XREF1":   "Xref1",
    "XREF2":   "Xref2",
    "XARCH":   "Xarch",
    "PSWSL":   "Pswsl",
    "PSWBT":   "Pswbt",
    "LZBKZ":   "Lzbkz",
    "LANDL":   "Landl",
    "IMKEY":   "Imkey",
    "VBEL2":   "Vbel2",
    "VPOS2":   "Vpos2",
    "POSN2":   "Posn2",
    "ETEN2":   "Eten2",
    "FISTL":   "Fistl",
    "GEBER":   "Geber",
    "DABRZ":   "Dabrz",
    "XNEGP":   "Xnegp",
    "KOSTL":   "Kostl",
    "RFZEI":   "Rfzei",
    "KKBER":   "Kkber",
    "EMPFB":   "Empfb",
    "PRCTR":   "Prctr",
    "XREF3":   "Xref3",
    "QSSKZ":   "Qsskz",
    "ZINKZ":   "Zinkz",
    "DTWS1":   "Dtws1",
    "DTWS2":   "Dtws2",
    "DTWS3":   "Dtws3",
    "DTWS4":   "Dtws4",
    "XPYPR":   "Xpypr",
    "KIDNO":   "Kidno",
    "ABSBT":   "Absbt",
    "CCBTC":   "Ccbtc",
    "PYCUR":   "Pycur",
    "PYAMT":   "Pyamt",
    "BUPLA":   "Bupla",
    "SECCO":   "Secco",
    "CESSION_KZ": "CessionKz",
    "PPDIFF":  "Ppdiff",
    "PPDIF2":  "Ppdif2",
    "PPDIF3":  "Ppdif3",
    "KBLNR":   "Kblnr",
    "KBLPOS":  "Kblpos",
    "GRANT_NBR": "GrantNbr",
    "GMVKZ":   "Gmvkz",
    "SRTYPE":  "Srtype",
    "LOTKZ":   "Lotkz",
    "FKBER":   "Fkber",
    "INTRENO": "Intreno",
    "PPRCT":   "Pprct",
    "BUZID":   "Buzid",
    "AUGGJ":   "Auggj",
    "BUDGET_PD": "BudgetPd",
    "PAYS_PROV": "PaysProv",
    "PAYS_TRAN": "PaysTran",
    "MNDID":   "Mndid",
    "KONTT":   "Kontt",
    "KONTL":   "Kontl",
    "UEBGDAT": "Uebgdat",
    "VNAME":   "Vname",
    "EGRUP":   "Egrupp",
    "BTYPE":   "Btype",
    "PROPMANO": "Propmano",
    # --- Additional fields from the SEGW model ---------------------
    "TAX_COUNTRY": "TaxCountry",
    "TXDAT_FROM":  "TxdatFrom",
    "FCSL":        "Fcsl",
    "RFCURR":      "Rfccur",
}


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
        json_data = response.json()
        results = json_data["d"]["results"]
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected SAP response shape: {e}",
        )

    return results


XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


class ProcessRequest(BaseModel):
    # The ECC rows the frontend already holds from GET /ar/ecc_data.
    # SAP is NOT called again here.
    records: List[Dict[str, Any]]


@router.post("/process")
def process_ar(payload: ProcessRequest):
    """
    Transforms the posted ECC AR rows to S/4, pushes them to the custom
    OData service, and returns the populated LTMC workbook as a download.
    """
    try:
        result = process_ar_records(payload.records, AR_TEMPLATE_PATH)
    except EccDataError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except TemplateError as e:
        raise HTTPException(status_code=500, detail=f"S/4 template problem: {e}")

    # Push to S/4 and capture the result
    push_result = {"status": "skipped", "message": "No rows to push."}
    if result.s4_rows:
        if not result.warnings:
            # Only push if there are no warnings (i.e., data is clean)
            push_result = push_to_s4(result.s4_rows)
        else:
            push_result["message"] = "Skipped push due to transformation warnings."

    # Log the push summary to the console
    print()
    print("=" * 70)
    print("S/4 PUSH SUMMARY")
    print("=" * 70)
    print(json.dumps(push_result, indent=2, default=str))
    print("=" * 70)
    print()

    # The filename is generated with a timestamp
    filename = f"AR_S4_Load_{datetime.now():%Y%m%d_%H%M%S}.xlsx"

    # Add push result to the response headers for visibility
    response_headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Record-Count": str(len(result.s4_rows)),
        "X-Warning-Count": str(len(result.warnings)),
        "X-S4-Push-Status": push_result.get("status", "unknown"),
    }
    if push_result.get("success_count") is not None:
        response_headers["X-S4-Push-Success"] = str(push_result["success_count"])
    if push_result.get("error_count") is not None:
        response_headers["X-S4-Push-Errors"] = str(push_result["error_count"])

    return StreamingResponse(
        result.output,
        media_type=XLSX_MEDIA_TYPE,
        headers=response_headers,
    )


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