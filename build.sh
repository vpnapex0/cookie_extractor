#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Installing Python dependencies ---"
pip install -r requirements.txt

echo "--- Installing Playwright browsers (Chromium) ---"
# --with-deps ensures all necessary system dependencies for Chromium are installed.
playwright install chromium --with-deps

echo "--- Build complete ---"