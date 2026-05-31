#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=== Weather Incident Monitoring Agent Startup ==="

# Ensure directories exist
mkdir -p data logs

# Start Ingestion Pipeline Loop in the background
echo "Starting ingestion pipeline loop in the background..."
python app.py --loop > logs/pipeline.log 2>&1 &
PIPELINE_PID=$!
echo "Ingestion pipeline started with PID: $PIPELINE_PID"

# Start Telegram Bot polling in the background
echo "Starting Telegram Bot polling in the background..."
python telegram_bot.py > logs/telegram_bot.log 2>&1 &
BOT_PID=$!
echo "Telegram Bot started with PID: $BOT_PID"

# Function to clean up background processes on exit
cleanup() {
    echo "Shutting down background services..."
    kill $PIPELINE_PID $BOT_PID 2>/dev/null || true
}
trap cleanup EXIT

# Start Streamlit Dashboard in the foreground
PORT=${PORT:-8501}
echo "Starting Streamlit dashboard on port $PORT..."
exec streamlit run dashboard.py --server.port "$PORT" --server.address 0.0.0.0
