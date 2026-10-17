"""
Expense Tracker - Mini Project
Stack: Python (Flask), SQLite, HTML, CSS, JavaScript (Chart.js)
Features: user registration/login, add/delete expenses, categories,
          monthly total, category chart, monthly budget alert, CSV export.
"""
import csv
import io
import os
import sqlite3
from datetime import date
from functools import wraps

from flask import (Flask, Response, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "expenses.db")

app = Flask(__name__)
app.secret_key = "change-this-secret-key-before-real-use"

CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Entertainment",
              "Health", "Education", "Other"]


# ---------------------------------------------------------------- database
def get_db():
    """Open one database connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables if they do not exist."""
    db = sqlite3.connect(DATABASE)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            budget        REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            title       TEXT NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            expense_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
    )
    db.commit()
    db.close()


# ------------------------------------------------------------- login guard
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ------------------------------------------------------------ auth routes
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That username is already taken.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# -------------------------------------------------------- expense routes
def month_range(month_str):
    """Return (start, end) date strings for a 'YYYY-MM' month."""
    year, month = int(month_str[:4]), int(month_str[5:7])
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start.isoformat(), end.isoformat()


@app.route("/dashboard")
@login_required
def dashboard():
    month = request.args.get("month") or date.today().strftime("%Y-%m")
    try:
        start, end = month_range(month)
    except ValueError:
        month = date.today().strftime("%Y-%m")
        start, end = month_range(month)

    db = get_db()
    uid = session["user_id"]

    expenses = db.execute(
        """SELECT * FROM expenses
           WHERE user_id = ? AND expense_date >= ? AND expense_date < ?
           ORDER BY expense_date DESC, id DESC""",
        (uid, start, end),
    ).fetchall()

    total = sum(e["amount"] for e in expenses)

    by_category = db.execute(
        """SELECT category, SUM(amount) AS total FROM expenses
           WHERE user_id = ? AND expense_date >= ? AND expense_date < ?
           GROUP BY category ORDER BY total DESC""",
        (uid, start, end),
    ).fetchall()

    budget = db.execute(
        "SELECT budget FROM users WHERE id = ?", (uid,)
    ).fetchone()["budget"] or 0

    percent_used = round(total / budget * 100) if budget > 0 else 0

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total,
        month=month,
        categories=CATEGORIES,
        chart_labels=[r["category"] for r in by_category],
        chart_values=[round(r["total"], 2) for r in by_category],
        budget=budget,
        percent_used=percent_used,
        today=date.today().isoformat(),
    )


@app.route("/add", methods=["POST"])
@login_required
def add_expense():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "Other")
    expense_date = request.form.get("expense_date") or date.today().isoformat()

    try:
        amount = float(request.form.get("amount", ""))
    except ValueError:
        amount = 0

    if not title or amount <= 0 or category not in CATEGORIES:
        flash("Please enter a valid title, amount and category.", "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    db.execute(
        """INSERT INTO expenses (user_id, title, amount, category, expense_date)
           VALUES (?, ?, ?, ?, ?)""",
        (session["user_id"], title, amount, category, expense_date),
    )
    db.commit()
    flash("Expense added.", "success")
    return redirect(url_for("dashboard", month=expense_date[:7]))


@app.route("/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    db = get_db()
    # user_id check makes sure users can only delete their own expenses
    db.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session["user_id"]),
    )
    db.commit()
    flash("Expense deleted.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/budget", methods=["POST"])
@login_required
def set_budget():
    try:
        budget = float(request.form.get("budget", 0))
    except ValueError:
        budget = 0
    if budget < 0:
        budget = 0
    db = get_db()
    db.execute("UPDATE users SET budget = ? WHERE id = ?",
               (budget, session["user_id"]))
    db.commit()
    flash("Monthly budget updated.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/export")
@login_required
def export_csv():
    rows = get_db().execute(
        """SELECT expense_date, title, category, amount FROM expenses
           WHERE user_id = ? ORDER BY expense_date DESC""",
        (session["user_id"],),
    ).fetchall()

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Date", "Title", "Category", "Amount"])
    for r in rows:
        writer.writerow([r["expense_date"], r["title"], r["category"], r["amount"]])

    return Response(
        out.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"},
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
