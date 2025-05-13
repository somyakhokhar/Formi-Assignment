
# Formi Chatbot

A full-stack chat interface application consisting of a React-based frontend and Python-based backend for the Formi Chatbot service.

## Demo

https://drive.google.com/file/d/1TQb1cUX-9DfbCHEyJQSNZqRGwdp_AE3J/view?usp=sharing

## Project Structure

- formi-chatbot-frontend/ - React-based frontend application
- formi-chatbot-backend/ - Python-based backend server

## Frontend Setup

### Prerequisites

- Node.js and npm installed

### Installation

1. Clone the repository:

bash
git clone https://github.com/somyakhokhar/Formi-Assignment.git


2. Navigate to the frontend directory and install dependencies:

bash
cd formi-chatbot-frontend
npm install


3. Start the development server:

bash
npm run dev


The frontend application will be available at http://localhost:5173

### WebSocket Connection

The frontend connects to a WebSocket server at ws://localhost:8765. Ensure the backend server is running before starting the frontend application.

## Backend Setup

### Prerequisites

- Python 3.x
- PyCharm Community Edition (recommended)

### Installation

1. Navigate to the backend directory:

bash
cd formi-chatbot-backend


2. Set up and activate virtual environment:

bash
source ./.venv/bin/activate


3. Install dependencies:

bash
pip install -r requirements.txt


### Configuration

1. Create a .env file in the backend directory with the following variables:

bash
OPENAI_API_KEY=your_openai_api_key
GOOGLE_SHEET_ID=your_google_sheet_id


2. Google Cloud Platform Setup:
   - Create a service account on GCP
   - Download the credentials file
   - Place credentials.json in the backend folder

### Running the Server

Start the backend server:

bash
python main.py


## Data Management

The application uses Google Sheets for data storage:

- Spreadsheet URL: [Formi Chatbot Data](https://docs.google.com/spreadsheets/d/1n-v04zXcOnVZmSKHshgGKFwbkd_trzT6ws6WindW6gE/edit?gid=0#gid=0)

