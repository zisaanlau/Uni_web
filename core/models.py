import uuid
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from core import db
from core import app

class UserFiles(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(200))
    created_time = db.Column(db.String(200))
    created_user = db.Column(db.String(200))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(254))
    username = db.Column(db.String(254))
    password_hash = db.Column(db.String(254))
    credit = db.Column(db.Integer)
    voice_words = db.Column(db.Integer)
    audio_clone_times = db.Column(db.Integer)
    delete_clone_audio_times = db.Column(db.Integer)
    email = db.Column(db.String(255))
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

class PaymentDetails(db.Model):
    __tablename__ = 'payment_details'
    id = db.Column(db.String(20), primary_key=True, nullable=False, unique=True, default=lambda:'pd-' + str(uuid.uuid4())[:16])
    user_id = db.Column(db.Integer)
    payment_intent_id = db.Column(db.String(200), default = '')
    status = db.Column(db.Integer)
    type = db.Column(db.Integer)
    product_type = db.Column(db.String(20), default = '')
    amount = db.Column(db.Integer)
    credits = db.Column(db.Integer)
    currency = db.Column(db.String(3))
    payment_email = db.Column(db.String(20))
    name = db.Column(db.String(20), default = '')
    country = db.Column(db.String(3), default = '')
    postal_code = db.Column(db.String(10), default = '')
    dispute = db.Column(db.Integer)
    disputed = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, nullable=False, unique=False, index=False, default=datetime.now())
    updated_at = db.Column(db.DateTime, nullable=False, unique=False, index=False, default=datetime.now(), onupdate=db.func.now())

class PaymentChargeDetails(db.Model):
    id = db.Column(db.String(20), primary_key=True, nullable=False, unique=True, default=lambda:'pc-' + str(uuid.uuid4())[:16])
    external_id = db.Column(db.String(200))
    payment_intent_id = db.Column(db.String(200), default = '')
    type = db.Column(db.Integer)
    status = db.Column(db.Integer)
    amount = db.Column(db.Integer)
    amount_authorized = db.Column(db.Integer)
    amount_captured = db.Column(db.Integer)
    currency = db.Column(db.String(3))
    brand = db.Column(db.String(10))
    last4 = db.Column(db.String(4))
    exp_month = db.Column(db.Integer)
    exp_year = db.Column(db.Integer)
    country = db.Column(db.String(3))
    meta_data = db.Column(db.String(1024))
    receipt_url = db.Column(db.String(200), default = '')
    created_at = db.Column(db.DateTime, nullable=False, unique=False, index=False, default=datetime.now())
    updated_at = db.Column(db.DateTime, nullable=False, unique=False, index=False, default=datetime.now(), onupdate=db.func.now())

class PaymentIntentDetails(db.Model):
    id = db.Column(db.String(20), primary_key=True, nullable=False, unique=True, default=lambda:'pi-' + str(uuid.uuid4())[:16])
    external_id = db.Column(db.String(200))
    client_secret = db.Column(db.String(200))
    latest_charge = db.Column(db.String(200))
    type = db.Column(db.Integer)
    status = db.Column(db.Integer)
    amount = db.Column(db.Integer)
    amount_received = db.Column(db.Integer)
    meta_data = db.Column(db.String(1024))
    created_at = db.Column(db.DateTime, nullable=False, unique=False, index=False, default=datetime.now())
    updated_at = db.Column(db.DateTime, nullable=False, unique=False, index=False, default=datetime.now(), onupdate=db.func.now())

class PaymentWebhook(db.Model):
    __tablename__ = 'payment_webhook'
    id = db.Column(db.String(20), primary_key=True, nullable=False, unique=True, default=lambda:'pw-' + str(uuid.uuid4())[:16])
    external_id = db.Column(db.String(200))
    name = db.Column(db.String(254))
    amount = db.Column(db.Integer)
    client_secret = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, nullable=False, unique=False, index=False, default=datetime.now())
    updated_at = db.Column(db.DateTime, nullable=False, unique=False, index=False, default=datetime.now(), onupdate=db.func.now())

with app.app_context():
    db.drop_all()
    db.create_all()