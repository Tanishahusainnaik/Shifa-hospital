import os, re, datetime as dt
import mysql.connector
from flask import Flask, jsonify, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
DB = dict(host=os.environ.get("DB_HOST", "localhost"), user=os.environ.get("DB_USER", "root"),
          password=os.environ.get("DB_PASSWORD", ""), database=os.environ.get("DB_NAME", "medicare"))
SLOTS = ["09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"]
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE = re.compile(r"^[0-9+\-\s]{10,15}$")

def q(sql, args=(), one=False, commit=False):
    con = mysql.connector.connect(**DB)
    try:
        cur = con.cursor(dictionary=True)
        cur.execute(sql, args)
        if commit:
            con.commit()
            return cur.lastrowid
        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        con.close()

def err(msg, code=400):
    return jsonify(ok=False, message=msg), code

def clean(v, n=255):
    return re.sub(r"\s+", " ", (v or "").strip())[:n]

def user():
    return q("SELECT id,full_name,email,phone,dob,address,doctor_id FROM users WHERE id=%s", (session["uid"],), one=True) if "uid" in session else None

@app.context_processor
def inject():
    u = user() if "uid" in session else None
    return dict(me=u, depts_nav=None)

DOCSQL = "SELECT d.*,p.name dept FROM doctors d JOIN departments p ON p.id=d.department_id"

@app.route("/")
def home():
    return render_template("home.html", docs=q(DOCSQL + " ORDER BY d.experience DESC LIMIT 4"),
                           depts=q("SELECT * FROM departments LIMIT 6"))

@app.route("/about")
def about(): return render_template("about.html")

@app.route("/departments")
def departments(): return render_template("departments.html", depts=q("SELECT * FROM departments"))

@app.route("/doctors")
def doctors(): return render_template("doctors.html", docs=q(DOCSQL + " ORDER BY d.name"), depts=q("SELECT * FROM departments"))

@app.route("/doctors/<int:i>")
def doctor(i):
    d = q(DOCSQL + " WHERE d.id=%s", (i,), one=True)
    return render_template("doctor.html", d=d) if d else ("Doctor not found", 404)

@app.route("/services")
def services(): return render_template("services.html")

@app.route("/contact")
def contact(): return render_template("contact.html")

@app.route("/search")
def search():
    t = "%" + clean(request.args.get("q"), 60) + "%"
    return render_template("search.html", term=request.args.get("q", ""),
        docs=q(DOCSQL + " WHERE d.name LIKE %s OR p.name LIKE %s", (t, t)),
        depts=q("SELECT * FROM departments WHERE name LIKE %s OR description LIKE %s", (t, t)))

@app.route("/appointment")
def appointment():
    return render_template("appointment.html", depts=q("SELECT * FROM departments"), slots=SLOTS,
                           pre_doc=request.args.get("doctor", ""), pre_dept=request.args.get("dept", ""))

@app.route("/portal")
def portal():
    u = user()
    if not u: return render_template("portal_login.html")
    today = dt.date.today()
    if u["doctor_id"]:
        rows = q("SELECT a.*,p.name dept FROM appointments a JOIN departments p ON p.id=a.department_id "
                 "WHERE a.doctor_id=%s ORDER BY a.appt_date,a.slot", (u["doctor_id"],))
        live = [r for r in rows if r["status"] == "Confirmed"]
        return render_template("doctor_dashboard.html", today=[r for r in live if r["appt_date"] == today],
            up=[r for r in live if r["appt_date"] > today], past=[r for r in rows if r not in live or r["appt_date"] < today][::-1])
    rows = q("SELECT a.*,d.name doctor,p.name dept FROM appointments a JOIN doctors d ON d.id=a.doctor_id "
             "JOIN departments p ON p.id=a.department_id WHERE a.user_id=%s ORDER BY a.appt_date DESC", (u["id"],))
    up = [r for r in rows if r["appt_date"] >= today and r["status"] != "Cancelled"]
    return render_template("dashboard.html", up=up[::-1], hist=[r for r in rows if r not in up])

# ---------------- REST API ----------------
@app.get("/api/doctors")
def api_doctors():
    dept = request.args.get("dept", type=int)
    rows = q(DOCSQL + (" WHERE d.department_id=%s" if dept else "") + " ORDER BY d.name", (dept,) if dept else ())
    return jsonify([dict(id=r["id"], name=r["name"], dept=r["dept"]) for r in rows])

@app.get("/api/slots")
def api_slots():
    taken = q("SELECT slot FROM appointments WHERE doctor_id=%s AND appt_date=%s AND status!='Cancelled'",
              (request.args.get("doctor", type=int), request.args.get("date")))
    t = {r["slot"] for r in taken}
    return jsonify([s for s in SLOTS if s not in t])

@app.post("/api/appointments")
def api_book():
    d = request.get_json(silent=True) or {}
    name, email, phone, reason = clean(d.get("full_name"), 100), clean(d.get("email"), 120), clean(d.get("phone"), 20), clean(d.get("reason"), 500)
    try:
        doc = q("SELECT id,department_id FROM doctors WHERE id=%s", (int(d.get("doctor_id")),), one=True)
        day = dt.date.fromisoformat(d.get("appt_date", ""))
    except (TypeError, ValueError):
        return err("Choose a doctor and a valid date.")
    if len(name) < 3: return err("Enter your full name.")
    if not EMAIL.match(email): return err("Enter a valid email address.")
    if not PHONE.match(phone): return err("Enter a valid phone number (10 to 15 digits).")
    if not doc: return err("Selected doctor was not found.")
    if day < dt.date.today(): return err("Choose today or a future date.")
    if d.get("slot") not in SLOTS: return err("Choose a time slot.")
    if len(reason) < 5: return err("Briefly describe the reason for your visit.")
    try:
        i = q("INSERT INTO appointments(user_id,full_name,email,phone,doctor_id,department_id,appt_date,slot,reason) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
              (session.get("uid"), name, email, phone, doc["id"], doc["department_id"], day, d["slot"], reason), commit=True)
    except mysql.connector.IntegrityError:
        return err("That slot was just taken. Pick another time.", 409)
    return jsonify(ok=True, message=f"Appointment confirmed. Your booking reference is MC-{1000 + i}.")

@app.post("/api/appointments/<int:i>/cancel")
def api_cancel(i):
    if "uid" not in session: return err("Log in first.", 401)
    q("UPDATE appointments SET status='Cancelled' WHERE id=%s AND user_id=%s", (i, session["uid"]), commit=True)
    return jsonify(ok=True, message="Appointment cancelled.", reload=True)

@app.post("/api/appointments/<int:i>/status")
def api_status(i):
    u = user()
    if not u or not u["doctor_id"]: return err("Doctor login required.", 403)
    st = (request.get_json(silent=True) or {}).get("status")
    if st not in ("Completed", "Cancelled"): return err("Invalid status.")
    q("UPDATE appointments SET status=%s WHERE id=%s AND doctor_id=%s", (st, i, u["doctor_id"]), commit=True)
    return jsonify(ok=True, message=f"Marked {st.lower()}.", reload=True)

@app.post("/api/register")
def api_register():
    d = request.get_json(silent=True) or {}
    name, email, pw = clean(d.get("full_name"), 100), clean(d.get("email"), 120).lower(), d.get("password") or ""
    if len(name) < 3: return err("Enter your full name.")
    if not EMAIL.match(email): return err("Enter a valid email address.")
    if len(pw) < 8 or not re.search(r"\d", pw) or not re.search(r"[A-Za-z]", pw):
        return err("Password needs 8+ characters with letters and numbers.")
    if q("SELECT id FROM users WHERE email=%s", (email,), one=True): return err("An account with this email already exists.", 409)
    session["uid"] = q("INSERT INTO users(full_name,email,password_hash) VALUES(%s,%s,%s)", (name, email, generate_password_hash(pw)), commit=True)
    return jsonify(ok=True, message="Account created.", redirect="/portal")

@app.post("/api/login")
def api_login():
    d = request.get_json(silent=True) or {}
    u = q("SELECT id,password_hash FROM users WHERE email=%s", (clean(d.get("email"), 120).lower(),), one=True)
    if not u or not check_password_hash(u["password_hash"], d.get("password") or ""): return err("Incorrect email or password.", 401)
    session["uid"] = u["id"]
    return jsonify(ok=True, message="Welcome back.", redirect="/portal")

@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify(ok=True, message="Logged out.", redirect="/")

@app.put("/api/profile")
def api_profile():
    if "uid" not in session: return err("Log in first.", 401)
    d = request.get_json(silent=True) or {}
    name, phone, addr = clean(d.get("full_name"), 100), clean(d.get("phone"), 20), clean(d.get("address"))
    dob = d.get("dob") or None
    if len(name) < 3: return err("Enter your full name.")
    if phone and not PHONE.match(phone): return err("Enter a valid phone number.")
    try: dob and dt.date.fromisoformat(dob)
    except ValueError: return err("Enter a valid date of birth.")
    q("UPDATE users SET full_name=%s,phone=%s,dob=%s,address=%s WHERE id=%s", (name, phone, dob, addr, session["uid"]), commit=True)
    return jsonify(ok=True, message="Profile updated.")

@app.post("/api/contact")
def api_contact():
    d = request.get_json(silent=True) or {}
    name, email, subj, body = clean(d.get("name"), 100), clean(d.get("email"), 120), clean(d.get("subject"), 150), clean(d.get("body"), 2000)
    if len(name) < 2 or not EMAIL.match(email) or len(body) < 10: return err("Fill in your name, a valid email and a message of at least 10 characters.")
    q("INSERT INTO messages(name,email,subject,body) VALUES(%s,%s,%s,%s)", (name, email, subj, body), commit=True)
    return jsonify(ok=True, message="Message sent. We reply within one working day.")

if __name__ == "__main__":
    app.run(debug=True)
