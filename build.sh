#!/usr/bin/env bash
# Render build step. Tailwind CSS and htmx are committed as built assets, so the
# build stays pure Python and no Node toolchain is required here.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input
