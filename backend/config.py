import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# LTMC "Customer Open Items" template that the AR processor populates.
AR_TEMPLATE_PATH = os.getenv(
    "AR_TEMPLATE_PATH",
    str(BASE_DIR / "templates" / "AR_Data_Load_Sheet_SIT2_slim.xlsx"),
)

# Staging folders for the fetch -> process -> validate -> load flow.
# Single-run mode: each folder holds at most one workbook at a time.
ECC_DATA_DIR = BASE_DIR / "ECC_DATA"
S4_DATA_DIR  = BASE_DIR / "S4_DATA"