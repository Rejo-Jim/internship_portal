from extensions import db


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    # Academic info
    branch = db.Column(db.String(100))
    year = db.Column(db.String(20))
    division = db.Column(db.String(10))
    roll_number = db.Column(db.String(30))
    graduation_year = db.Column(db.String(10))
    college = db.Column(db.String(150), default="")
    cgpa = db.Column(db.Float)

    # Personal info
    date_of_birth = db.Column(db.String(20))
    address = db.Column(db.String(255))

    # Skills
    skill_python = db.Column(db.Boolean, default=False)
    skill_java = db.Column(db.Boolean, default=False)
    skill_javascript = db.Column(db.Boolean, default=False)
    skill_html_css = db.Column(db.Boolean, default=False)
    skill_sql = db.Column(db.Boolean, default=False)
    other_skills = db.Column(db.String(255))

    # Resume
    resume_filename = db.Column(db.String(255))

    applications = db.relationship(
        "Application", backref="student", cascade="all, delete-orphan", lazy="dynamic"
    )
    offers = db.relationship(
        "Offer", backref="student", cascade="all, delete-orphan", lazy="dynamic"
    )

    def skills_list(self):
        skills = []
        if self.skill_python:
            skills.append("Python")
        if self.skill_java:
            skills.append("Java")
        if self.skill_javascript:
            skills.append("JavaScript")
        if self.skill_html_css:
            skills.append("HTML/CSS")
        if self.skill_sql:
            skills.append("SQL")
        if self.other_skills:
            skills.extend([s.strip() for s in self.other_skills.split(",") if s.strip()])
        return skills
