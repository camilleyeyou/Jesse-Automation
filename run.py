#!/usr/bin/env python3
"""
Jesse A. Eisenbalm Automation - Quick Start Script
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     Jesse A. Eisenbalm - LinkedIn Automation System       ║
    ║     "The only business lip balm that keeps you human"     ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check for .env file
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("⚠️  No .env file found. Creating from .env.example...")
            import shutil
            shutil.copy(".env.example", ".env")
            print("📝 Please edit .env with your API keys before running.")
            sys.exit(1)
        else:
            print("❌ No .env or .env.example found!")
            sys.exit(1)
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed. Run: pip install python-dotenv")
    
    # Check for required API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set in .env")
        sys.exit(1)
    
    print("✅ Environment loaded")
    print("🚀 Starting API server on http://localhost:8001")
    print("   Dashboard: cd dashboard && npm run dev")
    print("   CLI: python cli/automation.py status")
    print("")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    # Start the API
    os.chdir("api")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", os.getenv("PORT", "8001")
    ])

if __name__ == "__main__":
    main()
