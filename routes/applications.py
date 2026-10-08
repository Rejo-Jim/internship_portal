from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, abort
)

from extensions import db
from models.student import StudentProfile
from models.application import Application, APPLICATION_STATUSES, STATUS_FLOW
from models.interview import Interview, INTERVIEW_TYPES, INTERVIEW_RESULTS
from models.offer import Offer, OFFER_STATUSES
from models.activity import ApplicationActivity
from routes.decorators import student_required

applications_bp = Blueprint("applications", __name__, url_prefix="/applications")


def current_profile():
    return StudentProfile.query.filter_by(user_id=session["user_id"]).first_or_404()


def log_activity(application, description):
    db.session.add(ApplicationActivity(application_id=application.id, description=description))


def owns_application(application):
    prof = current_profile()
    return application.student_id == prof.id


@applications_bp.route("/")
@student_required
def list_applications():
    prof = current_profile()
    query = prof.applications
    status_filter = request.args.get("status", "")
    search = request.args.get("q", "").strip()

    if status_filter:
        query = query.filter(Application.status == status_filter)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Application.company_name.ilike(like), Application.role.ilike(like))
        )

    apps = query.order_by(Application.created_at.desc()).all()
    return render_template(
        "student/applications.html",
        applications=apps,
        statuses=APPLICATION_STATUSES,
        status_filter=status_filter,
        search=search,
    )


@applications_bp.route("/add", methods=["GET", "POST"])
@student_required
def add_application():
    prof = current_profile()
    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        role = request.form.get("role", "").strip()
        errors = []
        if not company_name:
            errors.append("Company name is required.")
        if not role:
            errors.append("Internship role is required.")

        application_date = request.form.get("application_date", "").strip()
        application_deadline = request.form.get("application_deadline", "").strip()

        def valid_date(s):
            if not s:
                return True
            try:
                datetime.strptime(s, "%Y-%m-%d")
                return True
            except ValueError:
                return False

        if not valid_date(application_date):
            errors.append("Application date is invalid.")
        if not valid_date(application_deadline):
            errors.append("Application deadline is invalid.")

        contact_email = request.form.get("contact_email", "").strip()
        if contact_email and "@" not in contact_email:
            errors.append("Contact email is invalid.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("student/application_form.html", form=request.form, statuses=APPLICATION_STATUSES)

        app_obj = Application(
            student_id=prof.id,
            company_name=company_name,
            role=role,
            internship_type=request.form.get("internship_type", ""),
            location=request.form.get("location", "").strip(),
            work_mode=request.form.get("work_mode", ""),
            application_date=application_date,
            application_deadline=application_deadline,
            source=request.form.get("source", "").strip(),
            application_link=request.form.get("application_link", "").strip(),
            contact_person=request.form.get("contact_person", "").strip(),
            contact_email=contact_email,
            notes=request.form.get("notes", "").strip(),
            status=request.form.get("status") or "Applied",
        )
        db.session.add(app_obj)
        db.session.flush()
        log_activity(app_obj, f"Application created with status '{app_obj.status}'")
        db.session.commit()
        flash("Application added successfully.", "success")
        return redirect(url_for("applications.detail", app_id=app_obj.id))

    return render_template("student/application_form.html", form={}, statuses=APPLICATION_STATUSES)


@applications_bp.route("/<int:app_id>")
@student_required
def detail(app_id):
    application = Application.query.get_or_404(app_id)
    if not owns_application(application):
        abort(403)
    return render_template(
        "student/application_detail.html",
        application=application,
        next_statuses=application.next_allowed_statuses(),
        interview_types=INTERVIEW_TYPES,
        interview_results=INTERVIEW_RESULTS,
    )


@applications_bp.route("/<int:app_id>/edit", methods=["GET", "POST"])
@student_required
def edit_application(app_id):
    application = Application.query.get_or_404(app_id)
    if not owns_application(application):
        abort(403)

    if request.method == "POST":
        application.company_name = request.form.get("company_name", "").strip()
        application.role = request.form.get("role", "").strip()
        application.internship_type = request.form.get("internship_type", "")
        application.location = request.form.get("location", "").strip()
        application.work_mode = request.form.get("work_mode", "")
        application.application_date = request.form.get("application_date", "").strip()
        application.application_deadline = request.form.get("application_deadline", "").strip()
        application.source = request.form.get("source", "").strip()
        application.application_link = request.form.get("application_link", "").strip()
        application.contact_person = request.form.get("contact_person", "").strip()
        application.contact_email = request.form.get("contact_email", "").strip()
        application.notes = request.form.get("notes", "").strip()

        if not application.company_name or not application.role:
            flash("Company name and role are required.", "danger")
            return render_template("student/application_form.html", form=request.form, statuses=APPLICATION_STATUSES, edit=True, application=application)

        db.session.commit()
        flash("Application updated.", "success")
        return redirect(url_for("applications.detail", app_id=application.id))

    return render_template("student/application_form.html", form=application.__dict__, statuses=APPLICATION_STATUSES, edit=True, application=application)


@applications_bp.route("/<int:app_id>/status", methods=["POST"])
@student_required
def update_status(app_id):
    application = Application.query.get_or_404(app_id)
    if not owns_application(application):
        abort(403)

    new_status = request.form.get("status")
    allowed = application.next_allowed_statuses()

    if new_status not in allowed:
        flash("That status transition is not allowed.", "danger")
        return redirect(url_for("applications.detail", app_id=app_id))

    old_status = application.status
    application.status = new_status
    log_activity(application, f"Status changed from '{old_status}' to '{new_status}'")
    db.session.commit()
    flash(f"Status updated to '{new_status}'.", "success")

    if new_status == "Offer Received":
        flash("You can now create an offer record for this application.", "info")
        return redirect(url_for("applications.add_offer", app_id=app_id))

    return redirect(url_for("applications.detail", app_id=app_id))


@applications_bp.route("/<int:app_id>/delete", methods=["POST"])
@student_required
def delete_application(app_id):
    application = Application.query.get_or_404(app_id)
    if not owns_application(application):
        abort(403)
    db.session.delete(application)
    db.session.commit()
    flash("Application deleted.", "info")
    return redirect(url_for("applications.list_applications"))


# ---------------- Interviews ----------------

@applications_bp.route("/<int:app_id>/interviews/add", methods=["POST"])
@student_required
def add_interview(app_id):
    application = Application.query.get_or_404(app_id)
    if not owns_application(application):
        abort(403)

    round_name = request.form.get("round_name", "").strip()
    interview_date = request.form.get("interview_date", "").strip()

    errors = []
    if not round_name:
        errors.append("Interview round is required.")
    if interview_date:
        try:
            datetime.strptime(interview_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Interview date is invalid.")

    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("applications.detail", app_id=app_id))

    interview = Interview(
        application_id=app_id,
        round_name=round_name,
        interview_type=request.form.get("interview_type", ""),
        interview_date=interview_date,
        interview_time=request.form.get("interview_time", "").strip(),
        interviewer=request.form.get("interviewer", "").strip(),
        meeting_link=request.form.get("meeting_link", "").strip(),
        notes=request.form.get("notes", "").strip(),
        result=request.form.get("result") or "Pending",
    )
    db.session.add(interview)
    log_activity(application, f"Interview scheduled: {round_name}")
    db.session.commit()
    flash("Interview added.", "success")
    return redirect(url_for("applications.detail", app_id=app_id))


@applications_bp.route("/<int:app_id>/interviews/<int:interview_id>/result", methods=["POST"])
@student_required
def update_interview_result(app_id, interview_id):
    application = Application.query.get_or_404(app_id)
    if not owns_application(application):
        abort(403)
    interview = Interview.query.get_or_404(interview_id)
    interview.result = request.form.get("result", interview.result)
    log_activity(application, f"Interview result updated: {interview.round_name} -> {interview.result}")
    db.session.commit()
    flash("Interview result updated.", "success")
    return redirect(url_for("applications.detail", app_id=app_id))


# ---------------- Offers ----------------

@applications_bp.route("/<int:app_id>/offer/add", methods=["GET", "POST"])
@student_required
def add_offer(app_id):
    application = Application.query.get_or_404(app_id)
    if not owns_application(application):
        abort(403)

    if application.offer:
        return redirect(url_for("offers.detail", offer_id=application.offer.id))

    if request.method == "POST":
        prof = current_profile()
        offer_date = request.form.get("offer_date", "").strip()
        joining_date = request.form.get("joining_date", "").strip()

        errors = []

        def valid_date(s):
            if not s:
                return True
            try:
                datetime.strptime(s, "%Y-%m-%d")
                return True
            except ValueError:
                return False

        if not valid_date(offer_date):
            errors.append("Offer date is invalid.")
        if not valid_date(joining_date):
            errors.append("Joining date is invalid.")

        stipend = request.form.get("stipend", "").strip()
        if stipend and not stipend.replace(",", "").replace(".", "").isdigit():
            errors.append("Stipend must be a valid numeric value.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("student/offer_form.html", application=application, form=request.form)

        offer = Offer(
            application_id=application.id,
            student_id=prof.id,
            company_name=application.company_name,
            role=application.role,
            offer_date=offer_date,
            joining_date=joining_date,
            duration=request.form.get("duration", "").strip(),
            stipend=stipend,
            location=request.form.get("location", "").strip(),
            work_mode=request.form.get("work_mode", ""),
            status="Pending Decision",
        )
        db.session.add(offer)
        log_activity(application, "Offer record created")
        db.session.commit()
        flash("Offer recorded successfully.", "success")
        return redirect(url_for("offers.detail", offer_id=offer.id))

    return render_template("student/offer_form.html", application=application, form={})
