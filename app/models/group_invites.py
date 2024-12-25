from app.extensions import db
from datetime import datetime, timezone, timedelta

class GroupInvites(db.Model):
    __tablename__ = 'group_invites'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(255), unique=True, nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id', ondelete='CASCADE'), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    invitee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(
        db.String(10),
        nullable=False,
        default='pending',
        server_default='pending',
        comment='Status of the request: pending, approved, rejected'
    )
    expiration = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc) + timedelta(days=7))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relationships
    group = db.relationship('StudyGroup', backref=db.backref('invites', cascade='all, delete-orphan'))
    inviter = db.relationship('User', foreign_keys=[inviter_id], backref=db.backref('sent_invites', cascade='all, delete-orphan'))
    invitee = db.relationship('User', foreign_keys=[invitee_id], backref=db.backref('received_invites', cascade='all, delete-orphan'))
    
    def is_expired(self):
        return datetime.now(timezone.utc) > self.expiration.replace(tzinfo=timezone.utc)

    