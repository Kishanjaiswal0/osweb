import os
import subprocess
import logging


def log_action(user, action, status, extra_info=""):
    msg = f"User: {user} | Action: {action} | Status: {status}"
    if extra_info:
        msg += f" | Info: {extra_info}"
    logging.info(msg)


def create_file(user, filename):
    try:
        if os.path.exists(filename):
            log_action(user, f"Create {filename}", "Failed", "File exists")
            return "File already exists."

        with open(filename, "w") as f:
            f.write("")

        log_action(user, f"Create {filename}", "Success")
        return f"{filename} created successfully."
    except Exception as e:
        log_action(user, f"Create {filename}", "Failed", str(e))
        return "Error creating file."


def delete_file(user, filename):
    try:
        if not os.path.exists(filename):
            log_action(user, f"Delete {filename}", "Failed", "Not found")
            return "File not found."

        os.remove(filename)
        log_action(user, f"Delete {filename}", "Success")
        return f"{filename} deleted successfully."
    except Exception as e:
        log_action(user, f"Delete {filename}", "Failed", str(e))
        return "Error deleting file."


def get_process_list():
    try:
        cmd = "tasklist" if os.name == "nt" else "ps -aux"
        out = subprocess.check_output(cmd, shell=True, text=True)
        return out.splitlines()[:40]
    except Exception as e:
        return [f"Error fetching processes: {e}"]


# ✅ FIXED: read_file() is now OUTSIDE get_process_list()
def read_file(user, filename):
    try:
        if not os.path.exists(filename):
            return "File not found."

        with open(filename, "r") as f:
            content = f.read()

        log_action(user, f"Read {filename}", "Success")
        return content

    except Exception as e:
        log_action(user, f"Read {filename}", "Failed", str(e))
        return "Error reading file."


# ✅ FIXED: write_file() is correct & separate
def write_file(user, filename, data):
    try:
        if not os.path.exists(filename):
            return "File not found."

        if data is None:
            return "No content received."

        with open(filename, "w", encoding="utf-8") as f:
            f.write(data)

        log_action(user, f"Write {filename}", "Success")
        return "File updated successfully."

    except Exception as e:
        log_action(user, f"Write {filename}", "Failed", str(e))
        return f"Error writing to file: {e}"

