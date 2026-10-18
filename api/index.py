import os
import sys

# Add parent directory to sys.path so app and its packages can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel Serverless Function entry point
# Vercel's @vercel/python builder looks for 'app' WSGI instance
