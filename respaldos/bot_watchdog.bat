@echo off
cd /d C:\aprs_bot
:loop
echo [%date% %time%] arrancando aprs_bot.py
python aprs_bot.py
echo [%date% %time%] bot cayo, reiniciando en 15 s...
timeout /t 15 /nobreak >nul
goto loop
