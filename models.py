from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Task(db.Model):
    # Information
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(50), default="Pending") # Overdue, Pending, Completed

    # Dates
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), 
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda:datetime.now(timezone.utc))
    deadline = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deadline": self.deadline.isoformat() if self.deadline else None
        }
    
    def update_deadline(self):
        if self.deadline:
                deadline = self.deadline

                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc) # Convert to SQLite timezone

                if deadline < datetime.now(timezone.utc) and self.status != "Completed":
                    self.status = "Overdue"