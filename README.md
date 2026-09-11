# AMR-Shield Surveillance Platform
### National Clinical Intelligence Network

AMR-Shield is a comprehensive clinical surveillance system designed to monitor antibiotic dispensing patterns and identify regional resistance risks in real-time.

## 🌐 Live Deployment

**https://amr-shield.vercel.app**

Hosted on Vercel with a Neon Postgres database. The `main` branch deploys automatically on every push.

---

## 🚀 Quick Start (Local)

### 1. Environment Preparation
```bash
# Initialize virtual environment
python3 -m venv venv
source venv/bin/activate

# Install clinical dependencies
pip install -r requirements.txt
```

### 2. Network Initialization
Run the unified setup script to apply migrations, purge existing data, and establish the national surveillance catalog and regional nodes.
```bash
python setup.py
```

> ⚠️ This **deletes every record** before seeding. It refuses to run against a
> non-SQLite database, so it cannot wipe the deployment by accident.

### 3. Launch Surveillance Server
```bash
python manage.py runserver
```

The server runs with `DEBUG` on locally and off automatically when deployed.

### 4. Run the Test Suite
```bash
python manage.py test core
```

---

## 🏛️ Clinical Access Points

Seeded by `setup.py` for **local development only**.

| Console | Role | Credentials | URL |
| --- | --- | --- | --- |
| Health Ministry (Government) | Nationwide oversight, policy management, clinical reporting | `gov_admin` / `admin123` | `/dashboard/` |
| Pharmacy Terminal (Clinical Node) | Dispensing logs and patient metadata synchronization | `pharmacy_1` / `pharm123` | `/pharmacy/` |
| Patient Health Portal (Individual) | Personal medication history and regional health alerts | `john_doe` / `user123` | `/user/` |

> 🔐 These are public demo passwords. Do not reuse them for any account on the
> live deployment.

---

## 🔌 Sales Ingestion API

Pharmacy nodes can post dispensing records directly:

```
POST /api/sales/
{"antibiotic_name": "Amoxicillin", "quantity": 12}
```

Requires an authenticated pharmacy account with a registered profile; any other
caller receives `403`. The dispensing pharmacy is always taken from the
authenticated session, never from the request body.

---

## 📂 Project Architecture
The platform is built on a **Modular Django Package System** for clinical-grade reliability:

- `core/models/`: Modularized data schemas (Accounts, Clinical, Settings).
- `core/views/`: Functional view controllers (Dashboards, Management, API).
- `core/forms.py`: Validation layer for every operator-submitted record.
- `core/utils/`: Specialized intelligence logic (Risk Analysis, Reporting).
- `core/decorators.py`: Role-based access control for clinical consoles.
- `core/tests.py`: Regression coverage for access control, validation, and risk scoring.
- `scripts/`: System initialization and data population.
- `api/`: Serverless WSGI entry point used by the Vercel deployment.

---

## ⚙️ Deployment Configuration

The deployment reads its configuration from environment variables:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Postgres connection string; falls back to local SQLite when unset. |
| `SECRET_KEY` | Django signing key. |
| `DEBUG` | Defaults to off on Vercel, on locally. |
| `ALLOWED_HOSTS` | Comma-separated extra hostnames. |

Static assets are served through WhiteNoise. Regenerate them after changing any
stylesheet or script:

```bash
python manage.py collectstatic --noinput
```

---
© 2026 Clinical Intelligence Surveillance Division.
