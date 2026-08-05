#!/usr/bin/env bash
# Render build step. Tailwind CSS and htmx are committed as built assets, so the
# build stays pure Python and no Node toolchain is required here.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Free Render instances have an ephemeral filesystem, so uploaded images are
# gone after every deploy. Reseeding restores the demo listings and their
# photos, which listings cannot be published without.
if [ "${SEED_DEMO_ON_DEPLOY:-false}" = "true" ]; then
  python manage.py seed_demo --flush
fi
