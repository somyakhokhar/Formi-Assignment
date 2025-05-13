import os
import json
import uuid
from typing import Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import openai
from pathlib import Path
import aiofiles
import PyPDF2
import io
import dotenv
import asyncio
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
from services import clear_spreadsheet, process_uploaded_file
from chat import ChatManager

dotenv.load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
TRAINING_DIR = Path("training")
UPLOAD_DIR.mkdir(exist_ok=True)
TRAINING_DIR.mkdir(exist_ok=True)

# Store active connections and chat sessions
active_connections: Dict[str, WebSocket] = {}
chat_sessions: Dict[str, Dict] = {}

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')
RANGE_NAME = "Sheet1!A:F" 

def get_google_sheets_service():
    """Initialize and return Google Sheets service."""
    try:
        creds = service_account.Credentials.from_service_account_file(
            'credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        return service.spreadsheets()
    except Exception as e:
        print(f"Error initializing Google Sheets service: {e}")
        raise

async def clear_spreadsheet():
    """Clear all data from the Bookings sheet."""
    try:
        service = get_google_sheets_service()
        
        # Clear the sheet
        service.values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        # Add headers
        headers = [['Booking ID', 'Name', 'Date', 'Time', 'Number of Persons', 'Created At']]
        body = {
            'values': headers
        }
        
        service.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        return True
    except Exception as e:
        print(f"Error clearing spreadsheet: {e}")
        raise

async def add_booking(booking_data: Dict) -> str:
    """Add a new booking to Google Sheets."""
    try:
        service = get_google_sheets_service()
        booking_id = str(uuid.uuid4())[:8]
        
        values = [[
            booking_id,
            booking_data['name'],
            booking_data['date'],
            booking_data['time'],
            booking_data['persons'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]]
        
        body = {
            'values': values
        }
        
        result = service.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        return booking_id
    except Exception as e:
        print(f"Error adding booking to Google Sheets: {e}")
        raise

async def update_booking(booking_id: str, booking_data: Dict) -> bool:
    """Update an existing booking in Google Sheets."""
    try:
        service = get_google_sheets_service()
        
        # Get all bookings
        result = service.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        values = result.get('values', [])
        
        # Find and update the booking
        for i, row in enumerate(values):
            if row[0] == booking_id:
                values[i] = [
                    booking_id,
                    booking_data['name'],
                    booking_data['date'],
                    booking_data['time'],
                    booking_data['persons'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
                
                body = {
                    'values': values
                }
                
                service.values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=RANGE_NAME,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                return True
        
        return False
    except Exception as e:
        print(f"Error updating booking in Google Sheets: {e}")
        raise

TRAINING_FILE = TRAINING_DIR / "training_data.txt"

async def summarize_file_content(content: str) -> str:
    """Summarize file content using OpenAI API."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
                {"role": "user", "content": f"Please summarize the following content:\n\n{content}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in summarization: {e}")
        return "Error summarizing content"

async def save_training_data(content: str):
    """Save training data to the common file."""
    async with aiofiles.open(TRAINING_FILE, 'a') as f:
        await f.write(f"\n\n{content}")

async def load_training_data() -> str:
    """Load training data from the common file."""
    if TRAINING_FILE.exists():
        async with aiofiles.open(TRAINING_FILE, 'r') as f:
            return await f.read()
    return """Welcome to Barbecue Nation Booking Assistant! I can help you with:
1. Making new reservations
2. Updating existing bookings
3. Information about our menu and locations
4. Special offers and timings

To make a booking, just say 'I want to book a table' or 'Make a reservation'.
To update an existing booking, say 'Update my booking' and provide your booking ID."""

chat_manager = ChatManager()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    summary = await process_uploaded_file(content, file.filename)
    return {"status": "success", "message": "File uploaded and added to training data"}

async def stream_response(response_text: str, websocket: WebSocket):
    """Stream the response in chunks."""
    chunk_size = 20  # Number of characters per chunk
    for i in range(0, len(response_text), chunk_size):
        chunk = response_text[i:i + chunk_size]
        await websocket.send_json({
            "content": chunk,
            "status": "streaming"
        })
        await asyncio.sleep(0.05)  # Small delay between chunks
    
    # Send end status
    await websocket.send_json({
        "status": "end"
    })

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await chat_manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            await chat_manager.handle_message(websocket, session_id, message_data["message"])
    except WebSocketDisconnect:
        await chat_manager.disconnect(session_id)
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
        await chat_manager.disconnect(session_id)

@app.post("/clear-spreadsheet")
async def clear_spreadsheet_endpoint():
    try:
        await clear_spreadsheet()
        return {"status": "success", "message": "Spreadsheet cleared successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=True) 