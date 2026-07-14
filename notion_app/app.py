"""
app.py — Ellis Job Board (Notion-style Flask web app)
Run: python3 app.py
Open: http://127.0.0.1:5000
"""

import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

from jobs_engine import get_all_jobs
from storage import (
    load_saved_jobs, save_job, update_job, delete_job,
    load_settings, update_cover_image, update_avatar, update_quote, update_cover_position,
    load_search_cache, save_search_cache,
)

app = Flask(__name__)
app.secret_key = "ellis-secret-key"

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Home ──────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    settings = load_settings()
    return render_template("home.html", settings=settings, page="home")


@app.route("/upload-cover", methods=["POST"])
def upload_cover():
    if "cover" not in request.files:
        return redirect(request.referrer or "/")
    file = request.files["cover"]
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)
        update_cover_image(f"/uploads/{filename}")
    return redirect(request.referrer or "/")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/set-cover-position", methods=["POST"])
def set_cover_position():
    position = request.form.get("position", "50")
    # Accept numeric percent or legacy keywords
    try:
        val = float(position)
        position = str(round(val, 2))
    except ValueError:
        if position not in ("top", "center", "bottom"):
            position = "50"
    update_cover_position(position)
    if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded' and not request.referrer:
        return '', 204
    return redirect(request.referrer or "/")


@app.route("/upload-avatar", methods=["POST"])
def upload_avatar():
    if "avatar" not in request.files:
        return redirect(request.referrer or "/")
    file = request.files["avatar"]
    if file and file.filename and allowed_file(file.filename):
        filename = "avatar_" + secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)
        update_avatar(f"/uploads/{filename}")
    return redirect(request.referrer or "/")


@app.route("/save-quote", methods=["POST"])
def save_quote():
    quote = request.form.get("quote", "").strip()
    update_quote(quote)
    return redirect(request.referrer or "/")


# ── Job Search ────────────────────────────────────────────────────────────────

@app.route("/search")
def search():
    settings = load_settings()
    saved_jobs = load_saved_jobs()
    saved_links = {j["link"] for j in saved_jobs}

    # Use cached results — only re-fetch when user clicks Refresh
    cached = load_search_cache()
    if not cached:
        cached = get_all_jobs()
        save_search_cache(cached)

    jobs = [j for j in cached if j["link"] not in saved_links]
    return render_template("search.html", jobs=jobs, settings=settings, page="search")


@app.route("/refresh-jobs", methods=["POST"])
def refresh_jobs():
    fresh = get_all_jobs()
    save_search_cache(fresh)
    return redirect("/search")


@app.route("/save-job", methods=["POST"])
def save_job_route():
    job = {
        "title":    request.form.get("title", ""),
        "company":  request.form.get("company", ""),
        "location": request.form.get("location", ""),
        "link":     request.form.get("link", ""),
    }
    save_job(job)
    return redirect("/tracker")


# ── Job Tracker ───────────────────────────────────────────────────────────────

STATUSES = ["Not Applied", "Applied", "Interview", "Offer", "Rejected"]


@app.route("/tracker")
def tracker():
    settings = load_settings()
    saved_jobs = load_saved_jobs()
    return render_template("tracker.html",
                           jobs=saved_jobs,
                           statuses=STATUSES,
                           settings=settings,
                           page="tracker")


@app.route("/update-job", methods=["POST"])
def update_job_route():
    link = request.form.get("link", "")
    status = request.form.get("status")
    notes = request.form.get("notes")
    update_job(link, status=status, notes=notes)
    return redirect("/tracker")


@app.route("/delete-job", methods=["POST"])
def delete_job_route():
    link = request.form.get("link", "")
    delete_job(link)
    return redirect("/tracker")


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
