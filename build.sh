#!/usr/bin/env bash
# Build script for Render deployment
set -o errexit

pip install -r requirements.txt

# Create required directories
mkdir -p logs
mkdir -p index_data

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py index_docs
