from app.extensions import db
from datetime import datetime, timezone

class GroupJoinRequest(db.Model):
    __tablename__ = 'membership_requests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id'), nullable=False)
    status = db.Column(
        db.String(10),
        nullable=False,
        default='pending',
        server_default='pending',
        comment='Status of the request: pending, approved, rejected'
    )
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        server_default=db.func.now(),
        comment="Timestamp when the request was creted"
    )

    user = db.relationship('User', backref='join_requests', lazy=True)
    group = db.relationship('StudyGroup', backref='join_requests', lazy=True)

    def approve(self):
        """Approve the join request."""
        self.status='approved'

    def reject(self):
        """Reject the join request."""
        self.status = 'rejected'

    def __repr__(self):
        return (
            f"<GroupJoinRequest id={self.id}, user_id={self.user_id}, "
            f"group_id={self.group_id}, status='{self.status}'>"
        )