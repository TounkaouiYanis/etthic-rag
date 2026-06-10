@echo off
cd /d "%~dp0"
py -m streamlit run scripts\chat.py
pause