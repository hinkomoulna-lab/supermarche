import sqlite3
conn = sqlite3.connect('C:\\Users\\MOULNA\\Postman\\files\\db.sqlite3')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
for t in tables:
    print(t[0])
conn.close()
