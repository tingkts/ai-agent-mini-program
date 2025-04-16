@echo off
cd /d "%~dp0"
python tts_gui.py
if errorlevel 1 pause
