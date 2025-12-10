from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import os
import logging
import psutil
from werkzeug.security import check_password_hash

# Import everything needed from sysmod
from sysmod import (
    create_file,
    delete_file,
    get_process_list,
    log_action,
    read_file,
    write_file
)

from userdb import (
    init_db,
    get_user_by_username,
    register_user,
    list_users,
    approve_user,
    delete_user as db_delete_user,
    update_user_role,
)

app = Flask(__name__, template_folder="tpl", static_folder="st")
app.secret_key = "osweb_secret_key_123"

logging.basicConfig(
    filename="web_logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# Initialize DB and ensure admin exists
init_db()


def require_login():
    return "user" in session


def current_metrics():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage(os.getcwd()).percent
    return {"cpu": cpu, "memory": mem, "disk": disk}


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        pwd = request.form.get("password")

        user = get_user_by_username(uname)
        if not user:
            return render_template("log.html", error="Invalid username or password")

        if not user["approved"]:
            return render_template("log.html", error="Account pending admin approval")

        if not check_password_hash(user["password_hash"], pwd):
            return render_template("log.html", error="Invalid username or password")

        session["user"] = user["username"]
        session["role"] = user["role"]
        log_action(user["username"], "Login", "Success")
        return redirect(url_for("dash"))

    return render_template("log.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        pwd = request.form.get("password")
        confirm = request.form.get("confirm")

        if not uname or not pwd or not confirm:
            return render_template("reg.html", error="All fields are required")

        if pwd != confirm:
            return render_template("reg.html", error="Passwords do not match")

        ok, msg = register_user(uname, pwd)
        if ok:
            return render_template("reg.html", success=msg)
        else:
            return render_template("reg.html", error=msg)

    return render_template("reg.html")


@app.route("/logout")
def logout():
    user = session.get("user", "unknown")
    log_action(user, "Logout", "Success")
    session.clear()
    return redirect(url_for("login"))


@app.route("/dash")
def dash():
    if not require_login():
        return redirect(url_for("login"))
    metrics = current_metrics()
    return render_template(
        "dash.html",
        user=session["user"],
        role=session["role"],
        metrics=metrics
    )
@app.route("/files", methods=["GET", "POST"])
def files():
    if not require_login():
        return redirect(url_for("login"))

    message = ""
    content = ""
    selected_file = None

    if request.method == "POST":
        filename = request.form.get("filename")
        action = request.form.get("action")

        if action == "create":
            message = create_file(session["user"], filename)

        elif action == "delete":
            if session["role"] == "admin":
                message = delete_file(session["user"], filename)
            else:
                message = "Permission denied (admin only)."

        elif action == "read":
            selected_file = filename
            content = read_file(session["user"], filename)

        elif action == "edit":
            selected_file = filename
            content = read_file(session["user"], filename)

        elif action == "write":
            if session["role"] == "admin":
                data = request.form.get("filedata")
                message = write_file(session["user"], filename, data)
                selected_file = filename
                content = read_file(session["user"], filename)
            else:
                message = "Write permission denied (admin only)."

    file_list = os.listdir()

    return render_template(
        "files.html",
        files=file_list,
        message=message,
        role=session["role"],
        selected_file=selected_file,
        content=content
    )




       
       
    


@app.route("/proc")
def proc():
    if not require_login():
        return redirect(url_for("login"))
    processes = get_process_list()
    return render_template("proc.html", processes=processes)


@app.route("/logs")
def logs():
    if not require_login():
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return "Access denied: only admin can view logs."

    try:
        with open("web_logs.txt", "r") as f:
            data = f.readlines()
    except FileNotFoundError:
        data = ["No logs yet."]

    return render_template("logs.html", logs=data)


@app.route("/users", methods=["GET", "POST"])
def users():
    if not require_login():
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return "Access denied: only admin can manage users."

    msg = ""
    if request.method == "POST":
        try:
            user_id = int(request.form.get("user_id"))
        except (TypeError, ValueError):
            user_id = None

        action = request.form.get("action")

        if not user_id or not action:
            msg = "Invalid user action."
        else:
            if action == "approve":
                approve_user(user_id)
                msg = "User approved."
            elif action == "make_admin":
                update_user_role(user_id, "admin")
                msg = "Role updated to admin."
            elif action == "make_user":
                update_user_role(user_id, "user")
                msg = "Role updated to user."
            elif action == "delete":
                db_delete_user(user_id)
                msg = "User deleted."

    all_users = list_users()
    return render_template("users.html", users=all_users, message=msg)


@app.route("/api/metrics")
def api_metrics():
    if not require_login():
        return jsonify({"error": "not authenticated"}), 401
    return jsonify(current_metrics())


if __name__ == "__main__":
    app.run(debug=True)
