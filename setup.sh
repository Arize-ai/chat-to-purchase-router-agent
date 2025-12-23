#!/bin/bash
set -e

echo "🚀 Setting up Chat to Purchase project..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install Python requirements
echo "📥 Installing Python requirements..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📋 Copying .env.example to .env..."
        cp .env.example .env
        echo "⚠️  Please edit .env file and add your API keys and configuration."
        echo "   Required: OPENAI_API_KEY"
        echo "   Optional: ARIZE_SPACE_ID, ARIZE_API_KEY (for tracing)"
        read -p "   Press Enter to continue after updating .env, or Ctrl+C to exit..."
    else
        echo "⚠️  Warning: .env file not found and .env.example doesn't exist!"
        echo "   Please create a .env file in the root directory with required environment variables."
        echo "   Required variables: OPENAI_API_KEY, ARIZE_SPACE_ID, ARIZE_API_KEY, DB_*"
        read -p "   Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "✅ .env file found"
fi

# Start database
echo "🐳 Starting database..."
docker-compose up -d

# Wait a moment for database to be ready
sleep 2

# Check if database needs to be populated
echo "📊 Checking database..."
DB_COUNT=$(docker-compose exec -T postgres psql -U postgres -d chat_to_purchase -t -c "SELECT COUNT(*) FROM products;" 2>/dev/null | xargs || echo "0")

if [ "$DB_COUNT" = "0" ] || [ -z "$DB_COUNT" ]; then
    echo "📥 Populating database..."
    python3 database/populate_db.py
else
    echo "✅ Database already populated ($DB_COUNT products found)"
fi

# Install npm dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "✅ Frontend dependencies already installed"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application, run:"
echo "  cd frontend && npm run dev:all"

