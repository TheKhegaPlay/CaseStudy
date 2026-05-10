@echo off
REM Setup and health check script for Forensic GAN Platform MVP
REM For Windows

setlocal enabledelayedexpansion

echo.
echo 🚀 Forensic GAN Platform - Setup and Health Check (Windows)
echo ============================================================
echo.

REM Check Python
echo 📦 Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python not found
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✓ %PYTHON_VERSION%

REM Check Node.js
echo.
echo 📦 Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Node.js not found
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✓ Node.js !NODE_VERSION!

REM Check npm
echo.
echo 📦 Checking npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo ✗ npm not found
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo ✓ npm !NPM_VERSION!

REM Check CUDA (optional)
echo.
echo 📦 Checking CUDA (optional)...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo ℹ CUDA not found - will use CPU (slower inference)
) else (
    echo ✓ CUDA available - GPU acceleration enabled
)

REM Setup Backend
echo.
echo ============================================================
echo 📂 Setting up Backend...
echo ============================================================

if not exist "backend" (
    echo ✗ backend/ directory not found
    pause
    exit /b 1
)

cd backend

REM Create venv if not exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install requirements
echo Installing Python dependencies...
pip install -q -r requirements.txt --disable-pip-version-check

echo ✓ Backend setup complete

REM Check if model exists
echo.
if exist "..\models\aotgan_best.pth" (
    echo ✓ Model weights found
) else (
    echo ⚠ Model weights not found at models/aotgan_best.pth
    echo   Download from: https://github.com/TheKhegaPlay/AOT-GAN-for-paper
    echo   Or place your pretrained weights in the models/ directory
)

REM Verify imports
echo.
echo Verifying Python imports...
python -c "import torch; import fastapi; import PIL; print('✓ All required packages available')" >nul 2>&1
if errorlevel 1 (
    echo ✗ Missing dependencies
    pause
    exit /b 1
)

cd ..

REM Setup Frontend
echo.
echo ============================================================
echo 📂 Setting up Frontend...
echo ============================================================

if not exist "frontend" (
    echo ✗ frontend/ directory not found
    pause
    exit /b 1
)

cd frontend

REM Install npm dependencies
echo Installing npm dependencies...
npm install --silent

echo ✓ Frontend setup complete

cd ..

REM Summary
echo.
echo ============================================================
echo ✅ Setup Complete!
echo ============================================================
echo.
echo 📌 Next Steps:
echo.
echo 1️⃣  Start Backend (in Command Prompt):
echo    cd backend
echo    venv\Scripts\activate.bat
echo    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo 2️⃣  Start Frontend (in another Command Prompt):
echo    cd frontend
echo    npm run serve:ssr
echo.
echo 3️⃣  Open browser:
echo    http://localhost:4200
echo.
echo 4️⃣  Login with:
echo    Email: demo@forensics.gov
echo    Password: demo123
echo.
echo 📚 For more info, see README_MVP.md
echo.
pause
