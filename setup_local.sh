#!/bin/bash

# NYC Ridehail Analytics Chatbot - Local Setup Script
set -e

echo "🚀 Setting up NYC Ridehail Analytics Chatbot for local testing..."
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

echo "✓ Python: $(python3 --version)"
echo "✓ Node.js: $(node --version)"
echo ""

# Setup backend
echo "🔧 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
TURNSTILE_SECRET_KEY=1x00000000000000000000AA
RATE_LIMIT_PER_MINUTE=5
RATE_LIMIT_PER_DAY=50
GLOBAL_DAILY_CAP=1000
DATA_DIR=../data
TAXI_ZONE_LOOKUP=../data/taxi_zone_lookup.csv
BASE_LOOKUP=../data/fhv_base_lookup.csv
DEBUG=true
EOF
    echo "✓ Created backend/.env"
else
    echo "✓ backend/.env already exists"
fi

cd ..

# Setup frontend
echo ""
echo "🔧 Setting up frontend..."
cd frontend

echo "Installing Node.js dependencies..."
npm install --silent

if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
VITE_API_URL=http://localhost:8000
VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA
EOF
    echo "✓ Created frontend/.env"
else
    echo "✓ frontend/.env already exists"
fi

cd ..

# Verify data files
echo ""
echo "📊 Verifying data files..."
if [ -f "data/fhvhv_tripdata_2023-01.parquet" ] && \
   [ -f "data/taxi_zone_lookup.csv" ] && \
   [ -f "data/fhv_base_lookup.csv" ]; then
    echo "✓ Data files found"
else
    echo "⚠️  Warning: Some data files may be missing"
    echo "   Ensure these exist:"
    echo "   - data/fhvhv_tripdata_2023-*.parquet"
    echo "   - data/taxi_zone_lookup.csv"
    echo "   - data/fhv_base_lookup.csv"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Start backend (in one terminal):"
echo "   cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo "   Or use: make backend-dev"
echo ""
echo "2. Start frontend (in another terminal):"
echo "   cd frontend && npm run dev"
echo "   Or use: make frontend-dev"
echo ""
echo "3. Open browser:"
echo "   http://localhost:5173"
echo ""
echo "4. Test with query:"
echo "   'Show hourly trips by company'"
echo ""
echo "📖 For detailed instructions, see LOCAL_TESTING.md"

