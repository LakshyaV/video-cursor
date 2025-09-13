@echo off
echo FFmpeg Demo Application
echo =====================
echo.
echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)
echo.
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo.
echo Creating sample media files...
python create_samples.py
echo.
echo Starting FFmpeg Demo Application...
python ffmpeg_demo.py
pause
