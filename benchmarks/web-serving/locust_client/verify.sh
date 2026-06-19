#!/bin/bash

# Verification script for Locust Elgg Load Generator
# This script checks that all components are properly installed and configured

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TOTAL_CHECKS=0
PASSED_CHECKS=0

check_file() {
    local file=$1
    local description=$2
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $description - File not found: $file"
        return 1
    fi
}

check_executable() {
    local cmd=$1
    local description=$2
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $description"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $description - Command not found: $cmd"
        return 1
    fi
}

check_python_module() {
    local module=$1
    local description=$2
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if python3 -c "import $module" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $description"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $description - Module not installed: $module"
        echo "  Run: pip install -r requirements.txt"
        return 1
    fi
}

echo "================================================"
echo "Locust Elgg Benchmark Verification"
echo "================================================"
echo

echo "1. Checking required files..."
check_file "locustfile.py" "Main Locust script"
check_file "Dockerfile" "Docker configuration"
check_file "docker-compose.yml" "Docker Compose configuration"
check_file "requirements.txt" "Python dependencies"
check_file "users.list" "User credentials file"
check_file "locust.conf" "Locust configuration"
check_file "run_locust.sh" "Helper script"
echo

echo "2. Checking documentation..."
check_file "README.md" "Main README"
check_file "QUICKSTART.md" "Quick start guide"
check_file "ADVANCED_CONFIG.md" "Advanced configuration"
check_file "IMPLEMENTATION_SUMMARY.md" "Implementation summary"
echo

echo "3. Checking system dependencies..."
check_executable "python3" "Python 3"
check_executable "docker" "Docker" || echo "  (Optional, for containerized deployment)"
check_executable "docker-compose" "Docker Compose" || echo "  (Optional, for multi-container setup)"
echo

echo "4. Checking Python modules..."
check_python_module "locust" "Locust framework"
check_python_module "requests" "Requests library"
check_python_module "gevent" "Gevent"
echo

echo "5. Checking script permissions..."
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if [ -x "run_locust.sh" ]; then
    echo -e "${GREEN}✓${NC} run_locust.sh is executable"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${YELLOW}⚠${NC} run_locust.sh is not executable"
    echo "  Run: chmod +x run_locust.sh"
fi
echo

echo "6. Checking configuration syntax..."
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if python3 -m py_compile locustfile.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} locustfile.py syntax is valid"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}✗${NC} locustfile.py has syntax errors"
fi
echo

echo "7. Checking users.list format..."
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if grep -E "^[^:]+:[^:]+:[0-9]+$" users.list &>/dev/null; then
    echo -e "${GREEN}✓${NC} users.list has valid format"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    USER_COUNT=$(wc -l < users.list)
    echo "  Found $USER_COUNT users"
else
    echo -e "${RED}✗${NC} users.list format invalid"
    echo "  Expected format: username:password:guid"
fi
echo

echo "================================================"
echo "Verification Results: $PASSED_CHECKS/$TOTAL_CHECKS passed"
echo "================================================"
echo

if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to run load tests.${NC}"
    echo
    echo "Quick start:"
    echo "  1. Run with web UI:"
    echo "     ./run_locust.sh ui --host http://your-elgg-server:8080"
    echo
    echo "  2. Run headless:"
    echo "     ./run_locust.sh headless --users 100"
    echo
    echo "  3. Run with Docker:"
    echo "     docker build -t elgg-locust ."
    echo "     docker run -p 8089:8089 elgg-locust"
    exit 0
else
    FAILED=$((TOTAL_CHECKS - PASSED_CHECKS))
    echo -e "${YELLOW}⚠ $FAILED check(s) need attention${NC}"
    echo
    echo "Next steps:"
    if ! command -v python3 &> /dev/null; then
        echo "  1. Install Python 3"
    fi
    if ! python3 -c "import locust" 2>/dev/null; then
        echo "  2. Install dependencies: pip install -r requirements.txt"
    fi
    if [ ! -x "run_locust.sh" ]; then
        echo "  3. Make script executable: chmod +x run_locust.sh"
    fi
    echo "  4. For Docker: Install Docker and Docker Compose"
    exit 1
fi
