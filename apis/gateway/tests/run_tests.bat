@echo off
REM run_tests.bat - Test runner script for Windows

setlocal enabledelayedexpansion

echo ======================================
echo Vecinita Test Suite Runner
echo ======================================
echo.

REM Check if pytest is installed
python -m pytest --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: pytest not found. Install with: pip install pytest
    exit /b 1
)

REM Parse command line arguments
set TEST_TYPE=%1
if "!TEST_TYPE!"=="" set TEST_TYPE=unit

set VERBOSE=%2
if "!VERBOSE!"=="" set VERBOSE=-v

if "!TEST_TYPE!"=="unit" (
    echo Running unit tests...
    python -m pytest tests/ -m unit !VERBOSE!
) else if "!TEST_TYPE!"=="integration" (
    echo Running integration tests...
    python -m pytest tests/ -m integration !VERBOSE!
) else if "!TEST_TYPE!"=="ui" (
    echo Running UI tests...
    echo WARNING: Make sure the server is running: uv run uvicorn main:app --host localhost --port 8000
    python -m pytest tests/test_ui.py -m ui !VERBOSE! --run-skipped
) else if "!TEST_TYPE!"=="db" (
    echo Running database tests...
    python -m pytest tests/ -m db !VERBOSE!
) else if "!TEST_TYPE!"=="api" (
    echo Running API tests...
    python -m pytest tests/ -m api !VERBOSE!
) else if "!TEST_TYPE!"=="all" (
    echo Running all tests...
    python -m pytest tests/ !VERBOSE!
) else if "!TEST_TYPE!"=="coverage" (
    echo Running tests with coverage report...
    python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing !VERBOSE!
    echo Coverage report generated in htmlcov\index.html
) else if "!TEST_TYPE!"=="help" (
    echo Usage: run_tests.bat [test_type] [verbose_level]
    echo.
    echo test_type options:
    echo   unit        - Run unit tests only (default^)
    echo   integration - Run integration tests
    echo   ui          - Run UI tests with Playwright
    echo   db          - Run database tests
    echo   api         - Run API endpoint tests
    echo   all         - Run all tests
    echo   coverage    - Run tests with coverage report
    echo   help        - Show this help message
    echo.
    echo verbose_level options:
    echo   -v          - Verbose output (default^)
    echo   -q          - Quiet output
    echo   -vv         - Very verbose output
    echo.
    echo Examples:
    echo   run_tests.bat unit          # Run unit tests
    echo   run_tests.bat all -vv       # Run all tests with very verbose output
    echo   run_tests.bat coverage      # Run with coverage report
) else (
    echo Error: Unknown test type: !TEST_TYPE!
    echo Run 'run_tests.bat help' for available options
    exit /b 1
)

echo.
echo ======================================
echo Tests completed!
echo ======================================
