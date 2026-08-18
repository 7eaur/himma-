import bcrypt, psycopg2, os
from urllib.parse import urlparse

# Set password for researcher1
pwd = b'securepass123'
hashed = bcrypt.hashpw(pwd, bcrypt.gensalt()).decode()

p = urlparse(os.environ['DATABASE_URL'])
conn = psycopg2.connect(host=p.hostname, port=p.port or 5432,
    dbname=p.path.lstrip('/'), user=p.username, password=p.password)
cur = conn.cursor()

# Update researcher1 password
cur.execute("UPDATE users SET password_hash=%s, is_active=true WHERE username='researcher1'", (hashed,))
print(f"Updated researcher1: {cur.rowcount} row")

# Also check seed created the right hash — seed.py might handle this
cur.execute("SELECT id, username, role, is_active FROM users")
for row in cur.fetchall():
    print(f"  User: id={row[0]}, username={row[1]}, role={row[2]}, active={row[3]}")

conn.commit()
conn.close()
print("Done")
