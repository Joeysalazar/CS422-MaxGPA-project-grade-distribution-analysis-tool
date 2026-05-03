from flask import Flask, render_template, request, redirect, url_for, session
from pathlib import Path

app = Flask(__name__)

# Secret key 
# Required by Flask to sign session cookies.
# Sessions are used to pass the file preview and pending data
# between the upload step and the confirm step without storing files on disk.
app.secret_key = "maxgpa-secret-key"

# ── Resolve repo root 
# app.py lives at src/ui/app.py
# .parents[0] = src/ui
# .parents[1] = src
# .parents[2] = repo root
REPO_ROOT = Path(__file__).resolve().parents[2]

# ── Supported majors 
# Keys match the dropdown option values in select.html and admin.html
# Values are the display labels shown in the report header and messages
MAJORS = {
    "cs":           "Computer Science",
    "psychology":   "Psychology",
    "architecture": "Architecture",
}

# ── Available years in the grade data ────────────────────────────────────────
# Used to populate the year range dropdowns on the selection screen
YEARS = list(range(2015, 2026))


def build_report(major_key, year_start, year_end):
    """
    Returns fake grade data organized by degree plan year and term.
    This is a placeholder until Adriana's gradeAnalysis engine is finished.
    Structure matches exactly what report.html expects so the UI can be
    fully tested without the real analysis engine.

    When Adriana finishes gradeAnalysis.py, replace this entire function
    with a call to her run_analysis() function.
    """

    # Fake course data organized by term group.
    # Each group has a heading and a list of courses.
    # Each course has:
    #   code              — course subject and number e.g. "CS 122"
    #   all_grades        — overall distribution across all instructors
    #   best_instructor   — top ranked instructor (highest % A)
    #   other_instructors — remaining instructors ranked below best
    #   no_data           — True if no grade records exist for this course
    #   asterisk_only     — True if data was redacted by UO for privacy
    fake_data = {
        "cs": [
            {
                "heading": "Year 1 — Fall",
                "courses": [
                    {
                        "code": "CS 122",
                        "all_grades": {"A": 52.0, "B": 28.0, "C": 12.0, "DNF": 8.0},
                        "best_instructor": {
                            "name": "Young, Michal",
                            "A": 65.0, "B": 22.0, "C": 8.0, "DNF": 5.0,
                            "total": 120
                        },
                        "other_instructors": [
                            {"name": "Hopkins, Boyana", "A": 48.0, "B": 30.0, "C": 14.0, "DNF": 8.0, "total": 95},
                            {"name": "Scaffidi, Chris", "A": 40.0, "B": 32.0, "C": 18.0, "DNF": 10.0, "total": 88},
                        ],
                        "no_data": False,
                        "asterisk_only": False,
                    },
                    {
                        "code": "MATH 251",
                        "all_grades": {"A": 38.0, "B": 35.0, "C": 18.0, "DNF": 9.0},
                        "best_instructor": {
                            "name": "Aksamit, Anna",
                            "A": 45.0, "B": 33.0, "C": 15.0, "DNF": 7.0,
                            "total": 80
                        },
                        "other_instructors": [
                            {"name": "Polager, Shira", "A": 35.0, "B": 36.0, "C": 20.0, "DNF": 9.0, "total": 74},
                        ],
                        "no_data": False,
                        "asterisk_only": False,
                    },
                ]
            },
            {
                "heading": "Year 1 — Winter",
                "courses": [
                    {
                        "code": "CS 210",
                        "all_grades": {"A": 55.0, "B": 25.0, "C": 12.0, "DNF": 8.0},
                        "best_instructor": {
                            "name": "Childs, Zena",
                            "A": 68.0, "B": 20.0, "C": 8.0, "DNF": 4.0,
                            "total": 110
                        },
                        "other_instructors": [
                            {"name": "Sventek, Joe", "A": 50.0, "B": 28.0, "C": 14.0, "DNF": 8.0, "total": 102},
                        ],
                        "no_data": False,
                        "asterisk_only": False,
                    },
                    {
                        # Example of a course with no grade data available
                        "code": "CS 211",
                        "all_grades": {"A": 0.0, "B": 0.0, "C": 0.0, "DNF": 0.0},
                        "best_instructor": None,
                        "other_instructors": [],
                        "no_data": True,
                        "asterisk_only": False,
                    },
                ]
            },
            {
                "heading": "Year 1 — Spring",
                "courses": [
                    {
                        "code": "CS 212",
                        "all_grades": {"A": 48.0, "B": 30.0, "C": 14.0, "DNF": 8.0},
                        "best_instructor": {
                            "name": "Fickas, Stephen",
                            "A": 58.0, "B": 26.0, "C": 10.0, "DNF": 6.0,
                            "total": 95
                        },
                        "other_instructors": [
                            {"name": "Hornof, Anthony", "A": 44.0, "B": 32.0, "C": 16.0, "DNF": 8.0, "total": 88},
                        ],
                        "no_data": False,
                        "asterisk_only": False,
                    },
                    {
                        # Example of a course where UO redacted data for privacy
                        "code": "MATH 252",
                        "all_grades": {"A": 0.0, "B": 0.0, "C": 0.0, "DNF": 0.0},
                        "best_instructor": None,
                        "other_instructors": [],
                        "no_data": True,
                        "asterisk_only": True,
                    },
                ]
            },
            {
                "heading": "Year 2 — Fall",
                "courses": [
                    {
                        "code": "CS 313",
                        "all_grades": {"A": 44.0, "B": 32.0, "C": 16.0, "DNF": 8.0},
                        "best_instructor": {
                            "name": "Erwig, Martin",
                            "A": 55.0, "B": 28.0, "C": 12.0, "DNF": 5.0,
                            "total": 78
                        },
                        "other_instructors": [
                            {"name": "Putnam, Michal", "A": 40.0, "B": 34.0, "C": 18.0, "DNF": 8.0, "total": 72},
                        ],
                        "no_data": False,
                        "asterisk_only": False,
                    },
                ]
            },
        ],
        "psychology": [
            {
                "heading": "Year 1 — Fall",
                "courses": [
                    {
                        "code": "PSY 201",
                        "all_grades": {"A": 60.0, "B": 25.0, "C": 10.0, "DNF": 5.0},
                        "best_instructor": {
                            "name": "Smolker, Harry",
                            "A": 72.0, "B": 18.0, "C": 7.0, "DNF": 3.0,
                            "total": 145
                        },
                        "other_instructors": [
                            {"name": "Creager, Alison", "A": 55.0, "B": 28.0, "C": 12.0, "DNF": 5.0, "total": 130},
                        ],
                        "no_data": False,
                        "asterisk_only": False,
                    },
                ]
            },
        ],
        "architecture": [
            {
                "heading": "Year 1 — Fall",
                "courses": [
                    {
                        "code": "ARCH 111",
                        "all_grades": {"A": 58.0, "B": 27.0, "C": 10.0, "DNF": 5.0},
                        "best_instructor": {
                            "name": "Hurtt, Steven",
                            "A": 70.0, "B": 20.0, "C": 7.0, "DNF": 3.0,
                            "total": 62
                        },
                        "other_instructors": [
                            {"name": "Tanzer, Joshua", "A": 52.0, "B": 30.0, "C": 12.0, "DNF": 6.0, "total": 58},
                        ],
                        "no_data": False,
                        "asterisk_only": False,
                    },
                ]
            },
        ],
    }

    # Return data for selected major, fall back to CS if key not found
    return fake_data.get(major_key, fake_data["cs"])


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    """
    Landing page — the first screen the user sees.
    Shows two buttons: Student and Administrator.
    No login required for either role per the project spec.
    """
    return render_template("home.html")


@app.route("/select")
def select():
    """
    Student major and year selection screen.
    Passes MAJORS dict and YEARS list to populate the dropdowns.
    """
    return render_template("select.html", majors=MAJORS, years=YEARS)


@app.route("/report")
def report():
    """
    Student report screen.
    Reads major, year_start, year_end from the URL query string,
    builds the grouped report, and renders the report template.
    Example URL: /report?major=cs&year_start=2018&year_end=2023
    """
    major_key  = request.args.get("major", "cs")
    year_start = int(request.args.get("year_start", 2015))
    year_end   = int(request.args.get("year_end",   2025))

    # Sanitize inputs — fall back to CS if unrecognized major
    if major_key not in MAJORS:
        major_key = "cs"

    # Swap silently if student accidentally reversed the year range
    if year_start > year_end:
        year_start, year_end = year_end, year_start

    groups      = build_report(major_key, year_start, year_end)
    major_label = MAJORS[major_key]

    return render_template(
        "report.html",
        major=major_label,
        year_start=year_start,
        year_end=year_end,
        groups=groups,
    )


@app.route("/admin")
def admin():
    """
    Administrator control interface.
    Pops any pending session data so it is shown once then cleared.
    This prevents stale previews from appearing on page reload.
    """
    return render_template(
        "admin.html",
        # Pop flash message — shown once after a load attempt
        message=session.pop("message", None),
        message_type=session.pop("message_type", ""),
        # Pop previews — shown after file upload, cleared after confirm/cancel
        grade_preview=session.pop("grade_preview", None),
        degree_preview=session.pop("degree_preview", None),
    )


@app.route("/admin/load-grades", methods=["POST"])
def load_grades():
    """
    Receives the uploaded grade history CSV file.
    Reads the first non-asterisk row and stores it as a preview
    in the session. The file content is also stored in the session
    so it can be saved after the admin confirms.

    Does NOT save anything to disk yet — that happens in confirm_grades().
    """
    file = request.files.get("grade_file")

    # Check a file was actually selected
    if not file or file.filename == "":
        session["message"]      = "No file selected."
        session["message_type"] = "error"
        return redirect(url_for("admin"))

    import csv, io

    # Decode the uploaded file as UTF-8 with BOM support
    content = file.read().decode("utf-8-sig")
    reader  = csv.DictReader(io.StringIO(content))

    # Find the first row where at least one value is not an asterisk or empty
    # This skips UO's privacy-redacted rows and shows real data in the preview
    preview = None
    for row in reader:
        if any(v.strip() not in ("*", "") for v in row.values()):
            preview = dict(row)
            break

    # If no valid row found the file is entirely redacted or empty
    if not preview:
        session["message"]      = "File contains no valid data rows."
        session["message_type"] = "error"
        return redirect(url_for("admin"))

    # Store preview dict and full file content in session for the confirm step
    session["grade_preview"]      = preview
    session["pending_grade_data"] = content
    return redirect(url_for("admin"))


@app.route("/admin/confirm-grades", methods=["POST"])
def confirm_grades():
    """
    Admin has confirmed the grade data preview looks correct.
    Retrieves the pending file content from the session and
    saves it to data/grades/cleaned_pub_rec_master.csv,
    replacing the existing grade data.
    """
    content = session.pop("pending_grade_data", None)

    # Safety check — if session expired or no pending data, bail out
    if not content:
        session["message"]      = "No pending data to save."
        session["message_type"] = "error"
        return redirect(url_for("admin"))

    # Build the save path and create parent folders if they don't exist
    save_path = REPO_ROOT / "data" / "grades" / "cleaned_pub_rec_master.csv"
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the file — this overwrites the existing grade data
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)

    session["message"]      = "Grade data loaded and saved successfully."
    session["message_type"] = "success"
    return redirect(url_for("admin"))


@app.route("/admin/load-degree", methods=["POST"])
def load_degree():
    """
    Receives the uploaded degree plan CSV for a specific major.
    Works the same as load_grades() — reads a preview row and
    stores the file content in the session for the confirm step.
    The major key is also stored so confirm_degree() knows which
    file to overwrite.
    """
    file      = request.files.get("degree_file")
    major_key = request.form.get("major", "cs")

    if not file or file.filename == "":
        session["message"]      = "No file selected."
        session["message_type"] = "error"
        return redirect(url_for("admin"))

    import csv, io

    content = file.read().decode("utf-8-sig")
    reader  = csv.DictReader(io.StringIO(content))

    # Find first valid row for preview
    preview = None
    for row in reader:
        if any(v.strip() not in ("*", "") for v in row.values()):
            preview = dict(row)
            break

    if not preview:
        session["message"]      = "File contains no valid data rows."
        session["message_type"] = "error"
        return redirect(url_for("admin"))

    # Store preview, content, and major key in session for confirm step
    session["degree_preview"]       = preview
    session["pending_degree_data"]  = content
    session["pending_degree_major"] = major_key
    return redirect(url_for("admin"))


@app.route("/admin/confirm-degree", methods=["POST"])
def confirm_degree():
    """
    Admin confirmed the degree plan preview.
    Saves the file to the correct path based on which major was selected.
    Each major has its own CSV file so updating one does not affect others.
    """
    content   = session.pop("pending_degree_data",  None)
    major_key = session.pop("pending_degree_major", "cs")

    if not content:
        session["message"]      = "No pending data to save."
        session["message_type"] = "error"
        return redirect(url_for("admin"))

    # Map each major key to its expected filename in data/degree_plans/matched/
    filenames = {
        "cs":           "computer_science_bs_match_report.csv",
        "psychology":   "psychology_ba_match_report.csv",
        "architecture": "architecture_barch_match_report.csv",
    }

    save_path = REPO_ROOT / "data" / "degree_plans" / "matched" / filenames[major_key]
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)

    session["message"]      = f"Degree plan for {MAJORS[major_key]} saved successfully."
    session["message_type"] = "success"
    return redirect(url_for("admin"))


@app.route("/admin/load-recon", methods=["POST"])
def load_recon():
    """
    Receives and saves the reconciliation CSV immediately.
    No preview step for reconciliation — the file is small and
    its format is simple (CHANGE_FROM, TO) so confirmation is
    not needed.
    Saves to data/reconciliation.csv.
    """
    file = request.files.get("recon_file")

    if not file or file.filename == "":
        session["message"]      = "No file selected."
        session["message_type"] = "error"
        return redirect(url_for("admin"))

    content   = file.read().decode("utf-8-sig")
    save_path = REPO_ROOT / "data" / "reconciliation.csv"

    # Create the data folder if it doesn't exist yet
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(content)

    session["message"]      = "Reconciliation file saved successfully."
    session["message_type"] = "success"
    return redirect(url_for("admin"))


if __name__ == "__main__":
    # debug=True enables auto-reload on file save during development
    app.run(debug=True)