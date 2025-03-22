from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from core import db
class UserFiles(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(200))
    created_time = db.Column(db.String(200))
    created_user = db.Column(db.String(200))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))
    credit = db.Column(db.Integer)
    voice_words = db.Column(db.Integer)
    audio_clone_times = db.Column(db.Integer)
    delete_clone_audio_times = db.Column(db.Integer)
    email = db.Column(db.String(128))
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class ProcessQueue(db.Model):
    process_running = False
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200))
    create_time = db.Column(db.String(200))
    output_video_path = db.Column(db.String(200))
    cost = db.Column(db.Integer)

class BillQueue(db.Model):
    process_running = False
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200))
    create_time = db.Column(db.String(200))
    price = db.Column(db.Integer)
    add_credit = db.Column(db.Integer)

class AudioQueue(db.Model):
    process_running = False
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200))
    created_time = db.Column(db.String(200))
    voice_id = db.Column(db.String(200))
    voice_name = db.Column(db.String(200))
    prompt_url = db.Column(db.String(200))

class UserVoiceCloneQueue(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(200))
    credit_voice = db.Column(db.Integer)

class WxPublicMsg(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    msgId = db.Column(db.String(100))
    anwser = db.Column(db.String(1024))
    created_at = db.Column(db.String(200))