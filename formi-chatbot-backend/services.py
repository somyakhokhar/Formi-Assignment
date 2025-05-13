import uuid
from datetime import datetime
import openai
from google.oauth2 import service_account
from googleapiclient.discovery import build
import aiofiles
import PyPDF2
import io
from config import *

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_google_sheets_service():
    creds = service_account.Credentials.from_service_account_file('credentials.json', scopes=GOOGLE_SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

async def clear_spreadsheet():
    service = get_google_sheets_service()
    service.values().clear(spreadsheetId=GOOGLE_SHEET_ID, range=GOOGLE_SHEET_RANGE).execute()
    headers = [['Booking ID', 'Name', 'Date', 'Time', 'Number of Persons', 'Created At']]
    service.values().update(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=GOOGLE_SHEET_RANGE,
        valueInputOption='RAW',
        body={'values': headers}
    ).execute()
    return True

async def add_booking(booking_data):
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
    service.values().append(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=GOOGLE_SHEET_RANGE,
        valueInputOption='RAW',
        body={'values': values}
    ).execute()
    return booking_id

async def update_booking(booking_id, booking_data):
    service = get_google_sheets_service()
    result = service.values().get(spreadsheetId=GOOGLE_SHEET_ID, range=GOOGLE_SHEET_RANGE).execute()
    values = result.get('values', [])
    
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
            service.values().update(
                spreadsheetId=GOOGLE_SHEET_ID,
                range=GOOGLE_SHEET_RANGE,
                valueInputOption='RAW',
                body={'values': values}
            ).execute()
            return True
    return False

async def summarize_file_content(content):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
            {"role": "user", "content": f"Please summarize the following content:\n\n{content}"}
        ]
    )
    return response.choices[0].message.content

async def save_training_data(content):
    async with aiofiles.open(TRAINING_FILE, 'a') as f:
        await f.write(f"\n\n{content}")

async def load_training_data():
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

async def process_uploaded_file(content, filename):
    if filename.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text_content = "".join(page.extract_text() for page in pdf_reader.pages)
    else:
        text_content = content.decode()
    
    summary = await summarize_file_content(text_content)
    await save_training_data(summary)
    return summary 