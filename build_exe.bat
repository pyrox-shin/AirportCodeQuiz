@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo  Checking Python
echo ============================================
python --version
if errorlevel 1 (
    echo [ERROR] "python" command not found.
    echo Please install Python and make sure "Add python.exe to PATH" was checked during install.
    goto :error
)

echo.
echo ============================================
echo  Step 1/4: Install / upgrade required packages
echo ============================================
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller pygame
if errorlevel 1 (
    echo [ERROR] pip install failed. See messages above.
    goto :error
)

echo.
echo ============================================
echo  Step 2/4: Build release exe (onedir mode)
echo ============================================
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist AviationQuiz.spec del /q AviationQuiz.spec
if exist AviationQuiz_debug.spec del /q AviationQuiz_debug.spec

python -m PyInstaller --onedir --noconsole --name AviationQuiz --hidden-import=list --hidden-import=mainV4 --hidden-import=airlinesV2 --hidden-import=theme --hidden-import=records launcher_main.py
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed. See messages above.
    goto :error
)

echo.
echo --- dist folder contents right after build ---
dir /s /b dist

if not exist "dist\AviationQuiz\AviationQuiz.exe" (
    echo [ERROR] Build command finished but dist\AviationQuiz\AviationQuiz.exe was not found.
    echo This is usually caused by antivirus software ^(e.g. Windows Defender^) deleting or
    echo quarantining the newly built exe right after it was created.
    echo Please check "Windows Security -^> Virus ^& threat protection -^> Protection history",
    echo and add this project folder to the antivirus exclusion list before trying again.
    goto :error
)

echo.
echo ============================================
echo  Step 3/4: Build debug exe (keeps console window)
echo  Use this one first if the release exe closes immediately without any window.
echo ============================================
python -m PyInstaller --onedir --name AviationQuiz_debug --hidden-import=list --hidden-import=mainV4 --hidden-import=airlinesV2 --hidden-import=theme --hidden-import=records launcher_main.py
if errorlevel 1 (
    echo [ERROR] Debug build failed. See messages above.
    goto :error
)

echo.
echo ============================================
echo  Step 4/4: Copy data files next to each exe
echo ============================================
if exist airport.csv       xcopy /y airport.csv dist\AviationQuiz\
if exist worldmap.geojson  xcopy /y worldmap.geojson dist\AviationQuiz\
if exist sounds            xcopy /y /e /i sounds dist\AviationQuiz\sounds\
if exist airlines          xcopy /y /e /i airlines dist\AviationQuiz\airlines\

if exist airport.csv       xcopy /y airport.csv dist\AviationQuiz_debug\
if exist worldmap.geojson  xcopy /y worldmap.geojson dist\AviationQuiz_debug\
if exist sounds            xcopy /y /e /i sounds dist\AviationQuiz_debug\sounds\
if exist airlines          xcopy /y /e /i airlines dist\AviationQuiz_debug\airlines\

echo.
echo ============================================
echo  DONE. This build uses "onedir" mode, so the exe files are:
echo    - dist\AviationQuiz\AviationQuiz.exe             (release build)
echo    - dist\AviationQuiz_debug\AviationQuiz_debug.exe  (debug build, shows console)
echo  Give the WHOLE dist\AviationQuiz folder to the end user, not just the exe.
echo  Run the debug build first to confirm everything works.
echo  If it still crashes, check dist\AviationQuiz_debug\error_log.txt for details.
echo ============================================
pause
exit /b 0

:error
echo.
echo Build failed. Please copy the full error text above and send it back to me.
pause
exit /b 1
