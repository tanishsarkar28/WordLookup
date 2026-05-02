@echo off
echo Building WordLookup with PyInstaller...

REM Ensure pyinstaller is installed
pip install pyinstaller

REM Build the executable and bundle Tesseract
pyinstaller --noconfirm --onedir --windowed --exclude-module PySide6 --add-data "C:\Program Files\Tesseract-OCR;Tesseract-OCR" --add-data "dictionary_compact.json;." --add-data "icon.ico;." --icon="icon.ico" --name "WordLookup" "main.py"

echo Build complete! Executable should be in the dist/WordLookup folder.
pause
