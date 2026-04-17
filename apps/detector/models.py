from datetime import datetime

from apps.app import db

class UserImage(db.Model):
    __tablename__ = "user_images"
    id = db.Column(db.Integer, primary_key=True)
    # user_id는 users 테이블의 id 컬럼을 외부 키로 설정한다.
    user_id = db.Column(db.String, db.ForeignKey("user.id"))
    image_path = db.Column(db.String)
    is_detected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)      # Datetime → DateTime
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # Datetime → DateTime