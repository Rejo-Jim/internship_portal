import csv
import io
from datetime import datetime, date
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, Response, session
)

from extensions import db
from models.user import User
from models.student import StudentProfile
from models.internship import Internship
from models.application import Application, APPLICATION_STATUSES
from models.interview import Interview
from models.offer import Offer, OFFER_STATUSES
from routes.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    total_students = StudentProfile.query.count()
    total_applications = Application.query.count()
    active_applications = Application.query.filter(
        Application.status.in_([
            "Interested", "Applied", "Under Review", "Shortlisted",
            "Interview Scheduled", "Interview Completed", "Selected"
        ])
    ).count()
    total_interviews = Interview.query.count()
    total_offers = Offer.query.count()
    accepted_offers = Offer.query.filter_by(status="Accepted").count()
    rejected_applications = Application.query.filter_by(status="Rejected").count()

    # Applications by status
    status_counts = {}
    for a in Application.query.all():
        status_counts[a.status] = status_counts.get(a.status, 0) + 1

    # Applications by company (top 8)
    company_counts = {}
    for a in Application.query.all():
        company_counts[a.company_name] = company_counts.get(a.company_name, 0) + 1
    top_companies = sorted(company_counts.items(), key=lambda x: -x[1])[:8]

    # Offers by company
    offer_company_counts = {}
    for o in Offer.query.all():
        offer_company_counts[o.company_name] = offer_company_counts.get(o.company_name, 0) + 1

    # Work modes
    work_mode_counts = {}
    for i in Internship.query.all():
        work_mode_counts[i.work_mode or "Unspecified"] = work_mode_counts.get(i.work_mode or "Unspecified", 0) + 1

    # Monthly applications (by creation month)
    monthly_counts = {}
    for a in Application.query.all():
        key = a.created_at.strftime("%Y-%m") if a.created_at else "Unknown"
        monthly_counts[key] = monthly_counts.get(key, 0) + 1
    monthly_sorted = sorted(monthly_counts.items())

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        total_applications=total_applications,
        active_applications=active_applications,
        total_interviews=total_interviews,
        total_offers=total_offers,
        accepted_offers=accepted_offers,
        rejected_applications=rejected_applications,
        status_counts=status_counts,
        top_companies=top_companies,
        offer_company_counts=offer_company_counts,
        work_mode_counts=work_mode_counts,
        monthly_sorted=monthly_sorted,
    )


# ---------------- Students ----------------

@admin_bp.route("/students")
@admin_required
def students():
    query = StudentProfile.query.join(User)
    search = request.args.get("q", "").strip()
    department = request.args.get("department", "")
    year = request.args.get("year", "")

    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(User.full_name.ilike(like), User.email.ilike(like)))
    if department:
        query = query.filter(StudentProfile.branch == department)
    if year:
        query = query.filter(StudentProfile.year == year)

    profiles = query.all()
    departments = [row[0] for row in db.session.query(StudentProfile.branch).distinct() if row[0]]
    years = [row[0] for row in db.session.query(StudentProfile.year).distinct() if row[0]]

    return render_template(
        "admin/students.html",
        profiles=profiles,
        departments=departments,
        years=years,
        search=search,
        department=department,
        year=year,
    )


@admin_bp.route("/students/<int:profile_id>")
@admin_required
def student_detail(profile_id):
    profile = StudentProfile.query.get_or_404(profile_id)
    apps = profile.applications.order_by(Application.created_at.desc()).all()
    offers = profile.offers.order_by(Offer.created_at.desc()).all()
    return render_template("admin/student_detail.html", profile=profile, applications=apps, offers=offers)


# ---------------- Applications ----------------

@admin_bp.route("/applications")
@admin_required
def applications():
    query = Application.query.join(StudentProfile).join(User)

    student_search = request.args.get("student", "").strip()
    company_search = request.args.get("company", "").strip()
    status_filter = request.args.get("status", "")
    department = request.args.get("department", "")
    date_filter = request.args.get("date", "").strip()

    if student_search:
        like = f"%{student_search}%"
        query = query.filter(User.full_name.ilike(like))
    if company_search:
        query = query.filter(Application.company_name.ilike(f"%{company_search}%"))
    if status_filter:
        query = query.filter(Application.status == status_filter)
    if department:
        query = query.filter(StudentProfile.branch == department)
    if date_filter:
        query = query.filter(Application.application_date == date_filter)

    page = request.args.get("page", 1, type=int)
    per_page = 15
    total = query.count()
    apps = query.order_by(Application.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    departments = [row[0] for row in db.session.query(StudentProfile.branch).distinct() if row[0]]

    return render_template(
        "admin/applications.html",
        applications=apps,
        statuses=APPLICATION_STATUSES,
        departments=departments,
        student_search=student_search,
        company_search=company_search,
        status_filter=status_filter,
        department=department,
        date_filter=date_filter,
        page=page,
        total_pages=total_pages,
    )


@admin_bp.route("/applications/<int:app_id>")
@admin_required
def application_detail(app_id):
    application = Application.query.get_or_404(app_id)
    return render_template("admin/application_detail.html", application=application, statuses=APPLICATION_STATUSES)


@admin_bp.route("/applications/<int:app_id>/status", methods=["POST"])
@admin_required
def update_application_status(app_id):
    from models.activity import ApplicationActivity
    application = Application.query.get_or_404(app_id)
    new_status = request.form.get("status")
    if new_status in APPLICATION_STATUSES:
        old = application.status
        application.status = new_status
        db.session.add(ApplicationActivity(
            application_id=application.id,
            description=f"Status changed from '{old}' to '{new_status}' by admin"
        ))
        db.session.commit()
        flash("Application status updated.", "success")
    else:
        flash("Invalid status.", "danger")
    return redirect(url_for("admin.application_detail", app_id=app_id))


# ---------------- Internships ----------------

@admin_bp.route("/internships")
@admin_required
def internships():
    all_internships = Internship.query.order_by(Internship.created_at.desc()).all()
    return render_template("admin/internships.html", internships=all_internships)


@admin_bp.route("/internships/add", methods=["GET", "POST"])
@admin_required
def add_internship():
    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        title = request.form.get("title", "").strip()
        deadline = request.form.get("deadline", "").strip()

        errors = []
        if not company_name:
            errors.append("Company name is required.")
        if not title:
            errors.append("Internship title is required.")
        if deadline:
            try:
                datetime.strptime(deadline, "%Y-%m-%d")
            except ValueError:
                errors.append("Deadline is invalid.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/internship_form.html", form=request.form)

        internship = Internship(
            company_name=company_name,
            title=title,
            description=request.form.get("description", "").strip(),
            location=request.form.get("location", "").strip(),
            work_mode=request.form.get("work_mode", ""),
            internship_type=request.form.get("internship_type", ""),
            stipend=request.form.get("stipend", "").strip(),
            duration=request.form.get("duration", "").strip(),
            start_date=request.form.get("start_date", "").strip(),
            deadline=deadline,
            required_skills=request.form.get("required_skills", "").strip(),
            eligibility=request.form.get("eligibility", "").strip(),
            application_link=request.form.get("application_link", "").strip(),
            created_by=session.get("user_id"),
        )
        db.session.add(internship)
        db.session.commit()
        flash("Internship opportunity added.", "success")
        return redirect(url_for("admin.internships"))

    return render_template("admin/internship_form.html", form={})


@admin_bp.route("/internships/<int:internship_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_internship(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    if request.method == "POST":
        internship.company_name = request.form.get("company_name", "").strip()
        internship.title = request.form.get("title", "").strip()
        internship.description = request.form.get("description", "").strip()
        internship.location = request.form.get("location", "").strip()
        internship.work_mode = request.form.get("work_mode", "")
        internship.internship_type = request.form.get("internship_type", "")
        internship.stipend = request.form.get("stipend", "").strip()
        internship.duration = request.form.get("duration", "").strip()
        internship.start_date = request.form.get("start_date", "").strip()
        internship.deadline = request.form.get("deadline", "").strip()
        internship.required_skills = request.form.get("required_skills", "").strip()
        internship.eligibility = request.form.get("eligibility", "").strip()
        internship.application_link = request.form.get("application_link", "").strip()

        if not internship.company_name or not internship.title:
            flash("Company name and title are required.", "danger")
            return render_template("admin/internship_form.html", form=request.form, edit=True, internship=internship)

        db.session.commit()
        flash("Internship updated.", "success")
        return redirect(url_for("admin.internships"))

    return render_template("admin/internship_form.html", form=internship.__dict__, edit=True, internship=internship)


@admin_bp.route("/internships/<int:internship_id>/delete", methods=["POST"])
@admin_required
def delete_internship(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    db.session.delete(internship)
    db.session.commit()
    flash("Internship opportunity deleted.", "info")
    return redirect(url_for("admin.internships"))


@admin_bp.route("/internships/<int:internship_id>/close", methods=["POST"])
@admin_required
def close_internship(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    internship.status = "Closed"
    db.session.commit()
    flash("Internship marked as closed.", "info")
    return redirect(url_for("admin.internships"))


@admin_bp.route("/internships/<int:internship_id>/applications")
@admin_required
def internship_applications(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    apps = internship.applications.all()
    return render_template("admin/internship_applications.html", internship=internship, applications=apps)


# ---------------- Offers ----------------

@admin_bp.route("/offers")
@admin_required
def offers():
    query = Offer.query.join(StudentProfile).join(User)

    company = request.args.get("company", "").strip()
    department = request.args.get("department", "")
    year = request.args.get("year", "")
    status_filter = request.args.get("status", "")

    if company:
        query = query.filter(Offer.company_name.ilike(f"%{company}%"))
    if department:
        query = query.filter(StudentProfile.branch == department)
    if year:
        query = query.filter(StudentProfile.year == year)
    if status_filter:
        query = query.filter(Offer.status == status_filter)

    all_offers = query.order_by(Offer.created_at.desc()).all()
    departments = [row[0] for row in db.session.query(StudentProfile.branch).distinct() if row[0]]
    years = [row[0] for row in db.session.query(StudentProfile.year).distinct() if row[0]]

    return render_template(
        "admin/offers.html",
        offers=all_offers,
        statuses=OFFER_STATUSES,
        departments=departments,
        years=years,
        company=company,
        department=department,
        year=year,
        status_filter=status_filter,
    )


# ---------------- CSV Export ----------------

@admin_bp.route("/export/applications")
@admin_required
def export_applications():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Student Name", "Email", "Department", "Company", "Role",
        "Application Date", "Status", "Interview Date", "Offer Status"
    ])
    apps = Application.query.join(StudentProfile).join(User).all()
    for a in apps:
        latest_interview = a.interviews.order_by(Interview.interview_date.desc()).first()
        writer.writerow([
            a.student.user.full_name,
            a.student.user.email,
            a.student.branch or "",
            a.company_name,
            a.role,
            a.application_date or "",
            a.status,
            latest_interview.interview_date if latest_interview else "",
            a.offer.status if a.offer else "",
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications_export.csv"},
    )


@admin_bp.route("/export/students")
@admin_required
def export_students():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Full Name", "Email", "Phone", "Department", "Year", "Division", "Roll Number", "Graduation Year", "CGPA"])
    profiles = StudentProfile.query.join(User).all()
    for p in profiles:
        writer.writerow([
            p.user.full_name, p.user.email, p.user.phone or "", p.branch or "",
            p.year or "", p.division or "", p.roll_number or "", p.graduation_year or "", p.cgpa or ""
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=students_export.csv"},
    )


@admin_bp.route("/export/offers")
@admin_required
def export_offers():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "Email", "Company", "Role", "Stipend", "Joining Date", "Status"])
    all_offers = Offer.query.join(StudentProfile).join(User).all()
    for o in all_offers:
        writer.writerow([
            o.student.user.full_name, o.student.user.email, o.company_name,
            o.role, o.stipend or "", o.joining_date or "", o.status
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=offers_export.csv"},
    )
