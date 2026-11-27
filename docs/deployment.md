# Deployment

CoinHub currently runs on **Render** as **one web service** plus a hosted PostgreSQL database. The same Django service serves the website, the API and the admin panel:

| Piece | Where | Notes |
|---|---|---|
| Website, API and admin | One Render web service, built from the `Dockerfile` | Custom domain `https://coinhub.co.ke` (and `www`) |
| Database | Hosted PostgreSQL (for example Neon) | Connected with `DATABASE_URL` and SSL |

Confirm the exact service settings (branch, build, publish directory) in your Render dashboard. They are not stored in this repository.

## Backend service

The container starts `docker/entrypoint.sh`, which:

1. checks the database connection,
2. runs migrations,
3. collects static files,
4. attempts to create the superuser,
5. starts Gunicorn on `$PORT` (3 workers, 120 s timeout).

### Environment variables (production)

Set these in the Render dashboard, never in the repository:

| Variable | Production value |
|---|---|
| `SECRET_KEY` | New long random value |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | The site host names, for example `coinhub.co.ke,www.coinhub.co.ke` |
| `CSRF_TRUSTED_ORIGINS` | The site URLs with `https://`, for example `https://coinhub.co.ke,https://www.coinhub.co.ke`. The name is **plural**; a variable called `CSRF_TRUSTED_ORIGIN` is ignored |
| `CORS_ALLOWED_ORIGINS` | Not needed while one service serves everything (same origin) |
| `DATABASE_URL` | The hosted database URL (SSL on) |
| `DARAJA_ENV` | `production` |
| `DARAJA_CONSUMER_KEY`, `DARAJA_CONSUMER_SECRET` | Production Daraja app credentials |
| `DARAJA_SHORTCODE`, `DARAJA_TILL_NUMBER`, `DARAJA_PASSKEY` | Production values for your till |
| `DARAJA_CALLBACK_URL` | `https://<site-host>/api/payments/daraja/callback/` |
| `DJANGO_SUPERUSER_*` | Real admin account with a strong, unique password |
| `THROTTLE_ANON`, `THROTTLE_USER` | Rates suited to real traffic |

With `DEBUG=False`, Django redirects HTTP to HTTPS and marks cookies secure. See [Configuration](configuration.md) for every variable.

## Website (served by Django)

The website is not a separate service. The `Dockerfile` copies the `frontend/` folder into the image (`/app/frontend`), and `backend/config/settings.py` tells WhiteNoise to serve it at the site root:

```python
WHITENOISE_ROOT = <frontend folder>    # /app/frontend in the image, ../frontend when run from the repo
WHITENOISE_INDEX_FILE = True           # "/" serves index.html
```

| Path | Served by |
|---|---|
| `/`, `/recharge.html`, `/js/...`, `/css/...`, `/icons/...` | WhiteNoise (files from `frontend/`) |
| `/api/...` | Django REST API |
| `/admin/` | Django admin |
| `/static/...` | WhiteNoise (collected admin assets) |

`frontend/js/config.js` uses `API_BASE: '/api'`, because the website and the API share one origin. No CORS setup is needed.

Everything in `frontend/` is public. Never put secrets there.

WhiteNoise lets browsers cache these files for 60 seconds. After a change that must reach everyone immediately, bump the version in the script tags (for example `js/recharge.js?v=5`).

## Custom domain

1. In Render, open the web service, **Settings**, **Custom Domains**, and add `coinhub.co.ke` and `www.coinhub.co.ke`.
2. Create the DNS records Render shows, and wait until both are **Verified** with a certificate issued.
3. Update `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` and `DARAJA_CALLBACK_URL` (see the table above) and redeploy.
4. Check `https://coinhub.co.ke/` (website), `/api/coins/` (JSON) and `/admin/`.

## Deploying a change

1. Merge to the branch Render watches (normally `main`).
2. Render rebuilds and redeploys. Migrations run automatically on backend start.
3. Check the backend logs for `Running migrations` and no errors.
4. Smoke test: `/` shows the home page, `/api/coins/` returns the expected coins, the recharge page loads, the admin loads.

The website and the API ship in the same image, so a change that touches both goes live together.

## Going live checklist

- [ ] `DEBUG=False`, new `SECRET_KEY`, correct `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- [ ] `/` loads the website and `/api/coins/` returns JSON on the live domain
- [ ] Production Daraja credentials, till and passkey, with `DARAJA_ENV=production`
- [ ] Callback URL is public HTTPS and points to the production backend
- [ ] A successful small real payment, end to end, with the order reaching `paid`
- [ ] Superuser password is strong and not the example value
- [ ] Database backups enabled and a restore tested
- [ ] Rate limits reviewed ([Configuration](configuration.md))
- [ ] Items on the [Security](security.md) roadmap marked critical are done
- [ ] Coin prices checked in the admin
- [ ] `docs/user-guide/CoinHub-User-Guide.pdf` filled in with technician contact details

## Free-tier behaviour (Render)

Free web services sleep after a period of inactivity, so the first request can be slow. A payment callback arriving while the service is asleep may be delayed, and a sleeping backend can cause a timeout on the customer's screen. For real traffic use an always-on plan.

## Uploaded media

Files uploaded through the admin are stored on the container's disk and are lost on redeploy unless a persistent disk is attached. Keep coin icons in `frontend/icons/` instead.

## Rolling back

Redeploy the previous commit from Render. Migrations are not automatically reversed, so avoid destructive migrations, and take a database backup before risky changes.

## Switching to a new database

1. Create the new database and set the new `DATABASE_URL`.
2. Deploy. All migrations run from `0001`, creating the schema and the coin catalog.
3. The superuser step creates the first admin from `DJANGO_SUPERUSER_*`.
4. Recreate staff users and groups, and review coin prices in the admin.

Orders and payments from the old database are not copied automatically.
