@echo off
setlocal enabledelayedexpansion

:: ================================================
::          YOAIR - Setup Installer
:: ================================================
echo.
echo ================================================
echo          YOAIR - Setup Installer
echo ================================================
echo.

:: ================================================
:: CHECK 1: Python installed?
:: ================================================
echo [CHECK] Looking for Python...
python --version >nul 2>&1
if not errorlevel 1 (
    echo [OK] Python found:
    python --version
    echo.
    goto :check_pip
)

:: Python NOT found — install it
echo [INFO] Python not found. Installing latest Python...
echo.

:: Method 1: Try winget (Windows 10/11)
echo [1/4] Trying winget (Windows Package Manager)...
winget --version >nul 2>&1
if not errorlevel 1 (
    echo     Using winget to install Python...
    winget install Python.Python.3.13 --accept-package-agreements --accept-source-agreements
    if not errorlevel 1 goto :verify_python
    echo     winget install failed, trying alternate method...
) else (
    echo     winget not found, trying direct download...
)

:: Method 2: Direct download from python.org
echo.
echo [2/4] Downloading Python 3.13.1 from python.org...
set "PYTHON_URL=https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe"
set "PYTHON_EXE=%TEMP%\python-installer.exe"

powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_EXE%' -UseBasicParsing"

if not exist "%PYTHON_EXE%" (
    echo [!] Download failed.
    echo     Please install Python manually from: https://www.python.org/downloads/
    echo     Then run this script again.
    echo.
    pause
    exit /b 1
)
echo [OK] Downloaded

:: Install silently
echo.
echo [3/4] Running Python installer (silent)...
echo     This may take 1-3 minutes. Please wait...
"%PYTHON_EXE%" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

:: Wait for installer to finish (poll every 5s, max 180s)
set "WAIT_COUNT=0"
:wait_python
timeout /t 5 /nobreak >nul
set /a WAIT_COUNT+=5
python --version >nul 2>&1
if errorlevel 1 (
    if %WAIT_COUNT% LSS 180 goto :wait_python
    echo [!] Installation timed out.
    echo     Please install Python manually from: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Refresh PATH
set "PATH=%PATH%;C:\Program Files\Python313;C:\Program Files\Python313\Scripts"
del "%PYTHON_EXE%" 2>nul

:verify_python
echo.
echo [4/4] Verifying Python installation...
python --version
echo [OK] Python is ready
echo.

:: ================================================
:: CHECK 2: pip working?
:: ================================================
:check_pip
echo [CHECK] Verifying pip...
python -m pip --version >nul 2>&1
if not errorlevel 1 goto :check_deps

echo [INFO] pip not found. Installing pip...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%TEMP%\get-pip.py' -UseBasicParsing"
python "%TEMP%\get-pip.py"
del "%TEMP%\get-pip.py" 2>nul

:check_deps
echo [OK] pip ready
echo.

:: ================================================
:: INSTALL YOAIR DEPENDENCIES
:: ================================================
echo ================================================
echo       Installing YOAIR Dependencies
echo ================================================
echo.
echo Installing: opencv-python, mediapipe, numpy, pyautogui, pywin32
echo.

pip install opencv-python mediapipe numpy pyautogui pywin32
if errorlevel 1 (
    echo [!] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] All dependencies installed
echo.

:: ================================================
:: SETUP hand_landmarker.task MODEL
:: ================================================
echo ================================================
echo       Downloading AI Model
echo ================================================
echo.

set "MODEL_URL=https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
set "TASK_FILE=%~dp0YOAIR\YOAIR\hand_landmarker.task"

if exist "%TASK_FILE%" (
    echo [SKIP] hand_landmarker.task already present
) else (
    echo [INFO] Downloading hand_landmarker.task (~7.8MB)...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%MODEL_URL%' -OutFile '%TASK_FILE%' -UseBasicParsing"
    if errorlevel 1 (
        echo [!] Failed to download model. Check internet connection.
        pause
        exit /b 1
    )
    echo [OK] Model downloaded
)
echo.

:: ================================================
:: INSTALL YOAIR PACKAGE GLOBALLY
:: ================================================
echo ================================================
echo       Installing YOAIR Package
echo ================================================
echo.
pip install -e "%~dp0"
if errorlevel 1 (
    echo [!] Failed to install YOAIR.
    pause
    exit /b 1
)
echo [OK] YOAIR installed globally
echo.

:: ================================================
:: FINAL VERIFICATION
:: ================================================
echo ================================================
echo       Final Verification
echo ================================================
echo.

echo Python       : OK
python --version

echo pip          : OK
python -m pip --version

echo opencv-python: OK
python -c "import cv2; print('    version:', cv2.__version__)"

echo mediapipe    : OK
python -c "import mediapipe as mp; print('    version:', mp.__version__)"

echo numpy        : OK
python -c "import numpy; print('    version:', numpy.__version__)"

echo pyautogui    : OK
python -c "import pyautogui; print('    version:', pyautogui.__version__)"

echo win32api     : OK
python -c "import win32api; print('    available')"

echo YOAIR import : OK
python -c "import YOAIR; print('    ready')"

echo.
echo ================================================
echo  INSTALLATION COMPLETE!
echo ================================================
echo.
echo Usage: Open any Python file and type:
echo.
echo   import YOAIR
echo.
echo Controls:
echo   - Right/Left hand movement  = Move cursor (35x)
echo   - Right middle+thumb pinch  = Double click
echo   - Left middle+thumb pinch   = Single click
echo   - Left thumb UP (hold)     = Scroll up
echo   - Left thumb DOWN (hold)    = Scroll down
echo   - Both palms joined        = Exit
echo.
pause
