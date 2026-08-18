@echo off
cd /d "%~dp0"
title JARVIS
python "99_Meta/tools/jarvis.py"
echo.
echo ---- Jarvis chiuso. Premi un tasto per uscire. ----
pause >nul
