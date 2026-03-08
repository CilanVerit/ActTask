from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()
class Task(Base):
    __tablename__ = "tasks"

    # Information
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500))
    status = Column(String(50), default="Pending") # Overdue, Pending, Completed

    # Dates
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), 
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda:datetime.now(timezone.utc))
    deadline = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

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