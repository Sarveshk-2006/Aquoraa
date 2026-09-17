#!/usr/bin/env bash
set -e

echo "=== Aquora Local Development Setup ==="

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "Installing backend dependencies..."
cd backend
python -m venv .venv || true
source .venv/bin/activate || .venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "=== Setup Complete! ==="
