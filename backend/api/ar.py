from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import requests
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

ODATA_URL = (
    "http://ec2-54-158-63-191.compute-1.amazonaws.com:8080/"
    "sap/opu/odata/SAP/Z_BSID_ODATA_AR1_SRV/ZBSIDItemSet"
)
SAP_USERNAME = os.getenv("SAP_USERNAME")
SAP_PASSWORD = os.getenv("SAP_PASSWORD")


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