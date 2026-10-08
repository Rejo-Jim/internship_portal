from datetime import datetime
from extensions import db

APPLICATION_STATUSES = [
    "Interested",
    "Applied",
    "Under Review",
    "Shortlisted",
    "Interview Scheduled",
    "Interview Completed",
    "Selected",
    "Offer Received",
    "Accepted",
    "Rejected",
    "Withdrawn",
]

# Allowed forward transitions (student can always additionally move to Rejected/Withdrawn)
STATUS_FLOW = {
    "Interested": ["Applied", "Withdrawn"],
    "Applied": ["Under Review", "Rejected", "Withdrawn"],
    "Under Review": ["Shortlisted", "Rejected", "Withdrawn"],
    "Shortlisted": ["Interview Scheduled", "Rejected", "Withdrawn"],
    "Interview Scheduled": ["Interview Completed", "Rejected", "Withdrawn"],
    "Interview Completed": ["Selected", "Rejected", "Withdrawn"],
    "Selected": ["Offer Received", "Rejected", "Withdrawn"],
    "Offer Received": ["Accepted", "Rejected", "Withdrawn"],
    "Accepted": [],
    "Rejected": [],
    "Withdrawn": [],
}

STATUS_BADGE_CLASS = {
    "Interested": "secondary",
    "Applied": "primary",
    "Under Review": "warning",
    "Shortlisted": "info",
    "Interview Scheduled": "purple",
    "Interview Completed": "purple",
    "Selected": "success",
    "Offer Received": "teal",
    "Accepted": "success",
    "Rejected": "danger",
    "Withdrawn": "dark",
}


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    internship_id = db.Column(db.Integer, db.ForeignKey("internships.id"), nullable=True)

    company_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(150), nullable=False)
    internship_type = db.Column(db.String(20))
    location = db.Column(db.String(150))
    work_mode = db.Column(db.String(20))
    application_date = db.Column(db.String(20))
    application_deadline = db.Column(db.String(20))
    source = db.Column(db.String(100))
    application_link = db.Column(db.String(255))
    contact_person = db.Column(db.String(150))
    contact_email = db.Column(db.String(150))
    notes = db.Column(db.Text)
    status = db.Column(db.String(30), default="Applied")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interviews = db.relationship(
        "Interview", backref="application", cascade="all, delete-orphan", lazy="dynamic"
    )
    offer = db.relationship(
        "Offer", backref="application", uselist=False, cascade="all, delete-orphan"
    )
    activities = db.relationship(
        "ApplicationActivity",
        backref="application",
        cascade="all, delete-orphan",
        order_by="ApplicationActivity.timestamp",
    )

    def badge_class(self):
        return STATUS_BADGE_CLASS.get(self.status, "secondary")

    def next_allowed_statuses(self):
        return STATUS_FLOW.get(self.status, [])
