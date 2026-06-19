#!/bin/bash

# Elgg Locust Load Test Helper Script
# Usage: ./run_locust.sh [mode] [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
MODE="${1:-ui}"
HOST="${LOCUST_HOST:-http://localhost:8080}"
USERS="${USERS:-50}"
SPAWN_RATE="${SPAWN_RATE:-5}"
RUN_TIME="${RUN_TIME:-5m}"

print_usage() {
    cat << EOF
Elgg Locust Load Test Runner

Usage: ./run_locust.sh [MODE] [OPTIONS]

Modes:
  ui              - Run with web UI (default)
  headless        - Run in headless mode
  master          - Run as master node
  worker          - Run as worker node
  docker          - Run using docker-compose
  docker-headless - Run docker in headless mode

Options:
  --host HOST         Target server (default: $HOST)
  --users NUM         Number of users (default: $USERS)
  --spawn-rate NUM    Users spawned per second (default: $SPAWN_RATE)
  --run-time TIME     Test duration (default: $RUN_TIME)
  --help              Show this help message

Examples:
  # Run with 100 users via web UI
  ./run_locust.sh ui --users 100

  # Run headless for 10 minutes with 50 users
  ./run_locust.sh headless --users 50 --run-time 10m

  # Run distributed with master/worker nodes
  ./run_locust.sh master  # Terminal 1
  ./run_locust.sh worker  # Terminal 2

  # Run with docker-compose
  ./run_locust.sh docker

EOF
}

# Parse options
while [[ $# -gt 1 ]]; do
    case "$2" in
        --host)
            HOST="$3"
            shift 2
            ;;
        --users)
            USERS="$3"
            shift 2
            ;;
        --spawn-rate)
            SPAWN_RATE="$3"
            shift 2
            ;;
        --run-time)
            RUN_TIME="$3"
            shift 2
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $2"
            print_usage
            exit 1
            ;;
    esac
done

echo "================================================"
echo "Elgg Locust Load Test"
echo "================================================"
echo "Mode: $MODE"
echo "Target: $HOST"
echo "Users: $USERS"
echo "Spawn Rate: $SPAWN_RATE/second"
echo "Run Time: $RUN_TIME"
echo "================================================"
echo

case "$MODE" in
    ui)
        echo "Starting Locust with Web UI..."
        echo "Open http://localhost:8089 in your browser"
        locust -f locustfile.py --host "$HOST"
        ;;
    
    headless)
        echo "Starting Locust in headless mode..."
        locust -f locustfile.py \
            --host "$HOST" \
            --users "$USERS" \
            --spawn-rate "$SPAWN_RATE" \
            --run-time "$RUN_TIME" \
            --headless
        ;;
    
    master)
        echo "Starting Locust Master..."
        echo "Workers should connect to: localhost:5557"
        locust -f locustfile.py \
            --host "$HOST" \
            --master \
            --master-bind-host 0.0.0.0 \
            --master-bind-port 5557
        ;;
    
    worker)
        echo "Starting Locust Worker..."
        echo "Make sure master is running on: localhost:5557"
        read -p "Master host [localhost]: " MASTER_HOST
        MASTER_HOST=${MASTER_HOST:-localhost}
        locust -f locustfile.py \
            --host "$HOST" \
            --worker \
            --master-host "$MASTER_HOST" \
            --master-port 5557
        ;;
    
    docker)
        echo "Starting Locust with docker-compose..."
        docker-compose up
        ;;
    
    docker-headless)
        echo "Starting Locust with docker-compose in headless mode..."
        docker-compose run --rm locust-master \
            locust -f locustfile.py \
            --host "$HOST" \
            --users "$USERS" \
            --spawn-rate "$SPAWN_RATE" \
            --run-time "$RUN_TIME" \
            --headless
        ;;
    
    *)
        echo "Unknown mode: $MODE"
        print_usage
        exit 1
        ;;
esac
