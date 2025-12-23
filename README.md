# Chat-to-Purchase Agent Demo

This example showcases a conversational shopping agent that allows users to search for products and add items to their cart entirely through chat.

The agent is fully instrumented with Arize AX, providing detailed traces of agent actions, tool usage, and complete conversation flows via session-level views.

## Prerequisites

Before running the setup, make sure you have the following installed:

- **Python 3** (with `pip`)
- **Node.js** and `npm`
- **Docker** and `docker-compose` (Docker Desktop must be running)

## Quick Start

### First Time Setup

Run the setup script to install dependencies and configure the project:

```bash
chmod +x setup.sh
./setup.sh
```

**Note:** Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `ARIZE_SPACE_ID` - Arize space ID (optional, for tracing)
- `ARIZE_API_KEY` - Arize API key (optional, for tracing)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database configuration (prefilled in `.env.example`) 

### Start the Application

After setup, start both frontend and backend in a single terminal:

```bash
cd frontend && npm run dev:all
```

This will start:
- Frontend on [http://localhost:3000](http://localhost:3000) 

This is where you can browse the products, chat with the agent to learn more about the products and add them to your cart.