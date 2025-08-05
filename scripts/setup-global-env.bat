@echo off
REM Global UV Environment Setup Script for Windows
REM This script sets up the AssetUtilities environment globally for use across repositories

echo ================================
echo AssetUtilities Global UV Environment Setup
echo ================================

REM Check if UV is installed
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: UV is not installed or not in PATH
    echo Please install UV first: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

echo UV version detected:
uv --version

REM Get the current directory (AssetUtilities repo root)
set ASSETUTILS_ROOT=%cd%

echo.
echo Setting up global environment from: %ASSETUTILS_ROOT%
echo.

REM Create a global environment using the local configuration
echo Creating global UV environment...
uv venv --python 3.13 "%USERPROFILE%\.uv\envs\assetutilities-global"

if %errorlevel% neq 0 (
    echo ERROR: Failed to create global environment
    pause
    exit /b 1
)

REM Activate the global environment and install dependencies
echo Installing dependencies to global environment...
call "%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\activate.bat"
uv pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Install AssetUtilities in development mode
echo Installing AssetUtilities in development mode...
uv pip install -e .

if %errorlevel% neq 0 (
    echo ERROR: Failed to install AssetUtilities
    pause
    exit /b 1
)

echo.
echo ================================
echo SUCCESS: Global environment created!
echo ================================
echo.
echo Global environment location: %USERPROFILE%\.uv\envs\assetutilities-global
echo.
echo To use in other repositories:
echo 1. Copy the activation script to your repo
echo 2. Run: activate-assetutils-global.bat
echo 3. Or use: uv run --python %USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe your_script.py
echo.

pause