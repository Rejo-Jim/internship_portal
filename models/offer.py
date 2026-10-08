from datetime import datetime
from extensions import db

OFFER_STATUSES = ["Pending Decision", "Accepted", "Declined", "Withdrawn"]


class Offer(db.Model):
    __tablename__ = "offers"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False, unique=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)

    company_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(150), nullable=False)
    offer_date = db.Column(db.String(20))
    joining_date = db.Column(db.String(20))
    duration = db.Column(db.String(50))
    stipend = db.Column(db.String(50))
    location = db.Column(db.String(150))
    work_mode = db.Column(db.String(20))
    status = db.Column(db.String(30), default="Pending Decision")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
