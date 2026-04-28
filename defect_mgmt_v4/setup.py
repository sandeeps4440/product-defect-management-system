#!/usr/bin/env python
"""
Run once to set up the entire project:
    python setup.py
Then start the server:
    python manage.py runserver
"""
import os, sys, subprocess

def run(cmd, desc=""):
    if desc:
        print(f"\n  ▸ {desc}...")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ Failed: {cmd}")
        print("   Make sure Django is installed: pip install -r requirements.txt")
        sys.exit(1)

print("\n" + "="*52)
print("  DefectTrack Pro — First-Time Setup")
print("="*52)

# Remove stale DB so seed always works fresh
if os.path.exists("db.sqlite3"):
    os.remove("db.sqlite3")
    print("\n  Removed old database.")

run("python manage.py migrate --run-syncdb", "Running database migrations")
run("python manage.py seed_data", "Seeding demo users and data")

print("\n" + "="*52)
print("  ✅ Setup complete!")
print()
print("  Start the server:")
print("    python manage.py runserver")
print()
print("  Then open: http://127.0.0.1:8000/")
print("="*52 + "\n")
