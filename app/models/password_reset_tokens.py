from app.extensions import db
from datetime import datetime, timezone


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    create_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)

    def get_expires_at(self):
        if self.expires_at.tzinfo is None:
            return self.expires_at.replace(tzinfo=timezone.utc)
        return self.expires_at