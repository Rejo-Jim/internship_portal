from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort

from extensions import db
from models.internship import Internship
from models.student import StudentProfile
from models.application import Application
from models.activity import ApplicationActivity
from routes.decorators import student_required

internships_bp = Blueprint("internships", __name__, url_prefix="/internships")


def current_profile():
    return StudentProfile.query.filter_by(user_id=session["user_id"]).first_or_404()


@internships_bp.route("/")
@student_required
def browse():
    query = Internship.query.filter(Internship.status != "Closed")

    search = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    work_mode = request.args.get("work_mode", "")
    internship_type = request.args.get("internship_type", "")
    sort = request.args.get("sort", "")

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Internship.company_name.ilike(like), Internship.title.ilike(like))
        )
    if location:
        query = query.filter(Internship.location.ilike(f"%{location}%"))
    if work_mode:
        query = query.filter(Internship.work_mode == work_mode)
    if internship_type:
        query = query.filter(Internship.internship_type == internship_type)

    if sort == "deadline":
        query = query.order_by(Internship.deadline.asc())
    else:
        query = query.order_by(Internship.created_at.desc())

    internships = query.all()
    locations = [row[0] for row in db.session.query(Internship.location).distinct() if row[0]]

    return render_template(
        "student/internships.html",
        internships=internships,
        locations=locations,
        search=search,
        location=location,
        work_mode=work_mode,
        internship_type=internship_type,
        sort=sort,
    )


@internships_bp.route("/<int:internship_id>")
@student_required
def detail(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    prof = current_profile()
    already_applied = Application.query.filter_by(
        student_id=prof.id, internship_id=internship.id
    ).first() is not None
    return render_template(
        "student/internship_detail.html",
        internship=internship,
        already_applied=already_applied,
    )


@internships_bp.route("/<int:internship_id>/apply", methods=["POST"])
@student_required
def apply(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    prof = current_profile()

    if internship.is_expired() or internship.status == "Closed":
        flash("The application deadline for this internship has passed.", "danger")
        return redirect(url_for("internships.detail", internship_id=internship_id))

    existing = Application.query.filter_by(student_id=prof.id, internship_id=internship.id).first()
    if existing:
        flash("You have already applied to this internship.", "info")
        return redirect(url_for("applications.detail", app_id=existing.id))

    app_obj = Application(
        student_id=prof.id,
        internship_id=internship.id,
        company_name=internship.company_name,
        role=internship.title,
        internship_type=internship.internship_type,
        location=internship.location,
        work_mode=internship.work_mode,
        application_date=datetime.utcnow().strftime("%Y-%m-%d"),
        application_deadline=internship.deadline,
        source="Internship Cell Portal",
        application_link=internship.application_link,
        status="Applied",
    )
    db.session.add(app_obj)
    db.session.flush()
    db.session.add(ApplicationActivity(
        application_id=app_obj.id,
        description="Applied via Internship Opportunities listing"
    ))
    db.session.commit()
    flash("Application submitted successfully!", "success")
    return redirect(url_for("applications.detail", app_id=app_obj.id))
