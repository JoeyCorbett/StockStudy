from app.extensions import db
from datetime import datetime, timezone

class StudyGroup(db.Model):
    __tablename__ = 'study_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String, nullable=False)
    max_members = db.Column(db.Integer, nullable=False)
    current_members = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', name="fk_owner_id_users"), nullable=False)
    owner = db.relationship('User', back_populates='owned_groups')

    members = db.relationship('User', secondary='user_groups', back_populates='study_groups')

  
    
    def __repr__(self):
        return f"<StudyGroup {self.name} (ID: {self.id} )>"