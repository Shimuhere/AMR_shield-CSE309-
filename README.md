# AMR-Shield Surveillance Platform
### National Clinical Intelligence Network

AMR-Shield is a comprehensive clinical surveillance system designed to monitor antibiotic dispensing patterns and identify regional resistance risks in real-time.

---

## 🚀 Quick Deployment Guide

### 1. Environment Preparation
```bash
# Initialize virtual environment
python3 -m venv venv
source venv/bin/activate

# Install clinical dependencies
pip install -r requirements.txt
```

### 2. Network Initialization
Run the unified setup script to purge existing data and establish the national surveillance catalog and regional nodes.
```bash
python setup.py
```

### 3. Launch Surveillance Server
```bash
python manage.py runserver
```

---

## 🏛️ Clinical Access Points

### Health Ministry Console (Government)
- **Role:** Nationwide oversight, policy management, and clinical reporting.
- **Credentials:** `gov_admin` / `admin123`
- **URL:** `/dashboard/`

### Pharmacy Terminal (Clinical Nodes)
- **Role:** Dispensing logs and patient metadata synchronization.
- **Credentials:** `pharmacy_1` / `pharm123`
- **URL:** `/pharmacy/`

### Patient Health Portal (Individual)
- **Role:** Personal medication history and regional health alerts.
- **Credentials:** `john_doe` / `user123`
- **URL:** `/user/`

---

## 📂 Project Architecture
The platform is built on a **Modular Django Package System** for clinical-grade reliability:

- `core/models/`: Modularized data schemas (Accounts, Clinical, Settings).
- `core/views/`: Functional view controllers (Dashboards, Management, API).
- `core/utils/`: Specialized intelligence logic (Risk Analysis, Reporting).
- `scripts/`: System initialization and data population.

---
© 2026 Clinical Intelligence Surveillance Division.
