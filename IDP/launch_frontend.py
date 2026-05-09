"""
Launch Script - Start RTI-Lens Frontend with Timeline Visualization
This script will start both backend and frontend in the correct order
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def check_port(port):
    """Check if a port is in use"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def main():
    print("="*60)
    print("  RTI-Lens Frontend Launcher")
    print("="*60)

    # Check if we're in the right directory
    if not Path("streamlit_app.py").exists():
        print("\n[ERROR] streamlit_app.py not found!")
        print("Please run this script from the IDP directory")
        sys.exit(1)

    print("\n[1/3] Checking backend...")
    if check_port(8001):
        print("[OK] Backend is already running on port 8001")
    else:
        print("[INFO] Backend not running. Please start it in another terminal:")
        print("       uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload")
        print("\nPress Enter once backend is running...")
        input()

    print("\n[2/3] Checking Streamlit...")
    if check_port(8501):
        print("[OK] Streamlit is already running on port 8501")
        print("\n[INFO] Open your browser to: http://localhost:8501")
    else:
        print("[INFO] Starting Streamlit frontend...")
        print("\n" + "="*60)
        print("  Frontend will open in your browser")
        print("  Navigate to the 'Timeline' tab (6th tab)")
        print("="*60 + "\n")

        # Start Streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])

    print("\n[3/3] Access Instructions:")
    print("  1. Open browser to: http://localhost:8501")
    print("  2. Click the 'Timeline' tab (📅)")
    print("  3. Select 'Demo: Sample Timeline'")
    print("  4. Explore the visualization!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Launcher stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        sys.exit(1)
