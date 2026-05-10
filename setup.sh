#!/bin/bash
# Setup and health check script for Forensic GAN Platform MVP

set -e

echo "🚀 Forensic GAN Platform - Setup & Health Check"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "📦 Checking Python..."
if ! command -v python &> /dev/null; then
    echo -e "${RED}✗ Python not found${NC}"
    echo "Please install Python 3.9+ from https://python.org"
    exit 1
fi
PYTHON_VERSION=$(python --version)
echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"

# Check Node.js
echo ""
echo "📦 Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found${NC}"
    echo "Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION${NC}"

# Check npm
echo ""
echo "📦 Checking npm..."
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found${NC}"
    exit 1
fi
NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ npm $NPM_VERSION${NC}"

# Check CUDA (optional)
echo ""
echo "📦 Checking CUDA (optional)..."
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ CUDA available - GPU acceleration enabled${NC}"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo -e "${YELLOW}ℹ CUDA not found - will use CPU (slower inference)${NC}"
fi

# Setup Backend
echo ""
echo "=================================================="
echo "📂 Setting up Backend..."
echo "=================================================="

if [ ! -d "backend" ]; then
    echo -e "${RED}✗ backend/ directory not found${NC}"
    exit 1
fi

cd backend

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate venv
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null || true

# Install requirements
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

echo -e "${GREEN}✓ Backend setup complete${NC}"

# Check if model exists
echo ""
if [ -f "../models/aotgan_best.pth" ]; then
    echo -e "${GREEN}✓ Model weights found${NC}"
else
    echo -e "${YELLOW}⚠ Model weights not found at models/aotgan_best.pth${NC}"
    echo "  Download from: https://github.com/TheKhegaPlay/AOT-GAN-for-paper"
    echo "  Or place your pretrained weights in the models/ directory"
fi

# Verify imports
echo ""
echo "Verifying Python imports..."
python -c "import torch; import fastapi; import PIL; print('✓ All required packages available')" || {
    echo -e "${RED}✗ Missing dependencies${NC}"
    exit 1
}

cd ..

# Setup Frontend
echo ""
echo "=================================================="
echo "📂 Setting up Frontend..."
echo "=================================================="

if [ ! -d "frontend" ]; then
    echo -e "${RED}✗ frontend/ directory not found${NC}"
    exit 1
fi

cd frontend

# Install npm dependencies
echo "Installing npm dependencies..."
npm install -q

echo -e "${GREEN}✓ Frontend setup complete${NC}"

cd ..

# Summary
echo ""
echo "=================================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "📌 Next Steps:"
echo ""
echo "1️⃣  Start Backend:"
echo "   cd backend"
echo "   source venv/bin/activate  # Linux/Mac"
echo "   # or: venv\\Scripts\\activate  # Windows"
echo "   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "2️⃣  Start Frontend (in another terminal):"
echo "   cd frontend"
echo "   npm run serve:ssr"
echo ""
echo "3️⃣  Open browser:"
echo "   http://localhost:4200"
echo ""
echo "4️⃣  Login with:"
echo "   Email: demo@forensics.gov"
echo "   Password: demo123"
echo ""
echo "📚 For more info, see README_MVP.md"
echo ""
