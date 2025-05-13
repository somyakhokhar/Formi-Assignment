import os
from pathlib import Path
import dotenv

dotenv.load_dotenv()

UPLOAD_DIR = Path("uploads")
TRAINING_DIR = Path("training")
TRAINING_FILE = TRAINING_DIR / "training_data.txt"

UPLOAD_DIR.mkdir(exist_ok=True)
TRAINING_DIR.mkdir(exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SHEET_RANGE = "Sheet1!A:F"

GOOGLE_SCOPES = ['https://www.googleapis.com/auth/spreadsheets'] 