import os
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash,
    current_app, send_from_directory, abort
)
from werkzeug.utils import secure_filename

from extensions import db
from models.user import User
from models.student import StudentProfile
from models.application import Application
from models.interview import Interview
from models.offer import Offer
from routes.decorators import student_required

student_bp = Blueprint("student", __name__, url_prefix="/student")


def current_profile():
    return StudentProfile.query.filter_by(user_id=session["user_id"]).first_or_404()


@student_bp.route("/dashboard")
@student_required
def dashboard():
    profile = current_profile()
    apps = profile.applications

    total_applications = apps.count()
    in_progress = apps.filter(
        Application.status.in_([
            "Interested", "Applied", "Under Review", "Shortlisted",
            "Interview Scheduled", "Interview Completed", "Selected"
        ])
    ).count()
    interviews_scheduled = Interview.query.join(Application).filter(
        Application.student_id == profile.id,
        Interview.result == "Pending"
    ).count()
    offers_received = apps.filter(Application.status == "Offer Received").count() + \
        apps.filter(Application.status == "Accepted").count()
    accepted_offers = apps.filter(Application.status == "Accepted").count()
    rejected = apps.filter(Application.status == "Rejected").count()

    recent_apps = apps.order_by(Application.created_at.desc()).limit(5).all()

    today = datetime.utcnow().date()
    soon = today + timedelta(days=7)
    upcoming_interviews = Interview.query.join(Application).filter(
        Application.student_id == profile.id
    ).all()

    def parse_date(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            return None

    upcoming_interviews = [
        iv for iv in upcoming_interviews
        if parse_date(iv.interview_date) and today <= parse_date(iv.interview_date) <= soon
    ]
    upcoming_interviews.sort(key=lambda iv: iv.interview_date)

    status_counts = {}
    for a in apps.all():
        status_counts[a.status] = status_counts.get(a.status, 0) + 1

    return render_template(
        "student/dashboard.html",
        profile=profile,
        total_applications=total_applications,
        in_progress=in_progress,
        interviews_scheduled=interviews_scheduled,
        offers_received=offers_received,
        accepted_offers=accepted_offers,
        rejected=rejected,
        recent_apps=recent_apps,
        upcoming_interviews=upcoming_interviews,
        status_counts=status_counts,
    )


@student_bp.route("/profile", methods=["GET", "POST"])
@student_required
def profile():
    prof = current_profile()
    user = User.query.get(session["user_id"])

    if request.method == "POST":
        user.full_name = request.form.get("full_name", user.full_name).strip()
        user.phone = request.form.get("phone", user.phone).strip()

        prof.college = request.form.get("college", "").strip()
        prof.branch = request.form.get("branch", "").strip()
        prof.year = request.form.get("year", "").strip()
        prof.division = request.form.get("division", "").strip()
        prof.roll_number = request.form.get("roll_number", "").strip()
        prof.graduation_year = request.form.get("graduation_year", "").strip()
        prof.date_of_birth = request.form.get("date_of_birth", "").strip()
        prof.address = request.form.get("address", "").strip()

        cgpa_raw = request.form.get("cgpa", "").strip()
        errors = []
        if cgpa_raw:
            try:
                cgpa = float(cgpa_raw)
                if not (0 <= cgpa <= 10):
                    errors.append("CGPA must be between 0 and 10.")
                else:
                    prof.cgpa = cgpa
            except ValueError:
                errors.append("CGPA must be a valid number.")

        prof.skill_python = bool(request.form.get("skill_python"))
        prof.skill_java = bool(request.form.get("skill_java"))
        prof.skill_javascript = bool(request.form.get("skill_javascript"))
        prof.skill_html_css = bool(request.form.get("skill_html_css"))
        prof.skill_sql = bool(request.form.get("skill_sql"))
        prof.other_skills = request.form.get("other_skills", "").strip()

        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            db.session.commit()
            session["full_name"] = user.full_name
            flash("Profile updated successfully.", "success")
            return redirect(url_for("student.profile"))

    return render_template("student/profile.html", profile=prof, user=user)


@student_bp.route("/profile/resume", methods=["POST"])
@student_required
def upload_resume():
    prof = current_profile()
    file = request.files.get("resume")

    if not file or file.filename == "":
        flash("Please choose a PDF file to upload.", "danger")
        return redirect(url_for("student.profile"))

    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in current_app.config["ALLOWED_RESUME_EXTENSIONS"]:
        flash("Only PDF files are allowed for resumes.", "danger")
        return redirect(url_for("student.profile"))

    safe_name = f"student_{prof.user_id}_resume.pdf"
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], safe_name)
    file.save(filepath)

    prof.resume_filename = safe_name
    db.session.commit()
    flash("Resume uploaded successfully.", "success")
    return redirect(url_for("student.profile"))


@student_bp.route("/profile/resume/download")
@student_required
def download_resume():
    prof = current_profile()
    if not prof.resume_filename:
        abort(404)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], prof.resume_filename, as_attachment=True)
