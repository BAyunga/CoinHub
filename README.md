# CoinHub

Instant coin recharge for in-app coins, paid through M-Pesa (Safaricom Daraja STK Push).

> **More information is in the [`docs/`](docs/README.md) folder:** setup, configuration, the admin guide, pricing and coins, the API, payments, deployment and troubleshooting.

Customers choose an app, enter their App User ID, M-Pesa number and number of coins. CoinHub prices the order on the server, sends an STK Push to the customer's phone and tracks the payment until Safaricom confirms it. Staff then load the coins and mark the order as loaded in the admin panel. No customer registration is needed.

**Stack:** Django 5 · Django REST Framework · PostgreSQL · Gunicorn · Nginx · vanilla JavaScript frontend · Docker or Podman Compose

## Quick start

```bash
git clone https://github.com/Gilks97/CoinHub.git
cd CoinHub
cp .env.example .env      # then edit it, see docs/getting-started.md
docker compose up -d --build
```

| URL | What |
|---|---|
| http://localhost:8080/ | Customer website |
| http://localhost:8080/admin/ | Admin panel (sign in with the `DJANGO_SUPERUSER_*` values from `.env`) |
| http://localhost:8080/api/coins/ | Coins API |

The `.env` file needs a few values to match (especially `DATABASE_URL`). [Getting started](docs/getting-started.md) lists them, and also covers running without containers.

## Documentation

| I want to... | Read |
|---|---|
| Run it locally or deploy it | [Getting started](docs/getting-started.md) · [Deployment](docs/deployment.md) |
| Set environment variables | [Configuration](docs/configuration.md) |
| Operate the admin panel | [Admin panel](docs/admin-panel.md) |
| Change prices, minimums or coins | [Coin catalog](docs/coin-catalog.md) |
| Understand payments and Daraja | [Payments and Daraja](docs/payments-daraja.md) |
| Call the API | [API reference](docs/api-reference.md) |
| Fix a problem | [Troubleshooting](docs/troubleshooting.md) |
| Run the tests or contribute | [Testing](docs/testing.md) · [Contributing](docs/contributing.md) |

## Project status

CoinHub handles real payments. Read [Security](docs/security.md), especially the hardening roadmap, before relying on it in production.

## Support

Contact the project maintainer for technical problems. Report bugs as GitHub issues, but never post secrets, phone numbers, M-Pesa receipts or customer data in a public issue.

## License

© 2026 CoinHub