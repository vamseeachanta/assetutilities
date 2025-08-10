@echo off
REM Test the global environment directly
echo Testing Global AssetUtilities Environment
echo ========================================

REM Check if global environment exists
if not exist "%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe" (
    echo ERROR: Global environment not found at expected location
    echo Expected: %USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe
    pause
    exit /b 1
)

echo Found global Python at: %USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe
echo.

REM Run the test
"%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe" simple_test.py

echo.
echo Test completed.
pause