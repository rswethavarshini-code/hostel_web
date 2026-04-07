from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date

app = Flask(__name__)

DB_PATH = "hostel.db"

# ---------- DATABASE CONNECTION ----------
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- LOGIN PAGE ----------
@app.route("/")
def login_page():
    return render_template("login.html")

# ---------- LOGIN CHECK ----------
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    with get_db() as conn:
        cursor = conn.cursor()

        # Admin
        cursor.execute("SELECT * FROM admins WHERE email=? AND password=?", (email, password))
        admin = cursor.fetchone()
        if admin:
            return redirect("/admin")

        # Student
        cursor.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password))
        student = cursor.fetchone()
        if student:
            student_id = student["id"]
            return redirect(f"/student/{student_id}")

    return "Invalid Login"

# ---------- STUDENT DASHBOARD ----------
@app.route("/student/<int:student_id>")
def student_dashboard(student_id):
    return render_template("student_dashboard.html", student_id=student_id)

# ---------- MENU PAGE ----------
@app.route("/menu/<int:student_id>")
def menu(student_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM menu")
        menu = cursor.fetchall()
    return render_template("menu.html", menu=menu, student_id=student_id)

# ---------- SKIP PAGE ----------
@app.route("/skip/<int:student_id>")
def skip(student_id):
    msg = request.args.get("msg")
    return render_template("skip.html", student_id=student_id, msg=msg)

# ---------- VOTE PAGE ----------
@app.route("/vote_page/<int:student_id>")
def vote_page(student_id):
    msg = request.args.get("msg")
    return render_template("vote.html", student_id=student_id, msg=msg)

# ---------- FEEDBACK PAGE (UPDATED ✅) ----------
@app.route("/feedback_page/<int:student_id>")
def feedback_page(student_id):
    msg = request.args.get("msg")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM feedback WHERE student_id=?", (student_id,))
        feedback = cursor.fetchall()

    return render_template("feedback.html",
                           student_id=student_id,
                           msg=msg,
                           feedback=feedback)

# =====================================================
# ✅ ADMIN DASHBOARD
# =====================================================
@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")

# ---------- ADMIN MENU ----------
@app.route("/admin/menu")
def admin_menu():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM menu")
        menu = cursor.fetchall()
    return render_template("admin_menu.html", menu=menu)

# ---------- ADMIN ANALYTICS ----------
@app.route("/admin/analytics")
def admin_analytics():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT rating, COUNT(*) as total FROM feedback GROUP BY rating")
        rating_data = {str(row["rating"]): row["total"] for row in cursor.fetchall()}

        cursor.execute("SELECT food, COUNT(*) as total FROM votes GROUP BY food")
        vote_data = {row["food"]: row["total"] for row in cursor.fetchall()}

        cursor.execute("SELECT meal_type, COUNT(*) as total FROM meal_skip GROUP BY meal_type")
        skip_data = {row["meal_type"]: row["total"] for row in cursor.fetchall()}

    return render_template("admin_analytics.html",
                           rating_data=rating_data,
                           vote_data=vote_data,
                           skip_data=skip_data)

# ---------- ADMIN FEEDBACK ----------
@app.route("/admin/feedbacks")
def admin_feedbacks():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM feedback")
        feedbacks = cursor.fetchall()

    return render_template("admin_feedbacks.html", feedbacks=feedbacks)

# ---------- ADMIN REPLY (NEW ✅) ----------
@app.route("/reply/<int:feedback_id>", methods=["POST"])
def reply(feedback_id):
    reply_text = request.form["reply"]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE feedback SET reply=? WHERE id=?",
            (reply_text, feedback_id)
        )
        conn.commit()

    return redirect("/admin/feedbacks")

# ---------- ADD MENU ----------
@app.route("/add_menu", methods=["POST"])
def add_menu():
    meal_type = request.form["meal_type"]
    items = request.form["items"]
    menu_date = date.today()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO menu(meal_type, items, date) VALUES (?, ?, ?)",
            (meal_type, items, menu_date)
        )
        conn.commit()

    return redirect("/admin/menu")

# ---------- VOTE ----------
@app.route("/vote", methods=["POST"])
def vote():
    student_id = request.form["student_id"]
    food = request.form["food"]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO votes(student_id, food) VALUES (?, ?)", (student_id, food))
        conn.commit()

    return redirect(f"/vote_page/{student_id}?msg=Vote submitted")

# ---------- SKIP ----------
@app.route("/skip_meal", methods=["POST"])
def skip_meal():
    student_id = request.form["student_id"]
    meal_type = request.form["meal_type"]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO meal_skip(student_id, meal_type, date) VALUES (?, ?, ?)",
            (student_id, meal_type, date.today())
        )
        conn.commit()

    return redirect(f"/skip/{student_id}?msg=Meal skipped")

# ---------- FEEDBACK ----------
@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    student_id = request.form["student_id"]
    message = request.form["message"]
    rating = request.form["rating"]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback(student_id, message, rating) VALUES (?, ?, ?)",
            (student_id, message, rating)
        )
        conn.commit()

    return redirect(f"/feedback_page/{student_id}?msg=Feedback submitted")

# ---------- RUN ----------
if __name__ == "__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
             
