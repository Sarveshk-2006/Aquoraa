#!/usr/bin/env bash
set -e

echo "=== Initializing Aquora Database and Running Alembic Migrations ==="

cd backend
alembic upgrade head
echo "=== Database Migrations Applied Successfully ==="
