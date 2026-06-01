import sqlite3, os

db = r'C:\Users\MOULNA\Postman\files\SupermarchéMAUI\src\Supermarché.App\bin\Release\net9.0-windows10.0.19041.0\win-x64\publish\supermarché.db'
print(f"DB exists: {os.path.exists(db)}")
print(f"DB size: {os.path.getsize(db)}")

conn = sqlite3.connect(db)
all_tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print(f"Total tables (including system): {len(all_tables)}")
for t in all_tables:
    print(f"  {t[0]}")
conn.close()
