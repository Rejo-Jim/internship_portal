"""
Database initialization / seed script for the College Internship Portal.

Usage:
    python init_db.py

This will:
  1. Create all database tables (drops and recreates for a clean demo run).
  2. Create the first admin account (from Config.ADMIN_EMAIL / ADMIN_PASSWORD,
     which can be overridden with the ADMIN_EMAIL / ADMIN_PASSWORD environment
     variables).
  3. Seed sample students, internship opportunities, and applications so the
     dashboards look populated on first run.
"""
import os
import random
from datetime import date, timedelta

from app import create_app
from extensions import db
from models.user import User
from models.student import StudentProfile
from models.internship import Internship
from models.application import Application
from models.interview import Interview
from models.offer import Offer
from models.activity import ApplicationActivity

app = create_app()

COMPANIES = ["TCS", "Infosys", "Accenture", "Deloitte", "IBM", "Microsoft", "Google"]
ROLES = [
    "Web Development Intern",
    "Python Developer Intern",
    "Java Developer Intern",
    "Data Analyst Intern",
    "Software Engineering Intern",
    "UI/UX Intern",
]
WORK_MODES = ["On-site", "Hybrid", "Remote"]
LOCATIONS = ["Mumbai", "Pune", "Bengaluru", "Hyderabad", "Remote"]

SAMPLE_STUDENTS = [
    ("Aarav Sharma", "aarav.sharma@college.edu", "Computer Engineering"),
    ("Priya Nair", "priya.nair@college.edu", "Computer Engineering"),
    ("Rohan Deshmukh", "rohan.deshmukh@college.edu", "Information Technology"),
    ("Sneha Kulkarni", "sneha.kulkarni@college.edu", "Computer Engineering"),
    ("Aditya Verma", "aditya.verma@college.edu", "Electronics Engineering"),
    ("Isha Patil", "isha.patil@college.edu", "Information Technology"),
    ("Karan Mehta", "karan.mehta@college.edu", "Computer Engineering"),
    ("Ananya Joshi", "ananya.joshi@college.edu", "Information Technology"),
]

STATUS_CYCLE = [
    "Applied", "Under Review", "Shortlisted", "Interview Scheduled",
    "Interview Completed", "Selected", "Offer Received", "Accepted", "Rejected",
]


def rand_date(start_days_ago=60, end_days_ahead=30):
    d = date.today() + timedelta(days=random.randint(-start_days_ago, end_days_ahead))
    return d.strftime("%Y-%m-%d")


def seed():
    with app.app_context():
        print("Dropping and recreating all tables...")
        db.drop_all()
        db.create_all()

        # --- Admin account ---
        admin_email = os.environ.get("ADMIN_EMAIL", app.config["ADMIN_EMAIL"])
        admin_password = os.environ.get("ADMIN_PASSWORD", app.config["ADMIN_PASSWORD"])
        admin = User(full_name="Placement Cell Admin", email=admin_email, role="admin", phone="9999999999")
        admin.set_password(admin_password)
        db.session.add(admin)
        print(f"Created admin account: {admin_email} / {admin_password}")

        # --- Internship opportunities ---
        internships = []
        for i in range(10):
            company = random.choice(COMPANIES)
            role = random.choice(ROLES)
            internship = Internship(
                company_name=company,
                title=role,
                description=f"Join {company} as a {role} and work on real-world projects with mentorship from senior engineers.",
                location=random.choice(LOCATIONS),
                work_mode=random.choice(WORK_MODES),
                internship_type=random.choice(["Paid", "Unpaid"]),
                stipend=str(random.choice([0, 5000, 8000, 10000, 15000, 20000])),
                duration=random.choice(["2 months", "3 months", "6 months"]),
                start_date=rand_date(0, 20),
                deadline=rand_date(-10, 25),
                required_skills="Python, SQL, Git" if "Python" in role or "Data" in role else "JavaScript, HTML, CSS",
                eligibility="CGPA 6.5+, Final/Third Year students",
                application_link=f"https://careers.{company.lower()}.example.com/apply",
                created_by=admin.id if admin.id else None,
            )
            db.session.add(internship)
            internships.append(internship)
        db.session.flush()

        # --- Students ---
        students = []
        for idx, (name, email, branch) in enumerate(SAMPLE_STUDENTS, start=1):
            user = User(full_name=name, email=email, role="student", phone=f"90000000{idx:02d}")
            user.set_password("Student@123")
            db.session.add(user)
            db.session.flush()

            profile = StudentProfile(
                user_id=user.id,
                branch=branch,
                year=random.choice(["Second Year", "Third Year", "Final Year"]),
                division=random.choice(["A", "B", "C"]),
                roll_number=f"{branch[:2].upper()}{100 + idx}",
                graduation_year=str(2026 + random.randint(0, 2)),
                college="Government College of Engineering",
                cgpa=round(random.uniform(6.5, 9.5), 2),
                skill_python=random.choice([True, False]),
                skill_java=random.choice([True, False]),
                skill_javascript=random.choice([True, False]),
                skill_html_css=True,
                skill_sql=random.choice([True, False]),
                other_skills="Git, Flask, Bootstrap",
            )
            db.session.add(profile)
            db.session.flush()
            students.append(profile)

        db.session.flush()

        # --- Sample applications with varied statuses ---
        for profile in students:
            num_apps = random.randint(2, 4)
            chosen_internships = random.sample(internships, k=min(num_apps, len(internships)))
            for internship in chosen_internships:
                status = random.choice(STATUS_CYCLE)
                app_obj = Application(
                    student_id=profile.id,
                    internship_id=internship.id,
                    company_name=internship.company_name,
                    role=internship.title,
                    internship_type=internship.internship_type,
                    location=internship.location,
                    work_mode=internship.work_mode,
                    application_date=rand_date(45, 0),
                    application_deadline=internship.deadline,
                    source="Internship Cell Portal",
                    application_link=internship.application_link,
                    status=status,
                )
                db.session.add(app_obj)
                db.session.flush()

                db.session.add(ApplicationActivity(
                    application_id=app_obj.id,
                    description=f"Application created with status 'Applied'"
                ))
                if status != "Applied":
                    db.session.add(ApplicationActivity(
                        application_id=app_obj.id,
                        description=f"Status changed to '{status}'"
                    ))

                # Add an interview for further-along statuses
                if status in ["Interview Scheduled", "Interview Completed", "Selected", "Offer Received", "Accepted"]:
                    db.session.add(Interview(
                        application_id=app_obj.id,
                        round_name="Round 1 - Technical",
                        interview_type=random.choice(["Online", "Technical", "HR"]),
                        interview_date=rand_date(10, 10),
                        interview_time="10:00",
                        interviewer="HR Team",
                        result="Passed" if status in ["Selected", "Offer Received", "Accepted"] else "Pending",
                    ))

                # Add an offer for offer-stage statuses
                if status in ["Offer Received", "Accepted"]:
                    offer_status = "Accepted" if status == "Accepted" else "Pending Decision"
                    db.session.add(Offer(
                        application_id=app_obj.id,
                        student_id=profile.id,
                        company_name=internship.company_name,
                        role=internship.title,
                        offer_date=rand_date(5, 0),
                        joining_date=rand_date(-20, 40),
                        duration=internship.duration,
                        stipend=internship.stipend,
                        location=internship.location,
                        work_mode=internship.work_mode,
                        status=offer_status,
                    ))

        db.session.commit()
        print(f"Seeded {len(students)} students, {len(internships)} internships, and sample applications.")
        print("\nDemo student login: aarav.sharma@college.edu / Student@123")
        print(f"Demo admin login: {admin_email} / {admin_password}")


if __name__ == "__main__":
    seed()
