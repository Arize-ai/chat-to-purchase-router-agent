# Chat-to-Purchase Agent Demo

This example showcases a conversational shopping agent that allows users to search for products and add items to their cart entirely through chat.

The agent is fully instrumented with Arize AX, providing detailed traces of agent actions, tool usage, and complete conversation flows via session-level views.

![Shopping Assistant Chat](https://storage.googleapis.com/arize-phoenix-assets/assets/images/chat-to-purchase-chat.png)

## Prerequisites

Before running the setup, make sure you have the following installed:

- **Python 3.9 to 3.13** 
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

## Agent Structure

- **PostgreSQL Database**: Contains product information including images, descriptions, prices, ratings, and categories
- **Natural Language Search Tool** (`search_products_nl`): Converts conversational queries (ex: "running shoes under $100" or "highly rated casual shoes") into SQL and returns matching products with all their details
- **Product Reference Detection Tool** (`agent_references_products`): Uses an LLM to determine if the agent's response mentions specific products, which triggers the display of "Add to Cart" buttons in the UI

## Project Structure

- **`backend/`**: FastAPI server (`api.py`) and agent logic (`agent/router.py`, `agent/db_queries.py`) for handling chat requests and product searches
- **`database/`**: PostgreSQL database initialization script (`init.sql`) and population script (`populate_db.py`) with cached product data
- **`frontend/`**: Next.js application with React components for product browsing, chat interface, and cart management
- **Root files**: `instrumentation.py` for Arize AX tracing, `requirements.txt` for Python dependencies, `setup.sh` for project setup, and `docker-compose.yml` for database configuration

## Tracing in Arize AX

Each request to the chatbot is captured as a detailed trace in Arize AX, showing every tool call, LLM call, and database retrieval in context. You can view individual traces to understand exactly how the agent processes each user message, including which tools were invoked and what data was retrieved. 

![CAgent Trace](https://storage.googleapis.com/arize-phoenix-assets/assets/images/chat-to-purchase-trace.png)

For a complete view of the conversation flow, session views aggregate all traces from a single conversation, allowing you to see the entire interaction from start to finish.

![Session View of Full Conversation](https://storage.googleapis.com/arize-phoenix-assets/assets/images/shopping-assistant-session-view.png)


