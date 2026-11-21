"""Run once: adds doctor login accounts. Default password for all: Doctor@123 (change it!)."""
from app import q
from werkzeug.security import generate_password_hash
try:
    q("ALTER TABLE users ADD COLUMN doctor_id INT NULL", commit=True)
except Exception:
    print("doctor_id column already exists")
h = generate_password_hash("Doctor@123")
for d in q("SELECT id,name FROM doctors"):
    email = d["name"].lower().replace("dr. ", "").replace(" ", ".") + "@medicare.in"
    if not q("SELECT id FROM users WHERE email=%s", (email,), one=True):
        q("INSERT INTO users(full_name,email,password_hash,doctor_id) VALUES(%s,%s,%s,%s)", (d["name"], email, h, d["id"]), commit=True)
    print(email)
