# app.py
#!/usr/bin/env python
"""
Flask front-end for the Lung-Cancer Risk Predictor
* Uses PostgreSQL (works great with Python/psycopg2).
* Reads DB credentials + SECRET_KEY from .env
* Auto-creates `users` and `predictions` tables if they don’t exist,
  and ensures the `name` column is present for legacy installs.
"""
import os
import glob
import json
import datetime
import re
import smtplib
import io
import csv
from pathlib import Path
from email.mime.text import MIMEText

import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
import joblib
import pandas as pd
from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, Blueprint, g, jsonify,
    Response, abort
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2 import errors as pg_errors
from dotenv import load_dotenv
import shap

# ── env & app setup ─────────────────────────────────────────────────────────
load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

# ── email configuration ──────────────────────────────────────────────────────
GMAIL_USER       = os.getenv("GMAIL_USER")
GMAIL_PASS       = os.getenv("GMAIL_PASS")
CONTACT_RECEIVER = os.getenv("CONTACT_RECEIVER", GMAIL_USER)

login_manager = LoginManager(app)
login_manager.login_view = "auth.login"

# ── database helper ──────────────────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(
            host=os.getenv("PG_HOST", "localhost"),
            port=os.getenv("PG_PORT", "5432"),
            user=os.getenv("PG_USER", "postgres"),
            password=os.getenv("PG_PASS", ""),
            dbname=os.getenv("PG_DB", "lung_risk"),
            cursor_factory=RealDictCursor
        )
        g.db.autocommit = False
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db:
        db.close()

# ── initialize schema ────────────────────────────────────────────────────────
def init_db():
    ddl_users = """
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            pw_hash TEXT NOT NULL,
            role TEXT   DEFAULT 'user'
        );
    """
    ddl_add_name = """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS name TEXT NOT NULL DEFAULT '';
    """
    ddl_pred = """
        CREATE TABLE IF NOT EXISTS predictions(
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(id),
            ts      TIMESTAMPTZ,
            prob    DOUBLE PRECISION,
            version TEXT,
            input_json JSONB
        );
    """
    db = get_db()
    with db.cursor() as cur:
        cur.execute(ddl_users)
        cur.execute(ddl_add_name)
        cur.execute(ddl_pred)
    db.commit()

with app.app_context():
    init_db()

# ── Flask-Login user setup ──────────────────────────────────────────────────
class User:
    def __init__(self, row):
        self.id      = row["id"]
        self.name    = row.get("name", "")
        self.email   = row["email"]
        self.pw_hash = row["pw_hash"]
        self.role    = row["role"]
    def is_authenticated(self): return True
    def is_active(self): return True
    def is_anonymous(self): return False
    def get_id(self): return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
    return User(row) if row else None

# ── auth blueprint ──────────────────────────────────────────────────────────
auth_bp = Blueprint("auth", __name__, url_prefix="/")

@auth_bp.route("/login", methods=["GET","POST"])
@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pw    = request.form["password"]
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            row = cur.fetchone()
        if row and check_password_hash(row["pw_hash"], pw):
            user = User(row)
            login_user(user)
            # role‐based redirect:
            if user.role == "admin":
                return redirect(url_for("admindashboard"))
            else:
                return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("auth/registration.html", show_signup=False)


@auth_bp.route("/signup", methods=["GET","POST"])
def signup():
    if request.method=="POST":
        name     = request.form["name"].strip()
        email    = request.form["email"].strip().lower()
        password = request.form["password"]
        if not name:
            flash("Name is required."); return render_template("auth/registration.html", show_signup=True)
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash("Invalid email.");    return render_template("auth/registration.html", show_signup=True)
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*\W).{8,}$', password):
            flash("Password must be ≥8 chars."); return render_template("auth/registration.html", show_signup=True)
        pw_hash = generate_password_hash(password)
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute("INSERT INTO users(name,email,pw_hash) VALUES (%s,%s,%s)", (name,email,pw_hash))
            db.commit(); flash("Account created — please sign in."); return redirect(url_for("auth.login"))
        except pg_errors.UniqueViolation:
            db.rollback(); flash("Email already registered.")
    return render_template("auth/registration.html", show_signup=True)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("welcome"))

app.register_blueprint(auth_bp)

# ── predict endpoint ────────────────────────────────────────────────────────
@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    data = request.get_json(force=True)
    fields = [
        "YELLOW_FINGERS","ANXIETY","PEER_PRESSURE","CHRONIC DISEASE",
        "FATIGUE","ALLERGY","WHEEZING","ALCOHOL CONSUMING",
        "COUGHING","SWALLOWING DIFFICULTY","CHEST PAIN"
    ]
    sample = {f: int(data.get(f,0)) for f in fields}
    sample["ANXYELFIN"] = sample["ANXIETY"]*sample["YELLOW_FINGERS"]
    prob = float(MODEL.predict_proba(pd.DataFrame([sample]))[0,1])
    risk = "HIGH" if prob>=0.5 else ("MEDIUM" if prob>=0.2 else "LOW")

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO predictions(user_id,ts,prob,version,input_json)
            VALUES(%s,%s,%s,%s,%s) RETURNING id
        """,(
            current_user.id,
            datetime.datetime.utcnow(),
            prob,
            MODEL_VERSION,
            json.dumps(sample)
        ))
        pred_id = cur.fetchone()['id']
    db.commit()

    return jsonify({"id":pred_id,"prob":prob,"risk":risk})

# ── expert endpoint ────────────────────────────────────────────────────────
@app.route("/api/expert/<int:pred_id>")
@login_required
def api_expert(pred_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM predictions WHERE id=%s",(pred_id,))
        row = cur.fetchone()
    if not row:
        return jsonify({"error":"Prediction not found"}),404

    input_json = row['input_json']
    prob       = row['prob']
    ts         = row['ts']
    version    = row['version']

    X          = pd.DataFrame([input_json])
    explainer  = shap.TreeExplainer(MODEL)
    shap_vals  = explainer.shap_values(X)[1]
    shap_html  = shap.force_plot(
                   explainer.expected_value[1], shap_vals, X
                 ).html()

    feat_names = X.columns.tolist()
    feature_importances = np.abs(shap_vals).mean(axis=0).tolist()

    if hasattr(MODEL,'estimators_'):
        tree = MODEL.estimators_[0]
    else:
        tree = MODEL
    node_indicator = tree.decision_path(X)
    decision_path  = [f"Node {nid}" for nid in node_indicator.indices]

    sensitivity = []
    for f in feat_names:
        X2 = X.copy(); X2[f] = 1-X2[f]
        new_prob = float(MODEL.predict_proba(X2)[0,1])*100
        sensitivity.append({"feature":f,"changed_prob":round(new_prob,1)})

    with db.cursor() as cur:
        cur.execute("SELECT prob FROM predictions")
        all_probs = [r['prob']*100 for r in cur.fetchall()]
    bins, edges   = np.histogram(all_probs,bins=10,range=(0,100))
    cohort_bins   = edges[:-1].tolist()
    cohort_counts = bins.tolist()

    recs = []
    if prob>=0.5:
        recs.append("Recommend CT scan within 2 weeks")
    else:
        recs.append("Consider lifestyle interventions and follow-up")

    return jsonify({
        "shap_html":shap_html,
        "feature_names":feat_names,
        "feature_importances":feature_importances,
        "decision_path":decision_path,
        "sensitivity":sensitivity,
        "cohort_bins":cohort_bins,
        "cohort_counts":cohort_counts,
        "metrics":{"model_version":version,"generated_at":ts.isoformat()},
        "audit":{"input":input_json,"timestamp":ts.isoformat()},
        "recommendations":recs
    })

# ── download CSV endpoint ───────────────────────────────────────────────────
@app.route("/download-history")
@login_required
def download_history():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT ts, prob, version
              FROM predictions
             WHERE user_id=%s
             ORDER BY ts DESC
        """, (current_user.id,))
        rows = cur.fetchall()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["Date & Time", "Risk (%)", "Model Version"])
    for r in rows:
        writer.writerow([
            r["ts"].strftime("%Y-%m-%d %H:%M"),
            f"{r['prob']*100:.1f}%",
            r["version"]
        ])
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition":"attachment;filename=scan_history.csv"}
    )

# ── load model ──────────────────────────────────────────────────────────────
def latest_model_path():
    return max(glob.glob("trained_models/lung_*.pkl"), key=os.path.getctime)

MODEL_PATH    = latest_model_path()
MODEL         = joblib.load(MODEL_PATH)
MODEL_VERSION = Path(MODEL_PATH).name

# ── core routes ─────────────────────────────────────────────────────────────
@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/dashboard", methods=["GET","POST"])
@login_required
def dashboard():
    if current_user.role == "admin":
        return redirect(url_for("admindashboard"))
    prob = None
    if request.method=="POST":
        fields = [
            "YELLOW_FINGERS","ANXIETY","PEER_PRESSURE","CHRONIC DISEASE",
            "FATIGUE","ALLERGY","WHEEZING","ALCOHOL CONSUMING",
            "COUGHING","SWALLOWING DIFFICULTY","CHEST PAIN"
        ]
        sample = {f:1 if request.form.get(f) else 0 for f in fields}
        sample["ANXYELFIN"] = sample["ANXIETY"]*sample["YELLOW_FINGERS"]
        prob = MODEL.predict_proba(pd.DataFrame([sample]))[0,1]
        db = get_db()
        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO predictions(user_id,ts,prob,version,input_json)
                VALUES(%s,%s,%s,%s,%s)
            """, (
                current_user.id,
                datetime.datetime.utcnow(),
                prob,
                MODEL_VERSION,
                json.dumps(sample)
            ))
        db.commit()

    latest_run = (sorted(Path("runs").glob("*"))[-1].name
                  if Path("runs").exists() else None)
    return render_template("userDashboard.html",
                           prob=prob,
                           model_version=MODEL_VERSION,
                           latest_run=latest_run)

@app.context_processor
def inject_expert_panel():
    if current_user.is_authenticated and current_user.role=="expert":
        latest_run = sorted(Path("runs").glob("*"))[-1]
        return {"expert_panel": render_template("expert_panel.html", run=latest_run)}
    return {"expert_panel": None}

@app.route("/overview")
@login_required
def overview():
    return render_template("overview.html")

@app.route("/admin/scan-history")
@login_required
def admin_scan_history():
    # only admins may view
    if current_user.role != "admin":
        abort(403)

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT
              p.ts,
              p.prob,
              p.version,
              u.name,
              u.email
            FROM predictions AS p
            JOIN users       AS u
              ON p.user_id = u.id
            ORDER BY p.ts DESC
        """)
        records = cur.fetchall()
    return render_template("admin-scan-history.html", records=records)


@app.route("/download-history-all")
@login_required
def download_history_all():
    if current_user.role != "admin":
        abort(403)

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
          SELECT
            u.name, u.email,
            p.ts, p.prob, p.version
          FROM predictions p
          JOIN users u ON p.user_id = u.id
          ORDER BY p.ts DESC
        """)
        rows = cur.fetchall()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["User", "Email", "Date & Time", "Risk (%)", "Model Version"])
    for r in rows:
        writer.writerow([
            r["name"] or "",
            r["email"],
            r["ts"].strftime("%Y-%m-%d %H:%M:%S"),
            f"{r['prob']*100:.1f}%",
            r["version"]
        ])

    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition":"attachment;filename=all_scan_history.csv"}
    )


@app.route("/predictor")
@login_required
def predictor():
    return render_template("predictor.html")

@app.route("/scan-history")
@login_required
def scan_history():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT id, ts, prob, version
              FROM predictions
             WHERE user_id=%s
             ORDER BY ts DESC
        """, (current_user.id,))
        records = cur.fetchall()
    return render_template("scan-history.html", records=records)

@app.route("/result-details")
@login_required
def result_details():
    return render_template("result-details.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/admindashboard")
def admindashboard():
    if current_user.role != "admin": abort(403)
    return render_template("admindashboard.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/contact")
def contact():
    return render_template("contactUs.html")

@app.route("/send-contact-form", methods=["POST"])
def send_contact_form():
    data    = request.get_json(force=True) or {}
    name    = data.get("name","").strip()
    email   = data.get("email","").strip()
    phone   = data.get("phone","").strip()
    message = data.get("message","").strip()

    if not(name and email and phone and message):
        return jsonify({"error":"All fields required."}),400
    if not GMAIL_USER or not GMAIL_PASS:
        app.logger.error("Missing GMAIL creds")
        return jsonify({"error":"Email config missing"}),500

    html = f"""
      <h3>Contact Form Submission</h3>
      <p><strong>Name:</strong> {name}</p>
      <p><strong>Email:</strong> {email}</p>
      <p><strong>Phone:</strong> {phone}</p>
      <p><strong>Message:</strong></p>
      <p>{message}</p>
    """
    msg = MIMEText(html, "html")
    msg["Subject"]=f"Contact from {name}"
    msg["From"]=GMAIL_USER; msg["To"]=CONTACT_RECEIVER

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
            smtp.login(GMAIL_USER,GMAIL_PASS)
            smtp.send_message(msg)
        return jsonify({"message":"Your message has been sent successfully!"}),200
    except Exception:
        app.logger.exception("Error sending contact email")
        return jsonify({"error":"Failed to send message; please try again later."}),500

# ── run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
