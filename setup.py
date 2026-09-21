#!/usr/bin/env python3
"""
Setup script for Jarvis Voice Assistant
Installs all required dependencies for the Jarvis assistant.
"""

import subprocess
import sys

def install_requirements():
    """Install all required packages"""
    try:
        # Install requirements from requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("All dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def main():
    """Main setup function"""
    print("Setting up Jarvis Voice Assistant...")
    print("=" * 40)
    
    if install_requirements():
        print("=" * 40)
        print("Setup completed successfully!")
        print("Run 'python jarvis.py' to start the assistant.")
        print("")
        print("Before running, make sure:")
        print("1. LM Studio is installed and running")
        print("2. A model is loaded in LM Studio")
        print("3. The LM Studio API server is active at http://localhost:1234/v1")
    else:
        print("=" * 40)
        print("Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()