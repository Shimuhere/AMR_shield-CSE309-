import os
import random
import sys

import django

# `setup.py` is a symlink to this file, so neither sys.path[0] nor __file__
# reliably points at the project root. Resolve through the link to find it.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Initialize Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amr_shield_project.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

# Modular Imports
from core.models import User, Antibiotic, PharmacyProfile, SaleRecord, Prescription, SystemSettings


def guard_against_remote_database():
    """This script deletes every record, so refuse to point it at a real deployment.

    The project reads DATABASE_URL, so a shell with the deployment environment
    loaded would otherwise seed straight over production data.
    """
    if connection.vendor == 'sqlite' or os.environ.get('AMR_ALLOW_DESTRUCTIVE_SEED') == '1':
        return
    sys.exit(
        f"Refusing to run: this deletes all data, and the configured database is "
        f"{connection.vendor}, not a local SQLite file.\n"
        "Unset DATABASE_URL to seed your local database, or set "
        "AMR_ALLOW_DESTRUCTIVE_SEED=1 if you really intend to wipe this one."
    )


def run():
    print("--- AMR-Shield National Surveillance System Initialization ---")
    guard_against_remote_database()

    print("[0/6] Applying database migrations...")
    call_command('migrate', verbosity=0)

    # 1. Clear existing data
    print("[1/6] Purging clinical records...")
    SaleRecord.objects.all().delete()
    Prescription.objects.all().delete()
    PharmacyProfile.objects.all().delete()
    Antibiotic.objects.all().delete()
    SystemSettings.objects.all().delete()
    User.objects.exclude(is_superuser=True).delete()

    # 2. Initialize System Settings
    print("[2/6] Calibrating risk thresholds...")
    SystemSettings.objects.create(
        low_risk_limit=15,
        moderate_risk_limit=30,
        high_risk_limit=100
    )

    # 3. Create Antibiotics
    print("[3/6] Seeding clinical medication catalog...")
    antibiotics_data = [
        ("Azithromycin", "Macrolides", "B"),
        ("Amoxicillin", "Penicillins", "A"),
        ("Ciprofloxacin", "Quinolones", "C"),
        ("Cefixime", "Cephalosporins", "B"),
        ("Doxycycline", "Tetracyclines", "A"),
        ("Metronidazole", "Nitroimidazoles", "A"),
    ]
    antibiotics = []
    for name, group, cat in antibiotics_data:
        a, _ = Antibiotic.objects.get_or_create(name=name, group=group, category=cat)
        antibiotics.append(a)

    # 4. Create Stakeholder Accounts
    print("[4/6] Creating verified clinical accounts...")
    # Government Oversight
    gov, _ = User.objects.get_or_create(username="gov_admin", role="GOVERNMENT")
    gov.set_password("admin123")
    gov.save()

    # Bangladesh Regional Nodes
    pharmacy_locations = [
        ("Dhaka Central Pharma", "Dhanmondi, Dhaka", 23.7461, 90.3742),
        ("Gulshan Meds", "Gulshan 2, Dhaka", 23.7925, 90.4078),
        ("Chittagong Health Care", "GEC Circle, Chittagong", 22.3591, 91.8213),
        ("Sylhet Drug House", "Zindabazar, Sylhet", 24.8917, 91.8697),
        ("Rajshahi Medicine Mart", "Shaheb Bazar, Rajshahi", 24.3636, 88.6241),
    ]

    pharmacies = []
    for i, (name, addr, lat, lng) in enumerate(pharmacy_locations):
        username = f"pharmacy_{i+1}"
        user, _ = User.objects.get_or_create(username=username, role="PHARMACY", latitude=lat, longitude=lng)
        user.set_password("pharm123")
        user.save()
        profile = PharmacyProfile.objects.create(user=user, name=name, address=addr, latitude=lat, longitude=lng)
        pharmacies.append(profile)

    # Patient Portal Test
    patient, _ = User.objects.get_or_create(username="john_doe", role="INDIVIDUAL", latitude=23.7461, longitude=90.3742)
    patient.set_password("user123")
    patient.save()

    # 5. Generate Clinical Transactions
    print("[5/6] Generating simulated surveillance data...")
    # Targeted High Usage in Dhaka
    SaleRecord.objects.create(
        pharmacy=pharmacies[0], antibiotic=antibiotics[0], quantity=120,
        patient_age=45, patient_gender='M', doctor_name="Dr. Ahmed", prescription_reference="RX-DH-101"
    )

    # Patient history
    Prescription.objects.create(user=patient, antibiotic=antibiotics[0], dosage=500, frequency=2, duration_days=7)
    Prescription.objects.create(user=patient, antibiotic=antibiotics[2], dosage=250, frequency=1, duration_days=5)

    # Distributed random data
    for p in pharmacies[1:]:
        for a in random.sample(antibiotics, 2):
            SaleRecord.objects.create(
                pharmacy=p, antibiotic=a, quantity=random.randint(5, 45),
                patient_age=random.randint(18, 75), patient_gender=random.choice(['M', 'F']),
                doctor_name="Dr. Local Clinical", prescription_reference=f"RX-{random.randint(1000, 9999)}"
            )

    print("[6/6] Finalizing network synchronization...")
    print("\n✅ AMR-Shield System Ready!")
    print("------------------------------------")
    print("Health Official:  gov_admin / admin123")
    print("Pharmacy Node:    pharmacy_1 / pharm123")
    print("Patient Account:  john_doe / user123")
    print("------------------------------------")

if __name__ == "__main__":
    run()
