@echo off
cd /d "C:\Users\pc\Documents\AI_Document_summarizer"
start "backend" python serve_frontend.py
start "frontend" python -m http.server 8001
