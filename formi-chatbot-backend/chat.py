import json
import asyncio
from datetime import datetime
from fastapi import WebSocket
from services import add_booking, update_booking, load_training_data
from config import OPENAI_API_KEY
import openai

client = openai.OpenAI(api_key=OPENAI_API_KEY)

class ChatManager:
    def __init__(self):
        self.active_connections = {}
        self.chat_sessions = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = {
                "messages": [],
                "summary": await load_training_data(),
                "booking_state": None,
                "booking_data": {}
            }
            
            await self.stream_response(websocket, self.chat_sessions[session_id]["summary"])

    async def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def stream_response(self, websocket: WebSocket, response_text: str):
        chunk_size = 20
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i + chunk_size]
            await websocket.send_json({
                "content": chunk,
                "status": "streaming"
            })
            await asyncio.sleep(0.05)
        
        await websocket.send_json({"status": "end"})

    async def handle_message(self, websocket: WebSocket, session_id: str, message: str):
        session = self.chat_sessions[session_id]
        session["messages"].append({"role": "user", "content": message})
        
        response = await self.process_message(session, message)
        await self.stream_response(websocket, response)
        
        session["messages"].append({"role": "assistant", "content": response})

    async def process_message(self, session: dict, message: str) -> str:
        if session["booking_state"] is None:
            if "book" in message.lower() or "reservation" in message.lower():
                session["booking_state"] = "ask_name"
                return "Great! Let's make your reservation. What's your name?"
            elif "update" in message.lower():
                session["booking_state"] = "ask_booking_id"
                return "Please provide your booking ID to update your reservation."
            else:
                messages = [
                    {"role": "system", "content": session["summary"]}
                ]
                messages.extend(session["messages"])
                messages.append({"role": "user", "content": message})
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    stream=False
                ).choices[0].message.content
                return response

        elif session["booking_state"] == "ask_name":
            session["booking_data"]["name"] = message
            session["booking_state"] = "ask_date"
            return "What date would you like to make the reservation for? (Please provide in YYYY-MM-DD format)"

        elif session["booking_state"] == "ask_date":
            try:
                datetime.strptime(message, '%Y-%m-%d')
                session["booking_data"]["date"] = message
                session["booking_state"] = "ask_time"
                return "What time would you like to make the reservation for? (Please provide in HH:MM format)"
            except ValueError:
                return "Please provide the date in YYYY-MM-DD format (e.g., 2024-03-20)"

        elif session["booking_state"] == "ask_time":
            try:
                datetime.strptime(message, '%H:%M')
                session["booking_data"]["time"] = message
                session["booking_state"] = "ask_persons"
                return "How many persons will be dining?"
            except ValueError:
                return "Please provide the time in HH:MM format (e.g., 19:30)"

        elif session["booking_state"] == "ask_persons":
            try:
                persons = int(message)
                if persons > 0:
                    session["booking_data"]["persons"] = persons
                    booking_id = await add_booking(session["booking_data"])
                    session["booking_state"] = None
                    session["booking_data"] = {}
                    return f"Great! Your booking has been confirmed. Your booking ID is: {booking_id}\n\nPlease keep this ID safe for any future modifications to your reservation."
                else:
                    return "Please provide a valid number of persons (greater than 0)."
            except ValueError:
                return "Please provide a valid number of persons."

        elif session["booking_state"] == "ask_booking_id":
            if len(message) == 8:
                session["booking_data"]["booking_id"] = message
                session["booking_state"] = "update_name"
                return "What's the name for this booking?"
            else:
                return "Please provide a valid 8-character booking ID."

        elif session["booking_state"] == "update_name":
            session["booking_data"]["name"] = message
            session["booking_state"] = "update_date"
            return "What's the new date for your reservation? (Please provide in YYYY-MM-DD format)"

        elif session["booking_state"] == "update_date":
            try:
                datetime.strptime(message, '%Y-%m-%d')
                session["booking_data"]["date"] = message
                session["booking_state"] = "update_time"
                return "What's the new time for your reservation? (Please provide in HH:MM format)"
            except ValueError:
                return "Please provide the date in YYYY-MM-DD format (e.g., 2024-03-20)"

        elif session["booking_state"] == "update_time":
            try:
                datetime.strptime(message, '%H:%M')
                session["booking_data"]["time"] = message
                session["booking_state"] = "update_persons"
                return "How many persons will be dining?"
            except ValueError:
                return "Please provide the time in HH:MM format (e.g., 19:30)"

        elif session["booking_state"] == "update_persons":
            try:
                persons = int(message)
                if persons > 0:
                    session["booking_data"]["persons"] = persons
                    success = await update_booking(
                        session["booking_data"]["booking_id"],
                        session["booking_data"]
                    )
                    session["booking_state"] = None
                    session["booking_data"] = {}
                    return "Your booking has been successfully updated!" if success else "Sorry, I couldn't find your booking. Please check the booking ID and try again."
                else:
                    return "Please provide a valid number of persons (greater than 0)."
            except ValueError:
                return "Please provide a valid number of persons." 