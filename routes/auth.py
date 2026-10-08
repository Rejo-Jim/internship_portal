import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from extensions import db
from models.user import User
from models.student import StudentProfile

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        phone = request.form.get("phone", "").strip()
        branch = request.form.get("branch", "").strip()
        year = request.form.get("year", "").strip()
        division = request.form.get("division", "").strip()
        roll_number = request.form.get("roll_number", "").strip()
        graduation_year = request.form.get("graduation_year", "").strip()

        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not email or not EMAIL_RE.match(email):
            errors.append("A valid college email is required.")
        elif User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if not phone or not re.match(r"^[0-9+\-\s]{7,15}$", phone):
            errors.append("A valid phone number is required.")
        if not branch:
            errors.append("Branch/Department is required.")
        if not year:
            errors.append("Year is required.")
        if not roll_number:
            errors.append("Roll number is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html", form=request.form)

        user = User(full_name=full_name, email=email, phone=phone, role="student")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id before commit

        profile = StudentProfile(
            user_id=user.id,
            branch=branch,
            year=year,
            division=division,
            roll_number=roll_number,
            graduation_year=graduation_year,
        )
        db.session.add(profile)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form={})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        if session.get("role") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["role"] = user.role
            session["full_name"] = user.full_name
            flash(f"Welcome back, {user.full_name}!", "success")
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("student.dashboard"))
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
