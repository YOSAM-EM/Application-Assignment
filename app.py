from flask import Flask, render_template, request, redirect, session
from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key_for_sessions"  

# user registration logic 
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return "Email already registered"

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s,%s,%s)",
            (username, email, password)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# login verification of the user
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/dashboard")

        return "Invalid email or password"

    return render_template("login.html")
# this is the logout logic

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# DASHBOARD and TASK
#This is the logic for the  deadline of the tasks 
@app.route("/dashboard")
@app.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM tasks WHERE user_id=%s ORDER BY deadline ASC",
        (session["user_id"],)
    )
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()

    # deadline logic
    today = datetime.today().date()
    for task in tasks:
        if task["deadline"]:
            if isinstance(task["deadline"], str):
                deadline_date = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
            else:
                deadline_date = task["deadline"]

            task["deadline_status"] = (
                "overdue" if deadline_date < today
                else "today" if deadline_date == today
                else "upcoming"
            )
        else:
            task["deadline_status"] = "none"

    return render_template("dashboard.html", tasks=tasks)


@app.route("/complete-task/<int:task_id>")
def complete_task(task_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tasks SET status='completed' WHERE id=%s AND user_id=%s",
        (task_id, session["user_id"])
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/dashboard")
# This is the logic for adding tasks
@app.route("/add-task", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return redirect("/login")
    title = request.form["title"]
    description = request.form.get("description")
    deadline = request.form.get("deadline")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (user_id, title, description, status, deadline)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (session["user_id"], title, description, "pending", deadline)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/dashboard")

#this is  the delete task logic
@app.route("/delete-task/<int:task_id>")
def delete_task(task_id):
    if "user_id" not in session:
        return redirect("/login")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM tasks WHERE id=%s AND user_id=%s",
        (task_id, session["user_id"])
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/dashboard")



# RUN

if __name__ == "__main__":
    app.run(debug=True)
 