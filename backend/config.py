import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# LTMC "Customer Open Items" template that the AR processor populates.
# Uses the slim copy (header rows + one style row); the original SIT2 file
# carries ~30k empty styled rows and takes ~20s to open. Override with the
# AR_TEMPLATE_PATH env var if the template moves.
AR_TEMPLATE_PATH = os.getenv(
    "AR_TEMPLATE_PATH",
    str(BASE_DIR / "templates" / "AR_Data_Load_Sheet_SIT2_slim.xlsx"),
)