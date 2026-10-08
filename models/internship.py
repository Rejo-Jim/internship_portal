from datetime import date
from extensions import db


class Internship(db.Model):
    __tablename__ = "internships"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(150))
    work_mode = db.Column(db.String(20))  # On-site, Hybrid, Remote
    internship_type = db.Column(db.String(20))  # Paid, Unpaid
    stipend = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    start_date = db.Column(db.String(20))
    deadline = db.Column(db.String(20))  # stored as YYYY-MM-DD string
    required_skills = db.Column(db.String(255))
    eligibility = db.Column(db.String(255))
    application_link = db.Column(db.String(255))
    status = db.Column(db.String(20), default="Active")  # Active / Expired / Closed
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=db.func.now())

    applications = db.relationship("Application", backref="internship", lazy="dynamic")

    def is_expired(self):
        if not self.deadline:
            return False
        try:
            y, m, d = [int(x) for x in self.deadline.split("-")]
            return date(y, m, d) < date.today()
        except Exception:
            return False

    def effective_status(self):
        if self.status == "Closed":
            return "Closed"
        if self.is_expired():
            return "Expired"
        return "Active"
