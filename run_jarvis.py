#!/usr/bin/env python3
"""
Easy launcher for Jarvis Voice Assistant
This script provides a simple way to start the assistant with basic checks.
Launches the frontend GUI as the primary interaction interface.
"""

import subprocess
import sys
import os

def check_python():
    """Check if Python is available"""
    try:
        result = subprocess.run([sys.executable, '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✓ Python: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Python not found. Please install Python and add it to PATH.")
        return False

def check_lm_studio():
    """Check if LM Studio API is running"""
    try:
        import requests
        response = requests.get('http://localhost:1234/v1', timeout=5)
        if response.status_code == 200:
            print("✓ LM Studio API: Running")
            return True
        else:
            print("⚠ LM Studio API: Not responding properly")
            return False
    except Exception as e:
        print("⚠ LM Studio API: Not found at http://localhost:1234/v1")
        print("   Make sure LM Studio is running with a model loaded.")
        return False

def main():
    """Main launcher function"""
    print("Jarvis Voice Assistant - Easy Launcher")
    print("=" * 40)
    
    # Check prerequisites
    if not check_python():
        return 1
        
    check_lm_studio()
    
    print("\nStarting Jarvis frontend...")
    print("=" * 40)
    
    # Launch the frontend GUI (primary interaction interface)
    try:
        result = subprocess.run([sys.executable, 'run_frontend.py'])
        return result.returncode
    except KeyboardInterrupt:
        print("\nJarvis stopped by user.")
        return 0

if __name__ == "__main__":
    sys.exit(main())