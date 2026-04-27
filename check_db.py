import sqlite3
import os

db_path = r'c:\Users\86184\Desktop\双创\programming_education_system\programming_edu_sys\server\runtime\app.db'
print('DB exists:', os.path.exists(db_path))

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Tables:', [t[0] for t in tables])
    
    cursor.execute('SELECT username, access_expires_at FROM sessions ORDER BY access_expires_at DESC LIMIT 5')
    rows = cursor.fetchall()
    print('Recent sessions:')
    for row in rows:
        print(f'  {row[0]}: {row[1]}')
    
    conn.close()
