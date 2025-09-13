#!/usr/bin/env python3
"""
FFmpeg Demo Launcher
Automatically installs dependencies and runs the demo application
"""

import subprocess
import sys
import os

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required")
        return False
    return True

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def create_sample_files():
    """Create sample media files"""
    print("Creating sample media files...")
    try:
        subprocess.check_call([sys.executable, "create_samples.py"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating sample files: {e}")
        return False

def run_demo():
    """Run the main demo application"""
    print("Starting FFmpeg Demo Application...")
    try:
        subprocess.check_call([sys.executable, "ffmpeg_demo.py"])
    except subprocess.CalledProcessError as e:
        print(f"Error running demo: {e}")
    except KeyboardInterrupt:
        print("\nDemo application closed by user")

def main():
    """Main launcher function"""
    print("FFmpeg Demo Application Launcher")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Create sample files
    create_sample_files()
    
    # Run the demo
    run_demo()

if __name__ == "__main__":
    main()
