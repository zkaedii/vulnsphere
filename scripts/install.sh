#!/bin/bash

set -e

echo "🔱 VulnSphere PRIME - Installation Script"
echo "=========================================="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js 18+ required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required"; exit 1; }

echo "✅ Prerequisites check passed"

# Backend setup
echo ""
echo "[1/5] Setting up Python backend..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Frontend setup
echo ""
echo "[2/5] Setting up Node.js frontend..."
cd frontend
npm install
npm run build
cd ..

# Database setup
echo ""
echo "[3/5] Starting database services..."
docker-compose up -d postgres redis timescale

# Wait for databases
echo "Waiting for databases to be ready..."
sleep 10

# Run migrations (if any)
echo ""
echo "[4/5] Running database migrations..."
# python backend/manage.py migrate

# Start services
echo ""
echo "[5/5] Starting VulnSphere PRIME..."
docker-compose up -d

echo ""
echo "✅ Installation complete!"
echo ""
echo "🌐 Access points:"
echo "   Frontend: http://localhost:3000"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔱 Energy field: ACTIVE"
