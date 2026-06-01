"""Check new DB schema and run migration."""
import sqlite3, os

publish = r'C:\Users\MOULNA\Postman\files\SupermarchéMAUI\src\Supermarché.App\bin\Release\net9.0-windows10.0.19041.0\win-x64\publish'
new_db = os.path.join(publish, 'supermarché.db')

new = sqlite3.connect(new_db)
tables = new.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '__%' ORDER BY name").fetchall()
print("Tables in new DB:")
for t in tables:
    cols = new.execute(f'PRAGMA table_info("{t[0]}")').fetchall()
    print(f"  {t[0]}: {len(cols)} cols - {', '.join(c[1] for c in cols)}")
new.close()
