# Chat to Purchase Example

This is a chat to purchase agent example

## Setup Steps

1. Install Python requirements: `pip install -r requirements.txt`
2. Create `.env` file in root directory with required environment variables
3. Start database: `docker-compose up -d`
4. Populate database: `python3 database/populate_db.py`
5. Start frontend: `cd frontend && npm run dev`
6. Start backend: `./start-backend.sh` (or `python3 backend/main.py`)
