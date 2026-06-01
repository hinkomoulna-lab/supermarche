"""Examine both database schemas for migration planning."""
import sqlite3
import os
import subprocess
import time

OLD_DB = r'C:\Users\MOULNA\Postman\files\db.sqlite3'
NEW_DB = r'C:\Users\MOULNA\Postman\files\SupermarchéMAUI\src\Supermarché.App\bin\Release\net9.0-windows10.0.19041.0\win-x64\publish\supermarché.db'

# Run the MAUI app briefly to create the database
publish_dir = r'C:\Users\MOULNA\Postman\files\SupermarchéMAUI\src\Supermarché.App\bin\Release\net9.0-windows10.0.19041.0\win-x64\publish'
exe_path = os.path.join(publish_dir, 'Supermarché.App.exe')

if not os.path.exists(NEW_DB):
    print("Starting MAUI app to create database...")
    proc = subprocess.Popen([exe_path], cwd=publish_dir)
    time.sleep(5)
    proc.kill()
    time.sleep(1)

if not os.path.exists(NEW_DB):
    print(f"ERROR: New DB still not found at {NEW_DB}")
    # Try debug path
    NEW_DB = r'C:\Users\MOULNA\Postman\files\SupermarchéMAUI\src\Supermarché.App\bin\Debug\net9.0-windows10.0.19041.0\win10-x64\supermarché.db'
    if not os.path.exists(NEW_DB):
        print("Trying debug path...")
        proc = subprocess.Popen([exe_path.replace('Release', 'Debug').replace('win-x64', 'win10-x64')], cwd=publish_dir.replace('Release', 'Debug').replace('win-x64', 'win10-x64'))
        time.sleep(5)
        proc.kill()
        time.sleep(1)
        if not os.path.exists(NEW_DB):
            print("Still not found. Migration script will be written generically.")
            NEW_DB = None

old = sqlite3.connect(OLD_DB)
old.row_factory = sqlite3.Row

print("\n=== OLD DATABASE TABLES ===")
old_tables = old.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
for t in old_tables:
    cols = old.execute(f"PRAGMA table_info(\"{t[0]}\")").fetchall()
    col_info = ", ".join(f"{c['name']} ({c['type']})" for c in cols)
    print(f"  {t[0]}: {col_info}")

if NEW_DB and os.path.exists(NEW_DB):
    new = sqlite3.connect(NEW_DB)
    new.row_factory = sqlite3.Row
    print("\n=== NEW DATABASE TABLES ===")
    new_tables = new.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    for t in new_tables:
        if t[0].startswith('__'):
            continue
        cols = new.execute(f"PRAGMA table_info(\"{t[0]}\")").fetchall()
        col_info = ", ".join(f"{c['name']} ({c['type']})" for c in cols)
        print(f"  {t[0]}: {col_info}")
    new.close()

old.close()
print("\nDone.")
