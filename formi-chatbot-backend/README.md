# Barbecue Nation Booking Chatbot

A conversational AI-powered booking system for Barbecue Nation restaurants.

## Overview

This chatbot system enables automated restaurant bookings through natural conversation, powered by OpenAI's language models and integrated with Google Sheets for booking management.

## Features

- AI-powered conversational booking
- Date and time slot management
- Party size handling
- Booking modifications
- Google Sheets integration
- Document-based training system

## Architecture

### Core Components

1. **FastAPI Backend**

   - WebSocket endpoint for real-time chat
   - REST endpoints for file uploads and spreadsheet management
   - CORS middleware for cross-origin requests

2. **Booking System**

   - Unique booking ID generation
   - Date and time validation
   - Party size management
   - Booking modification workflow

3. **AI Integration**

   - OpenAI GPT integration
   - Document-based training system
   - Context-aware responses

4. **Data Storage**
   - Google Sheets integration
   - Local file system for uploads
   - Training data persistence

### Training Flow

1. Upload training documents
2. Process documents using PyPDF2
3. Generate summaries
4. Store processed data in `training_data.txt`
5. Use stored data for context in OpenAI API calls

## Setup

### Prerequisites

- OpenAI API key
- Google Cloud account with Sheets API enabled

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
OPENAI_API_KEY=your_api_key
GOOGLE_SHEET_ID=your_sheet_id
```

3. Place Google service account credentials in `credentials.json`

### Running the Application

```bash
python main.py
```

## API Documentation

### Endpoints

- `POST /upload`: Upload training documents
- `POST /clear-spreadsheet`: Reset booking spreadsheet
- `WS /ws/{session_id}`: WebSocket endpoint for chat

### Booking Workflow

1. **New Booking**

   - User initiates booking through chat
   - System collects:
     - Name
     - Date (YYYY-MM-DD)
     - Time (HH:MM)
     - Number of persons
   - System generates booking ID
   - Booking stored in Google Sheets

2. **Booking Update**
   - User requests booking update
   - System verifies booking ID
   - User provides new booking details
   - System updates Google Sheets entry
