#!/bin/bash
# run_tests.sh - Convenient test runner script for Vecinita

set -e

echo "======================================"
echo "Vecinita Test Suite Runner"
echo "======================================"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Install with: pip install pytest"
    exit 1
fi

# Parse command line arguments
TEST_TYPE="${1:-unit}"
VERBOSE="${2:--v}"

case $TEST_TYPE in
    "unit")
        echo "🧪 Running unit tests..."
        pytest tests/ -m unit $VERBOSE
        ;;
    "integration")
        echo "🔗 Running integration tests..."
        pytest tests/ -m integration $VERBOSE
        ;;
    "ui")
        echo "🎨 Running UI tests..."
        echo "⚠️  Make sure the server is running: uv run uvicorn main:app --host localhost --port 8000"
        # Note: --run-skipped is not a valid pytest flag; use markers only
        pytest tests/test_ui.py -m ui $VERBOSE
        ;;
    "db")
        echo "🗄️  Running database tests..."
        pytest tests/ -m db $VERBOSE
        ;;
    "api")
        echo "🔌 Running API tests..."
        pytest tests/ -m api $VERBOSE
        ;;
    "all")
        echo "🚀 Running all tests..."
        pytest tests/ $VERBOSE
        ;;
    "coverage")
        echo "📊 Running tests with coverage report..."
        if ! command -v coverage &> /dev/null; then
            echo "❌ coverage not found. Install with: pip install coverage pytest-cov"
            exit 1
        fi
        pytest tests/ --cov=. --cov-report=html --cov-report=term-missing $VERBOSE
        echo "✅ Coverage report generated in htmlcov/index.html"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: ./run_tests.sh [test_type] [verbose_level]"
        echo ""
        echo "test_type options:"
        echo "  unit        - Run unit tests only (default)"
        echo "  integration - Run integration tests"
        echo "  ui          - Run UI tests with Playwright"
        echo "  db          - Run database tests"
        echo "  api         - Run API endpoint tests"
        echo "  all         - Run all tests"
        echo "  coverage    - Run tests with coverage report"
        echo "  help        - Show this help message"
        echo ""
        echo "verbose_level options:"
        echo "  -v          - Verbose output (default)"
        echo "  -q          - Quiet output"
        echo "  -vv         - Very verbose output"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh unit          # Run unit tests"
        echo "  ./run_tests.sh all -vv       # Run all tests with very verbose output"
        echo "  ./run_tests.sh coverage      # Run with coverage report"
        ;;
    *)
        echo "❌ Unknown test type: $TEST_TYPE"
        echo "Run './run_tests.sh help' for available options"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "✅ Tests completed!"
echo "======================================"
