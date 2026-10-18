"""
MediPulse EHR - Production WSGI Runner
CSE494: Intelligent NoSQL Databases
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from app import app

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    
    print("=" * 60)
    print("  MediPulse EHR - Production WSGI Server")
    print(f"  Listening on: http://{host}:{port}/")
    print("=" * 60)
    
    if sys.platform.startswith("win"):
        try:
            from waitress import serve
            print("[INFO] Serving with Waitress (Production WSGI for Windows)...")
            serve(app, host=host, port=port, threads=8)
        except ImportError:
            print("[WARN] Waitress not installed, falling back to standard server...")
            app.run(host=host, port=port, debug=False)
    else:
        try:
            import gunicorn
            print("[INFO] On Linux/Unix, recommend running: gunicorn -b 0.0.0.0:5000 app:app")
        except ImportError:
            pass
        from waitress import serve
        serve(app, host=host, port=port, threads=8)
