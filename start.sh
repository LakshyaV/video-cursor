#!/bin/bash

# Professional Video Editor Startup Script
echo "Starting Professional Video Editor..."

# Check if we're in the correct directory
if [ ! -f "backend/server.py" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Install dependencies if needed
echo "Installing dependencies..."
cd backend

# Check if virtual environment exists
if [ ! -d "htn" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv htn
fi

# Activate virtual environment
echo "Activating virtual environment..."
source htn/bin/activate

# Install Python dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p uploads outputs

# Check for environment variables
if [ ! -f ".env" ]; then
    echo " Creating .env file..."
    cat > .env << EOL
# Add your API keys here
COHERE_API_KEY=your_cohere_api_key_here
api_key_1=your_twelvelabs_api_key_here

# Optional: Set custom upload/output directories
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
EOL
    echo "📝 Please edit backend/.env with your API keys"
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found. Please install FFmpeg."
fi

# Start the FastAPI server
python server.py
