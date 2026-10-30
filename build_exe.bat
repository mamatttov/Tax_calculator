@echo off
REM Builds dist\Kalkulyator.exe from okno.py
.\.venv\Scripts\python.exe -m pip install pyinstaller openpyxl
.\.venv\Scripts\python.exe -m PyInstaller --onefile --windowed --name Kalkulyator okno.py
echo.
echo Done: dist\Kalkulyator.exe
pause
