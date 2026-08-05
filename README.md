# Mrentals

A trust-first long-term rental marketplace for Kenya, built as a single Django
application. The MVP exists to answer one question honestly: *is this house
real, and is this person real?*

## What the MVP does

| Feature | Why it exists |
| --- | --- |
| **Manual ID verification** for landlords and tenants | A human on our team looks at every ID and ownership document in the Django admin. Nothing about a listing is trustworthy if the person behind it is not. |
| **Mandatory structured photo sets** | Every published listing must carry a photo of the building exterior, gate/entrance, room interior, water/electricity meter and the nearest landmark. No complete set, no publication. |
| **Landmark-first location** | Kenyan renters navigate by "200m past Quickmart Ruaka, blue gate", not by a map pin. Directions and walking time from a named landmark are required fields; GPS is optional. |
| **Publication gating** | A listing can only go live when the landlord is verified *and* the photo set is complete. Both rules are enforced in the model, not just the UI. |
| **Tenancy-gated two-way reviews** | The landlord records who actually rented the unit. That single act unlocks the tenant to review the landlord and the landlord to review the tenant. Nobody else can review either side. |
| **Search and filter** | Free text across landmarks and descriptions, plus county, price range, bedrooms, property type, verified-landlord-only and sorting. HTMX swaps just the results grid. |

Deliberately **out of scope** for this MVP: in-app messaging, M-Pesa escrow,
and a low-data mode.

## Stack

Server-rendered Django 5.2 with HTMX for partial updates and Tailwind CSS for
styling. No REST API and no separate JavaScript frontend. Every page is a
Django template. HTMX is vendored locally rather than loaded from a CDN.

```
config/          settings, URLs, test runner
apps/accounts/   custom user with dual email/phone identity
apps/listings/   listings, structured photos, search, saved listings
apps/verification/  manual landlord & tenant ID review workflow
apps/reviews/    tenancies and the two-way reviews they unlock
apps/pages/      home, dashboard, how-it-works
templates/       all server-rendered templates
assets/, static/ Tailwind source and built assets
```

## Getting started

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
npm install                     # Tailwind + vendors htmx into static/js/

cp .env.example .env            # then edit DJANGO_SECRET_KEY

.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo
npm run build:css
.venv/bin/python manage.py runserver
```

Open <http://127.0.0.1:8000>.

### Demo accounts

`seed_demo` creates four landlords, four tenants, six listings with full photo
sets, recorded tenancies and reviews on both sides.

| Account | Email | Password |
| --- | --- | --- |
| Verified landlord | `achieng@example.com` | `mrentals2024` |
| Unverified landlord (listing stays a draft) | `brian@example.com` | `mrentals2024` |
| Verified tenant | `wanjiru@example.com` | `mrentals2024` |
| Admin / verification desk | `admin@mrentals.co.ke` | `admin12345` |

Every demo account can also sign in with its phone number in local format, e.g.
`0712000001`.

Re-run with `--flush` to rebuild demo data from scratch:

```bash
.venv/bin/python manage.py seed_demo --flush
```

## The verification desk

Verification is intentionally manual. Sign in at `/admin/` as the admin account
and open **Landlord verifications** or **Tenant verifications**. Each row shows
a preview of the submitted ID and documents, and the list actions **Approve
selected** / **Reject selected** flip the applicant's verified status. A
rejected applicant sees the reviewer's note and can resubmit.

## Development

```bash
npm run watch:css                          # rebuild Tailwind on change
.venv/bin/python manage.py test            # 56 tests
.venv/bin/python manage.py test apps.reviews   # one app
```

Tailwind only emits classes it finds in the templates, so re-run
`npm run build:css` after adding new utility classes.

Tests run against a temporary `MEDIA_ROOT` (see `config/test_runner.py`) so
image uploads in fixtures never touch your local `media/` folder.

## Configuration

All settings read from the environment, with development-friendly defaults:

| Variable | Default | Notes |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | insecure dev key | Must be set in production. |
| `DJANGO_DEBUG` | `True` | Set to `False` in production. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma separated. |
| `DATABASE_URL` | bundled SQLite | Set to a Postgres URL for production. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | Comma separated, needed for custom domains. |
| `DJANGO_MEDIA_ROOT` | `media/` | Point at a persistent volume in production. |
| `DJANGO_SERVE_MEDIA_FILES` | `True` | Set to `False` once uploads move to object storage. |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` when `DEBUG=False` | Only disable behind a proxy that already forces HTTPS. |

The domain rules live at the bottom of `config/settings.py`.
`LISTING_REQUIRED_PHOTO_CATEGORIES` is the list a listing must satisfy before it
can be published.

With `DEBUG=False`, static files are served by WhiteNoise with hashed
filenames, so run `manage.py collectstatic` as part of deployment.

## Deploying to Render

`render.yaml` is a Render Blueprint that provisions the web service, and
`build.sh` is the build step. Both assume the committed Tailwind CSS and htmx
bundle, so the build stays pure Python and needs no Node toolchain.

1. In Render, create a new Blueprint pointed at this repository.
2. Set `DATABASE_URL` to the Postgres instance's **internal** connection string.
3. Deploy. The build installs dependencies, runs `collectstatic`, then `migrate`.

`RENDER_EXTERNAL_HOSTNAME` is injected by Render and is added to
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` automatically, so the default
`onrender.com` URL works without extra configuration.

### Uploads need a disk

Render replaces the container filesystem on every deploy. Listing photos and ID
documents are user uploads, so the blueprint mounts a persistent disk at
`/var/data/media` and sets `DJANGO_MEDIA_ROOT` to match. Disks require a paid
instance type. On a free instance every uploaded image is lost on the next
deploy or restart, which breaks listings, because photos are mandatory for
publication. The longer term fix is object storage such as S3, at which point
`DJANGO_SERVE_MEDIA_FILES` can be set to `False`.

To load the demo data on Render, open a shell on the service and run
`python manage.py seed_demo`.

## Brand

Logo variants live in `static/img/` (lockup, icon, reversed, mono, favicon) and
are generated from `static/img/logo-primary.png` by `scripts/trace_logo.py` and
`scripts/emit_logo.py`. Brand colours are exposed to Tailwind as `brand`
(accent `#1B9D80`) and `ink` (`#000000`) in `tailwind.config.js`.
