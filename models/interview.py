from datetime import datetime
from extensions import db

INTERVIEW_TYPES = ["Online", "Offline", "Technical", "HR", "Group Discussion", "Assessment"]
INTERVIEW_RESULTS = ["Pending", "Passed", "Failed", "No Show"]


class Interview(db.Model):
    __tablename__ = "interviews"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)

    round_name = db.Column(db.String(100))
    interview_type = db.Column(db.String(30))
    interview_date = db.Column(db.String(20))
    interview_time = db.Column(db.String(10))
    interviewer = db.Column(db.String(150))
    meeting_link = db.Column(db.String(255))
    notes = db.Column(db.Text)
    result = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
