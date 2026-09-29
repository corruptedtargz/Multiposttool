@echo off
echo ==========================================
echo  Building Clip Poster. This takes a few
echo  minutes. Do not close this window.
echo ==========================================
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto fail
python -m PyInstaller --noconfirm --onefile --windowed --name ClipPoster --add-data "static;static" --collect-submodules uvicorn --collect-data googleapiclient --hidden-import multipart main.py
if errorlevel 1 goto fail
echo.
echo ==========================================
echo  SUCCESS! Your app is in the "dist" folder:
echo  dist\ClipPoster.exe
echo ==========================================
pause
exit /b 0
:fail
echo.
echo ==========================================
echo  Something went wrong. Take a screenshot of
echo  this window and send it to Claude.
echo ==========================================
pause
exit /b 1
