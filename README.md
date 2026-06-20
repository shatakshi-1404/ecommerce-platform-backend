# Vendora — Backend

> Django REST API powering a full-stack multi-vendor e-commerce marketplace.

**Live Demo:** [https://ecommerce-platform-frontend-37ed.vercel.app](https://ecommerce-platform-frontend-37ed.vercel.app)
**Frontend Repo:** [github.com/shatakshi-1404/ecommerce-platform-frontend](https://github.com/shatakshi-1404/ecommerce-platform-frontend)

---

## What it does

Vendora is a multi-vendor marketplace (think mini Amazon) where buyers browse and purchase products, sellers manage their inventory and orders, and an admin controls the whole platform. This repo is the Django REST backend — it handles all business logic, authentication, payments, async tasks, and scheduled jobs.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 5.1 + Django REST Framework 3.15 |
| Auth | Token-based authentication (DRF) |
| Payments | Razorpay (server-side order creation + HMAC-SHA256 signature verification) |
| Async Tasks | Celery 5.4 + Redis |
| Scheduled Jobs | Celery Beat |
| Database | PostgreSQL (production) / SQLite (local dev) |
| Static Files | WhiteNoise |
| Production Server | Gunicorn |
| Hosting | Render |

---

## Project Structure

```
ecommerce-platform-backend/
├── core/              # Django project settings, URLs, Celery config
├── users/             # Registration, login, token auth, role management
├── products/          # Product CRUD, categories, image uploads, filtering
├── orders/            # Cart, checkout, Razorpay integration, order tracking
├── notifications/     # Async email tasks, low stock alerts, daily reports
├── manage.py
├── requirements.txt
├── Procfile           # Gunicorn + Celery worker start commands for Render
└── build.sh           # Render build script (migrations, collectstatic)
```

---

## Key Features

### Role-Based Access Control
Three user roles — `buyer`, `seller`, `admin` — with custom DRF permission classes (`IsBuyer`, `IsSeller`, `IsAdminUser`) enforced at the API level, not just the frontend.

### Cryptographic Payment Verification
Razorpay orders are created server-side. After payment, the backend verifies an HMAC-SHA256 signature before confirming any order. Tampered or fake payments are rejected automatically.

### Atomic Stock Deduction
Stock deduction on order placement is wrapped in `transaction.atomic()`. If anything fails mid-operation, the entire transaction rolls back — no orphaned stock reductions.

### Async Email System
Order confirmation, low stock alerts, and daily sales reports are all sent via Celery workers. The API responds instantly — email delivery never blocks a request.

### Inventory Alerts
Each product has a configurable `low_stock_threshold`. When stock drops below it after an order, a Celery task fires automatically and emails the seller.

### Scheduled Daily Reports
Celery Beat triggers a daily task every morning that emails each seller a summary of their previous day's sales.

---

## API Overview

15+ REST endpoints across 4 Django apps:

**Users** — register, login, logout, profile
**Products** — list, detail, create, update, delete, search/filter/sort by category and price
**Orders** — cart management, checkout, Razorpay order creation, payment verification, order history, status updates
**Notifications** — internal task triggers (not public-facing)

---

## Local Setup

**Prerequisites:** Python 3.12+, Redis running locally

```bash
git clone https://github.com/shatakshi-1404/ecommerce-platform-backend.git
cd ecommerce-platform-backend

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///db.sqlite3   # or your postgres URL
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

In a separate terminal, start Celery:

```bash
celery -A core worker --loglevel=info
celery -A core beat --loglevel=info   # for scheduled tasks
```

---

## Deployment (Render)

The `Procfile` defines two processes:

```
web: gunicorn core.wsgi:application
worker: celery -A core worker --beat --loglevel=info
```

`build.sh` runs on every deploy:

```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

Set all `.env` variables as Render environment variables. Redis is provisioned via Render's Redis service.

---

## Environment Variables Reference

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for dev, `False` for prod |
| `RAZORPAY_KEY_ID` | Razorpay API key |
| `RAZORPAY_KEY_SECRET` | Razorpay secret (used for signature verification) |
| `EMAIL_HOST_USER` | Gmail address for sending emails |
| `EMAIL_HOST_PASSWORD` | Gmail app password |
| `REDIS_URL` | Redis connection URL |
| `DATABASE_URL` | PostgreSQL or SQLite URL |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames |
| `CORS_ALLOWED_ORIGINS` | Frontend origin (e.g. Vercel URL) |
