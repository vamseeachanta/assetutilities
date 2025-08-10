@echo off
REM Global AssetUtilities Environment Activation Script
REM Copy this file to any repository to activate the global AssetUtilities environment

echo Activating AssetUtilities Global Environment...

REM Check if global environment exists
if not exist "%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\activate.bat" (
    echo ERROR: Global AssetUtilities environment not found!
    echo Please run setup-global-env.bat from the AssetUtilities repository first.
    echo.
    echo Expected location: %USERPROFILE%\.uv\envs\assetutilities-global
    pause
    exit /b 1
)

REM Activate the global environment
call "%USERPROFILE%\.uv\envs\assetutilities-global\Scripts\activate.bat"

echo.
echo ================================
echo AssetUtilities Global Environment Active
echo ================================
echo Python: %USERPROFILE%\.uv\envs\assetutilities-global\Scripts\python.exe
echo.
echo Available utilities:
echo - All AssetUtilities modules (excel, visualization, file management, etc.)
echo - Development tools (pytest, ruff, build tools)
echo - Web scraping tools (scrapy, selenium, playwright)
echo - Data processing tools (pandas, numpy, plotly)
echo.
echo Type 'deactivate' to exit this environment
echo.

REM Keep the command prompt open
cmd /k