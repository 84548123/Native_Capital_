@echo off
title Native Capital
echo Launching Native Capital...
start cmd /k python server.py
cd frontend
start cmd /k npm run dev
timeout /t 3 >nul
start http://localhost:5173
