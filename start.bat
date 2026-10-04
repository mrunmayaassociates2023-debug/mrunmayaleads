@echo off
title MRUNMAYA ASSOCIATES Portal Server
echo ===================================================
echo Starting MRUNMAYA ASSOCIATES Portal...
echo Family Dandia Night 2026 and Razorpay Live Gateway
echo ===================================================
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
