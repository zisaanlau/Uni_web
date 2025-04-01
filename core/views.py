from flask import render_template, request, url_for, redirect, flash, Response, jsonify
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired
from sqlalchemy.exc import SQLAlchemyError

from core import app, db, executor
from core.models import UserFiles, User, ProcessQueue, AudioQueue, UserVoiceCloneQueue, WxPublicMsg, PaymentDetails, PaymentChargeDetails, PaymentIntentDetails
import subprocess
import platform
import json
import stripe
import time
import requests
import threading
import os

from tool.stripe_util import validate_stripe_webhook, create_payment_intent, create_payment_charge_details, create_webhook_record, create_payment_details

os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'] = 'LTAI5tGnSHE7iu6n8fkZJoaQ'
os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'] = 'rDQtRcMUcCGM5W6ETcMLVrAQ6sesaG'
from functools import wraps
from tool.chat_backend import chat_backend
from tool.tts_backend import tts_backend, voice_clone_backend
from tool.video_backend import video_backend
import shutil
import datetime
import uuid
from tool.file_backend import get_file_type
import xml.etree.ElementTree as ET

from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions
from alibabacloud_videoenhan20200320.client import Client

from alibabacloud_viapi20230117.models import GetAsyncJobResultRequest
from alibabacloud_videoenhan20200320.models import SuperResolveVideoAdvanceRequest, EnhancePortraitVideoAdvanceRequest

# 生产
# stripe.api_key = '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'

# 测试
stripe.api_key = 'sk_test_51QafNkGHijBvYVwYliMvLWi6myRLwg7RuCa8E6r0vYDTRHCh6OlImX4ChIv7UDvKYY8FAaZrKOqr2CXm6RxiF8CG00vf83WO4y'


def create_token(user_id):
    s = Serializer(app.config['SECRET_KEY'], expires_in=7200)
    token = s.dumps({'user_id': user_id}).decode("ascii")
    return token


def encode_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token.encode("ascii"))
        return data
    # usr = User.query.filter_by(username = data['user_id']).first()
    # return usr
    except SignatureExpired:
        return None
    except BadSignature:
        return None


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('token')
        # if request.url == '/api/tts/set_audios':
        #   return view_func(*args, **kwargs)
        if not token:
            return json.dumps({'code': 401, 'status': 'false', 'msg': '身份验证失败，请重新登录.'})
        # user = encode_token(token)
        # # 如果token不存在，验证用户id与密码是否匹配
        # if not user:
        #   return json.dumps({'code': 401,'status': 'false','msg':'身份验证失败，请重新登录.'})
        return view_func(*args, **kwargs)

    return wrapper


@app.route('/')
def index():
    return render_template('/index.html')


@app.route('/workbenches')
def workbenches():
    return render_template('/workbenches/index.html')


@app.route('/sysApi/getUserFiles', methods=["POST"])
def getUserFiles():
    page = int(request.form['page'])
    pageSize = int(request.form['pageSize'])
    data = UserFiles.query.all()
    total = len(data)
    res = []
    for item in data[pageSize * (page - 1):pageSize * page - 1]:
        obj = {
            'id': item.id,
            'file_path': item.file_path,
            'created_time': item.created_time,
            'created_user': item.created_user
        }
        res.append(obj)
    return json.dumps({
        'code': 200,
        'status': 'true',
        'msg': '请求成功',
        'data': {
            "rows": res,
            "total": total
        }
    })


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']
        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))
        user = User.query.first()
        user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))
    return render_template('settings.html')


@app.route('/api/chat_with_file', methods=['POST'])
@login_required
def chat_with_file():
    token = request.headers.get('token')
    user = encode_token(token)
    user_username = user.username
    create_time = str(datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S"))
    dir_path = os.path.join("core/static/file_from_user", user_username, create_time)
    os.makedirs(dir_path, exist_ok=True)
    # userMessage = request.form.get('userMessage')
    userMessage = request.form.get('userMessage')
    userMessage = json.loads(userMessage)
    userMessage = userMessage[-1]['text']
    model_name = int(request.form.get('model_name'))
    model_name_map = {0: 'Ziwei', 1: "gpt4", 2: "gpt3.5", 3: "Ziwei_small", 4: "Ziwei_large"}
    fileToUpload = request.files.get('uploadfile')

    if fileToUpload != None:
        file_type = fileToUpload.filename.split('.')[-1]
        file_name = os.path.join(dir_path, 'tmp.' + file_type)
        fileToUpload.save(file_name)
    else:
        file_name = ''
    answer = chat_backend(userMessage, model_name, file=file_name)
    answer = model_name_map[model_name] + ':' + answer

    return json.dumps({'code': 200,
                       'status': 'true',
                       'msg': '请求成功', "text": answer, "image_path": 'static/image/demo1.jpeg',
                       "video_path": 'static/video/new1.mp4'})


@app.route('/api/set_video_hd', methods=['POST'])
@login_required
def set_video_hd():
    token = request.headers.get('token')
    user = encode_token(token)
    user_username = user.username
    video_param = request.form.get('video_param')
    fileToUpload = request.files.get('fileToUpload')
    cost = int(request.form.get('cost'))
    item = User.query.filter_by(username=user_username).first()
    if item.credit < cost:
        return json.dumps(
            {
                'code': 503,
                'status': 'false',
                'msg': '积分余额不足！'})

    create_time = str(datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S"))

    dir_path = os.path.join("core/static/file_from_user", user_username, create_time)
    os.makedirs(dir_path, exist_ok=True)
    filename = uuid.uuid4().hex + '.mp4'
    file_path = os.path.join(dir_path, filename)
    fileToUpload.save(file_path)
    config = Config(
        # 创建AccessKey ID和AccessKey Secret，请参考https://help.aliyun.com/document_detail/175144.html。
        # 如果您用的是RAM用户的AccessKey，还需要为RAM用户授予权限AliyunVIAPIFullAccess，请参考https://help.aliyun.com/document_detail/145025.html
        # 从环境变量读取配置的AccessKey ID和AccessKey Secret。运行代码示例前必须先配置环境变量。
        access_key_id=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID'),
        access_key_secret=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET'),
        # 访问的域名
        endpoint='videoenhan.cn-shanghai.aliyuncs.com',
        # 访问的域名对应的region
        region_id='cn-shanghai'
    )
    img = open(file_path, 'rb')
    # img = open('core/static/image/video/exam_gan.mp4', 'rb')
    # url = 'https://viapi-test-bj.oss-cn-beijing.aliyuncs.com/viapi-3.0domepic/videoenhan/SuperResolveVideo/SuperResolveVideo1.mp4'
    # img = io.BytesIO(urlopen(url).read())
    # 视频超分
    # super_resolve_video_request = SuperResolveVideoAdvanceRequest()
    # super_resolve_video_request.video_url_object = img
    # super_resolve_video_request.bit_rate = video_param

    # 人像增强
    enhance_portrait_video_request = EnhancePortraitVideoAdvanceRequest()
    enhance_portrait_video_request.video_url_object = img
    runtime = RuntimeOptions()
    try:
        # 初始化Client
        client = Client(config)
        # 超分
        # response = client.super_resolve_video_advance(super_resolve_video_request, runtime)
        # 人脸增强
        response = client.enhance_portrait_video_advance(enhance_portrait_video_request, runtime)
        # 获取整体结果
        res = str(response.body)
        item.credit -= cost
        db.session.commit()
        return json.dumps({'code': 200,
                           'status': 'true',
                           'msg': '请求成功',
                           'data': res
                           })
    except Exception as error:

        return json.dumps({'code': 500,
                           'status': 'false',
                           'msg': error,
                           })


@app.route('/api/get_video_hd', methods=['POST'])
@login_required
def get_video_hd():
    job_id = request.form.get('job_id')
    config = Config(
        # 创建AccessKey ID和AccessKey Secret，请参考https://help.aliyun.com/document_detail/175144.html。
        # 如果您用的是RAM用户的AccessKey，还需要为RAM用户授予权限AliyunVIAPIFullAccess，请参考https://help.aliyun.com/document_detail/145025.html
        # 从环境变量读取配置的AccessKey ID和AccessKey Secret。运行代码示例前必须先配置环境变量。
        access_key_id=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID'),
        access_key_secret=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET'),
        # 访问的域名
        endpoint='videoenhan.cn-shanghai.aliyuncs.com',
        # 访问的域名对应的region
        region_id='cn-shanghai'
    )
    get_async_job_result_request = GetAsyncJobResultRequest(
        job_id=job_id
    )
    runtime = RuntimeOptions()
    try:
        client = Client(config)
        response = client.get_async_job_result_with_options(get_async_job_result_request, runtime)

        return json.dumps({'code': 200,
                           'status': 'true',
                           'msg': '请求成功',
                           'data': str(response.body)
                           })
    except Exception as error:

        return json.dumps({'code': 500,
                           'status': 'false',
                           'msg': error,
                           })


@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    os.makedirs('core/static/file_from_user/', exist_ok=True)
    model_name_map = {0: 'Ziwei', 1: "gpt4", 2: "gpt3.5", 3: "Ziwei_small", 4: "Ziwei_large"}
    userMessage = request.form.get('userMessage')
    isUseAi = request.form.get('isUseAi')
    example_img = request.form.get('example_img')
    model_name = int(request.form.get('model_name'))
    voice_type = request.form.get('voice')
    if isUseAi != 'true':
        answer = chat_backend(userMessage, model_name)
        answer = model_name_map[model_name] + ':' + answer
        return json.dumps({'code': 200,
                           'status': 'true',
                           'msg': '请求成功', "text": answer, "image_path": 'static/image/demo1.jpeg',
                           "video_path": 'static/video/new1.mp4'})
    else:
        filename = str(datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")) + "__" + uuid.uuid4().hex + '.jpeg'
        file_path = os.path.join("core/static/file_from_user", filename)
        if example_img != None:

            example_img = os.path.join("core", example_img)
            shutil.copy(example_img, file_path)
        else:
            fileToUpload = request.files.get('fileToUpload')
            file_type = get_file_type(fileToUpload)

            fileToUpload.save(file_path)

        if userMessage == "":
            userMessage = '你好'
        answer = chat_backend(userMessage)

        # audio
        # audio_path = os.path.join("core/static/file_from_user", filename.split('.')[0] + ".mp3")
        # tts_backend(answer,audio_path,voice_type)

        # image 
        video_backend(filename, answer, voice_type)
        return json.dumps(
            {
                'code': 200,
                'status': 'true',
                'msg': '请求成功',
                "text": model_name_map[model_name] + ':' + answer,
                "image_path": os.path.join("static/file_from_user", filename),
                "video_path": os.path.join("static/file_from_user", filename.split('.')[0] + "_new.mp4")})


@app.route('/api/get_works', methods=["GET", 'POST'])
def get_works():
    token = request.headers.get('token')

    data = ProcessQueue.query.filter_by(username=token).all()
    res = []
    total = len(data)
    for item in data:
        obj = {
            'id': item.id,
            'create_time': item.create_time,
            'output_video_path': item.output_video_path,
            'cost': item.cost,
        }
        res.append(obj)
    return json.dumps({
        'code': 200,
        'status': 'true',
        'msg': '请求成功',
        'data': {
            "rows": res,
            "total": total
        }
    })


@app.route('/api/delete_works', methods=["GET", 'POST'])
def delete_works():
    token = request.headers.get('token')
    userid = token
    id = request.form.get('id')
    data = ProcessQueue.query.get(id)
    if data.username != userid:
        return json.dumps({
            'code': 403,
            'status': 'false',
            'msg': '不允许删除别人的视频！'
        })
    else:
        # folder_path = 'core/static/file_from_user/' + data.username +'/'+ data.create_time
        # shutil.rmtree(folder_path)
        db.session.delete(data)
        db.session.commit()
        return json.dumps({
            'code': 200,
            'status': 'true',
            'msg': '删除成功'
        })


@app.route('/api/dub_voice_v1', methods=["GET", 'POST'])
def dub_voice_v1():
    token = request.headers.get('token')
    user_username = token
    create_time = str(datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S"))
    userMessage = request.form.get('userMessage')
    cost = len(userMessage)
    item = User.query.filter_by(username=user_username).first()
    if item.credit < cost:
        return json.dumps(
            {
                'code': 503,
                'status': 'false',
                'msg': '账号配音字数余额不足！'})
    voice_type = request.form.get('voice')
    voice_clone = request.form.get('voice_clone')

    dir_path = os.path.join("core/static/file_from_user", user_username, create_time)
    os.makedirs(dir_path, exist_ok=True)
    answer = userMessage

    audio_path = os.path.join(dir_path, uuid.uuid4().hex + ".mp3")
    if voice_type != None:
        tts_backend(answer, audio_path, voice_type)
    else:
        voice_clone_backend(answer, audio_path, voice_clone)

    item.credit -= cost
    db.session.commit()
    return json.dumps(
        {
            'code': 200,
            'status': 'true',
            'data': {
                'credit': item.credit,
                'audio_path': audio_path
            },
            'msg': '音频输出成功。'})


@app.route('/api/read_text', methods=["GET", 'POST'])
@login_required
def read_text():
    token = request.headers.get('token')
    user = encode_token(token)
    user_username = user.username
    user_id = user.id
    create_time = str(datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S"))
    userMessage = request.form.get('userMessage')
    cost = int(request.form.get('cost'))
    item = User.query.filter_by(username=user_username).first()
    if item.credit < cost:
        return json.dumps(
            {
                'code': 503,
                'status': 'false',
                'msg': '积分余额不足！'})
    example_img = request.form.get('example_img')
    voice_type = request.form.get('voice')
    voice_clone = request.form.get('voice_clone')

    dir_path = os.path.join("core/static/file_from_user", user_username, create_time)
    os.makedirs(dir_path, exist_ok=True)
    if example_img != None:
        filename = uuid.uuid4().hex + '.jpeg'
        file_path = os.path.join(dir_path, filename)
        file_type = 'Image'
        example_img = os.path.join('core', example_img)

        shutil.copy(example_img, file_path)
    else:
        fileToUpload = request.files.get('fileToUpload')
        file_type = get_file_type(fileToUpload.filename)
        if file_type == 'Image':
            filename = uuid.uuid4().hex + '.jpeg'
            file_path = os.path.join(dir_path, filename)
            fileToUpload.save(file_path)
        elif file_type == 'Video':
            filename = uuid.uuid4().hex + '.mp4'
            file_path = os.path.join(dir_path, filename)
            fileToUpload.save(file_path)

    # chat
    answer = userMessage
    if userMessage != None:
        audio_path = os.path.join(dir_path, filename.split('.')[0] + ".mp3")
        if voice_type != None:
            tts_backend(answer, audio_path, voice_type)
        else:
            voice_clone_backend(answer, audio_path, voice_clone)

    else:
        audio = request.files.get('audio')
        audio_path = os.path.join(dir_path, filename.split('.')[0] + ".mp3")
        audio.save(audio_path)

    cost = 1
    executor.submit(video_backend,
                    id=int(db.session.query(db.func.max(ProcessQueue.id)).scalar() or 0) + 1,
                    username=user_username,
                    cost=cost,
                    create_time=create_time,
                    input_file_path=file_path,
                    input_audio_path=audio_path,
                    credit_cost=cost,
                    input_text=userMessage if userMessage else '音频交件'
                    )
    item.credit -= cost
    db.session.commit()
    return json.dumps(
        {
            'code': 200,
            'status': 'true',
            'msg': '视频正在制作中，请稍后去个人中心生成记录里面查看。'})


@app.route('/api/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return json.dumps({'msg': '请输入用户名或密码.'})
        this_user = User.query.filter_by(username=username).all()
        if len(this_user) == 0:
            flash('用户不存在')
            return json.dumps({'code': 401, 'status': 'false', 'msg': '用户不存在.'})
        user = this_user[0]

        # if username == user.username and user.validate_password(password):
        if username == user.username and user.password_hash == password:

            token = create_token(user.username)

            flash('Login success.')
            return json.dumps({
                'code': 200,
                'status': 'true',
                'msg': '登录成功',
                'data': {
                    "name": user.name,
                    "username": user.username,
                    "credit": user.credit,
                    "token": token
                }
            })
            # return redirect(url_for('index'))

        flash('Invalid username or password.')
        return json.dumps({'code': 401, 'status': 'false', 'msg': '用户名或密码不正确.'})
        # return redirect(url_for('login'))
    return json.dumps({'code': 401, 'status': 'false', 'msg': '请登录'})


@app.route('/api/mylogin', methods=['POST'])
def mylogin():
    obj = json.loads(request.get_data(as_text=True))
    displayName = obj['displayName']
    uid = obj['localId']
    email = obj['email']
    this_user = User.query.filter_by(username=uid).all()
    credit = 0
    if len(this_user) == 0:
        id = int(db.session.query(db.func.max(User.id)).scalar() or 0) + 1
        new_job = User(
            id=id,
            name=displayName,
            username=uid,
            password_hash='',
            credit=500,
            voice_words=10000,
            audio_clone_times=5,
            delete_clone_audio_times=5,
            email=email
        )
        db.session.add(new_job)
        db.session.commit()
        credit = 0
    else:
        user = this_user[0]
        credit = user.credit
    return json.dumps({
        'code': 200,
        'status': 'true',
        'msg': '登录成功',
        'data': {
            "credit": credit,
        }
    })


@app.route('/api/getCredit', methods=['GET', 'POST'])
@login_required
def getCredit():
    token = request.headers.get('token')
    user = encode_token(token)
    userid = user.username
    get_user = User.query.filter_by(username=userid).all()
    return json.dumps(
        {
            'code': 200,
            'status': 'true',
            'data': {
                'credit': get_user[0].credit
            }})


@app.route('/api/get_voice_words', methods=['GET', 'POST'])
def get_voice_words():
    token = request.headers.get('token')
    userid = token
    get_user = User.query.filter_by(username=userid).all()
    return json.dumps(
        {
            'code': 200,
            'status': 'true',
            'data': {
                'voice_words': get_user[0].credit
            }})
    # return render_template('login.html')


# @app.route('/regist', methods=['GET','POST'])
# def regist():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         password1 = request.form['password1']
#         if not username or not password or not password1:
#             flash('Invalid input.')
#             return redirect(url_for('login'))
#         if password!=password1:
#             flash('两次密码不同')
#             return redirect(url_for('login'))

#         user = User(username=username, name=username)
#         user.set_password(password)
#         db.session.add(user)
#         db.session.commit()
#         flash('注册成功')
#         return redirect(url_for('index'))
#     return render_template('regist.html')

@app.route('/sysApi/login', methods=['GET', 'POST'])
def sysLogin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return json.dumps({'msg': '请输入用户名或密码.'})
        if username != 'admin':
            flash('用户不存在')
            return json.dumps({'code': 403, 'status': 'false', 'msg': '用户不存在.'})
        this_user = User.query.filter_by(username=username).all()
        if len(this_user) == 0:
            flash('用户不存在')
            return json.dumps({'code': 403, 'status': 'false', 'msg': '用户不存在.'})
        user = this_user[0]

        # if username == user.username and user.validate_password(password):
        if username == user.username and user.password_hash == password:
            # login_user(user)
            token = create_token(user.username)
            flash('Login success.')
            return json.dumps({
                'code': 200,
                'status': 'true',
                'msg': '登录成功',
                'data': {
                    "name": user.name,
                    "username": user.username,
                    "token": token
                }
            })
            # return redirect(url_for('index'))

        flash('Invalid username or password.')
        return json.dumps({'code': 403, 'status': 'false', 'msg': '用户名或密码不正确.'})
        # return redirect(url_for('login'))
    return json.dumps({'code': 403, 'status': 'false', 'msg': '请登录'})


@app.route('/sysApi/getUser', methods=["GET", 'POST'])
@login_required
def getUser():
    token = request.headers.get('token')
    page = int(request.form['page'])
    pageSize = int(request.form['pageSize'])
    data = User.query.all()
    total = len(data)
    res = []
    for item in data[pageSize * (page - 1):pageSize * page - 1]:
        obj = {
            'id': item.id,
            'username': item.name,
            'userid': item.username,
            'credit': item.credit,
            'audio_clone_times': item.audio_clone_times,
        }
        res.append(obj)
    return json.dumps({
        'code': 200,
        'status': 'true',
        'msg': '请求成功',
        'data': {
            "rows": res,
            "total": total
        }
    })


@app.route('/sysApi/deleteUser', methods=["GET", 'POST'])
@login_required
def deleteUser():
    ids = request.form['ids']

    items = User.query.filter(User.id.in_(ids)).all()
    for item in items:
        db.session.delete(item)
    db.session.commit()
    return json.dumps({
        'code': 200,
        'status': 'true',
        'msg': '删除成功',
    })


@app.route('/sysApi/addUser', methods=["GET", 'POST'])
@login_required
def addUser():
    id = int(db.session.query(db.func.max(User.id)).scalar() or 0) + 1
    name = request.form['username']
    username = request.form['userid']
    password_hash = request.form['password']
    credit = request.form['credit']
    audio_clone_times = request.form['audio_clone_times']
    new_user = User(
        id=id,
        name=name,
        username=username,
        password_hash=password_hash,
        credit=credit,
        audio_clone_times=audio_clone_times
    )
    db.session.add(new_user)
    db.session.commit()
    return json.dumps({
        'code': 200,
        'status': 'true',
        'msg': '新增成功',
    })


@app.route('/sysApi/get_works', methods=["GET", 'POST'])
@login_required
def sys_get_works():
    page = int(request.form['page'])
    pageSize = int(request.form['pageSize'])
    username = request.form['username']
    if username:
        data = ProcessQueue.query.filter_by(username=username).all()
    else:
        data = ProcessQueue.query.all()
    total = len(data)
    res = []
    for item in data[pageSize * (page - 1):pageSize * page - 1]:
        obj = {
            'id': item.id,
            'username': item.username,
            'create_time': item.create_time,
            'input_file_path': item.input_file_path,
            'credit_cost': item.credit_cost,
            'input_text': item.input_text,
            'input_audio_path': item.input_audio_path,
            'output_img_path': item.output_img_path,
            'output_video_path': item.output_video_path
        }
        res.append(obj)
    return json.dumps({
        'code': 200,
        'status': 'true',
        'msg': '请求成功',
        'data': {
            "rows": res,
            "total": total,
            "process_running": ProcessQueue.process_running
        }
    })


@app.route('/sysApi/set_userinfo', methods=["GET", 'POST'])
@login_required
def sys_set_userinfo():
    userid = request.form['userid']
    username = request.form['username']
    audio_clone_times = int(request.form['audio_clone_times'])
    credit = int(request.form['credit'])
    item = User.query.filter_by(username=userid).first()
    if item:
        item.name = username
        item.credit = credit
        item.audio_clone_times = audio_clone_times
        db.session.commit()
        return json.dumps({
            'code': 200,
            'status': 'true',
            'msg': '修改成功',
        })
    else:
        return json.dumps({
            'code': 404,
            'status': 'false',
            'msg': '修改失败，找不到该用户',
        })


# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     flash('Goodbye.')
#     return redirect(url_for('index'))

@app.route('/api/get_audios', methods=["POST"])
def get_audios():
    token = request.headers.get('token')
    userid = token
    page = int(request.form.get('page'))
    rows = int(request.form.get('rows'))
    us = User.query.filter_by(username=userid).first()
    data = AudioQueue.query.filter_by(username=userid).all()
    res = []
    start = (page - 1) * rows
    end = page * rows - 1
    for item in data[start:end]:
        obj = {
            'id': item.id,
            'created_time': item.created_time,
            'voice_id': item.voice_id,
            'prompt_url': item.prompt_url,
            'voice_name': item.voice_name
        }
        res.append(obj)
    return json.dumps({
        'code': 200,
        'status': 'true',
        'data': res,
        'audio_times': us.audio_clone_times,
        'delete_times': us.delete_clone_audio_times,
        'total': len(data),
        'msg': ''
    })


@app.route('/api/delete_audios', methods=["POST"])
@login_required
def delete_audios():
    token = request.headers.get('token')
    user = encode_token(token)
    userid = user.username
    id = request.form.get('id')
    voice_id = request.form.get('voice_id')
    us = User.query.filter_by(username=userid).first()
    data = AudioQueue.query.get(id)
    if data.username != userid:
        return json.dumps({
            'code': 403,
            'status': 'false',
            'msg': '不允许删除别人的视频！'
        })
    if us.delete_clone_audio_times < 1:
        return json.dumps({
            'code': 405,
            'status': 'false',
            'msg': '声音角色删除次数超过限制'
        })

    url = 'https://v1.reecho.cn/api/tts/voice/' + voice_id
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer sk-2e0aaf36a6d8897478d17785736f1386'}
    response = requests.delete(url, headers=headers, verify=True, stream=True)
    res = json.loads(response.text)
    if res['status'] == 200:
        us.delete_clone_audio_times -= 1
        db.session.delete(data)
        db.session.commit()
        return json.dumps({
            'code': 200,
            'status': 'true',
            'msg': '删除成功！'
        })
    else:
        return json.dumps({
            'code': 501,
            'status': 'false',
            'msg': '删除失败，请重试！'
        })


@app.route('/api/set_audios', methods=["POST"])
@login_required
def set_audios():
    token = request.headers.get('token')
    user = User.query.filter_by(username=token).first()
    userid = user.username
    audioList = AudioQueue.query.filter_by(username=userid).all()
    audioTimes = User.query.filter_by(username=userid).first()
    if len(audioList) >= audioTimes.audio_clone_times:
        return json.dumps({
            'code': 405,
            'status': 'false',
            'msg': '声音复刻次数超过限制'
        })
    obj = json.loads(request.get_data(as_text=True))
    name = obj['name']
    prompt = obj['prompt']
    url = 'https://v1.reecho.cn/api/tts/voice'
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer sk-2e0aaf36a6d8897478d17785736f1386'}
    params = {'name': name, 'modelVersion': 'v2.0', 'prompt': prompt}
    response = requests.post(url, headers=headers, json=params, verify=True, stream=True)
    res = json.loads(response.text)

    if res['status'] == 200:
        unprocessed = AudioQueue(
            id=int(db.session.query(db.func.max(AudioQueue.id)).scalar() or 0) + 1,
            username=userid,
            created_time=str(datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")),
            voice_id=res['data']['id'],
            prompt_url=res['data']['metadata']['prompts'][0]['playBackAudio'],
            voice_name=name
        )
        db.session.add(unprocessed)
        db.session.commit()
        return json.dumps({
            'code': 200,
            'status': 'true',
            'msg': '上传成功'
        })
    return json.dumps({
        'code': 500,
        'status': 'false'
    })


@app.route('/api/TTS/set_audios_v1', methods=["POST"])
def set_audios_v1():
    token = request.headers.get('Authorization')
    if not token:
        return json.dumps({'code': 401, 'status': 'false', 'msg': '身份验证失败!'})
    authorization = token[7:]
    this_user = UserVoiceCloneQueue.query.filter_by(userid=authorization).all()
    if len(this_user) == 0:
        flash('用户不存在')
        return json.dumps({'code': 401, 'status': 'false', 'msg': '用户不存在.'})
    obj = json.loads(request.get_data(as_text=True))
    userMessage = obj['userMessage']
    voice_id = obj['voice_id']
    cost = len(userMessage)
    item = UserVoiceCloneQueue.query.filter_by(userid=authorization).first()
    if item.credit_voice < cost:
        return json.dumps(
            {
                'code': 503,
                'status': 'false',
                'msg': '账号配音字数余额不足！'})
    # userMessage = request.form.get('userMessage')
    # voice_id = request.form.get('voice_id')
    url = 'https://v1.reecho.cn/api/tts/simple-generate'
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer sk-2e0aaf36a6d8897478d17785736f1386'}
    params = {'voiceId': voice_id, 'text': userMessage, 'stream': False}
    response = requests.post(url, headers=headers, json=params, verify=True, stream=True)
    res = json.loads(response.text)
    if res['status'] == 200:
        res_audio = res['data']['audio']
        credit_used = res['data']['credit_used']
        down_res = requests.get(res_audio)
        create_time = str(datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S"))
        dir_path = os.path.join("core/static/file_from_user", 'app', create_time)
        os.makedirs(dir_path, exist_ok=True)

        audio_path = os.path.join(dir_path, uuid.uuid4().hex + ".mp3")
        with open(audio_path, 'wb') as file:
            file.write(down_res.content)
        item.credit_voice -= cost
        db.session.commit()
        return json.dumps({
            'status': 200,
            'data': {
                'url': 'https://www.aiagen.cn' + audio_path[4:]
            },
            'message': '请求成功'
        })
    return json.dumps(res)


@app.route('/api/TTS/set_roles', methods=["POST"])
def set_roles():
    token = request.headers.get('Authorization')
    if not token:
        return json.dumps({'code': 401, 'status': 'false', 'msg': '身份验证失败!'})
    authorization = token[7:]
    this_user = UserVoiceCloneQueue.query.filter_by(userid=authorization).all()
    if len(this_user) == 0:
        flash('用户不存在')
        return json.dumps({'code': 401, 'status': 'false', 'msg': '用户不存在.'})
    obj = json.loads(request.get_data(as_text=True))
    name = obj['name']
    prompt = obj['prompt']
    url = 'https://v1.reecho.cn/api/tts/voice'
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer sk-2e0aaf36a6d8897478d17785736f1386'}
    params = {'name': name, 'modelVersion': 'v2.0', 'prompt': prompt}
    response = requests.post(url, headers=headers, json=params, verify=True, stream=True)
    res = json.loads(response.text)
    if res['status'] == 200:
        return json.dumps({
            'status': 200,
            'voice_id': res['data']['id'],
            'message': '上传成功'
        })
    return json.dumps(res)


@app.route('/api/TTS/get_userInfo', methods=["GET"])
def get_userInfo():
    token = request.headers.get('Authorization')
    if not token:
        return json.dumps({'code': 401, 'status': 'false', 'msg': '身份验证失败!'})
    authorization = token[7:]
    this_user = UserVoiceCloneQueue.query.filter_by(userid=authorization).all()
    if len(this_user) == 0:
        flash('用户不存在')
        return json.dumps({'code': 401, 'status': 'false', 'msg': '用户不存在.'})
    item = UserVoiceCloneQueue.query.filter_by(userid=authorization).first()
    return json.dumps({
        'status': 200,
        'data': {
            'credit': item.credit_voice
        },
        'message': '请求成功'
    })


@app.route('/api/TTS/delete_roles', methods=["POST"])
def delete_roles():
    token = request.headers.get('Authorization')
    if not token:
        return json.dumps({'code': 401, 'status': 'false', 'msg': '身份验证失败!'})
    authorization = token[7:]
    this_user = UserVoiceCloneQueue.query.filter_by(userid=authorization).all()
    if len(this_user) == 0:
        flash('用户不存在')
        return json.dumps({'code': 401, 'status': 'false', 'msg': '用户不存在.'})
    obj = json.loads(request.get_data(as_text=True))
    voice_id = obj['voice_id']
    url = 'https://v1.reecho.cn/api/tts/voice/' + voice_id
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer sk-2e0aaf36a6d8897478d17785736f1386'}
    response = requests.delete(url, headers=headers, verify=True, stream=True)
    res = json.loads(response.text)
    if res['status'] == 200:
        return json.dumps({
            'status': 200,
            'message': '删除成功'
        })
    return json.dumps(res)


@app.route('/api/set_chat_audio', methods=["GET", 'POST'])
@login_required
def set_chat_audio():
    token = request.headers.get('token')
    user = User.query.filter_by(username=token).first()
    userid = user.username

    data = ProcessQueue.query.filter_by(username=userid).all()
    obj = json.loads(request.get_data(as_text=True))
    text = obj['text']
    messageList = [
        {
            "role": "system",
            "content": """把这段对话文本转成json列表格式,列表项为person对话人,和text对话内容。首尾不要有任何格式，回答只保留json文本。输出样例如下:
[
  {
    "person": "Person A",
    "text": "Hi, how's it going?"
  },
  {
    "person": "Person B",
    "text": "Hey! I'm doing well, thanks. How about you?"
  },
  {
    "person": "Person A",
    "text": "Not bad, just been busy with work. What have you been up to?"
  },
  {
    "person": "Person B",
    "text": "Same here. I've been working on a new project that's been keeping me pretty occupied."
  }
]
          """
        },
        {
            "role": "user",
            "content": text
        }]
    param = {
        "prompt": "",
        "max_tokens": 2048,
        "temperature": 0.3,
        "top_p": 0.9,
        "model": "yi-lightning",
        "messages": messageList,
        "tools": None
    }
    url = 'https://api.lingyiwanwu.com/v1/chat/completions'
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 633158349771440d9054e705316ca0c3'}
    n = 0
    try:
        while n < 10:
            response = requests.post(url, headers=headers, json=param, verify=True, stream=True)
            res = response.text
            res = json.loads(res.replace('```json', '').replace('```', ''))
            res = res['choices'][0]['message']['content']
            res = json.loads(res)
            break
    except:
        n += 1
    create_time = str(datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S"))
    dir_path = os.path.join("core/static/file_from_user", user.username, create_time)
    os.makedirs(dir_path, exist_ok=True)
    mp3_files = []

    cmd = """
    ffmpeg  """
    for i in range(len(res)):
        output_path = os.path.join(dir_path, str(i) + '.wav')
        mp3_files.append(output_path)
        text = res[i]['text']

        if i % 2 == 0:
            tts_backend(text, output_path, voice_type="BV034_streaming")
        else:
            tts_backend(text, output_path, voice_type="BV056_streaming")
        cmd += """ -i """ + output_path
    output_path = os.path.join(dir_path, 'result_audio.wav')
    cmd = cmd + """   -filter_complex "[0:a][1:a][2:a]concat=n=""" + str(
        len(res)) + """:v=0:a=1[out]" -map "[out]" """ + output_path

    subprocess.call(cmd, shell=platform.system() != 'Windows')
    # concatenate_mp3_files(mp3_files, output_path)
    audio_url = output_path

    return json.dumps({
        'code': 200,
        'status': 'true',
        'msg': '请求成功',
        'data': {
            "url": audio_url,
            "data": res,
        }
    })


def generate_xml(ToUserName, FromUserName, CreateTime, Content):

    # 1. 先准备好回复的xml格式，后面只需要填充里面的字段即可
    output_xml = '''
    <xml>
        <ToUserName><![CDATA[%s]]></ToUserName>
        <FromUserName><![CDATA[%s]]></FromUserName>
        <CreateTime>%s</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[%s]]></Content>
    </xml>'''

    # 2. 通过 make_response 函数封装网络返回结构体
    response = output_xml % (FromUserName, ToUserName, str(int(time.time())), Content)
    # response.content_type = 'application/xml'
    return response


def setAnwser(text, MsgId):
    # messageList = [{
    #       "role": "system",
    #       "content": "回答尽量简便，尽快回复,回复除了纯文本和标点符号，不要带任何特殊字符。"
    #     },{
    #       "role": "user",
    #       "content": text
    #     }]
    # param = {
    #     "prompt": "",
    #     "max_tokens": 2048,
    #     "temperature": 0.3,
    #     "top_p": 0.9,
    #     "model": "yi-large",
    #     "messages":messageList,
    #     "tools": None
    #   }
    # #sk-OL2CeOdOK98uhuK1dbeAlA6ZePIWoSbj8iEWip02bwgLGD0A
    # url = 'https://api.lingyiwanwu.com/v1/chat/completions'
    # headers = {'Content-Type': 'application/json','Authorization': 'Bearer 633158349771440d9054e705316ca0c3'} 
    # response = requests.post(url, headers=headers,json=param, verify=False,stream=True)
    messageList = [{
        "role": "system",
        "content": "你是 Dimi，由 安玲恒鑫 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确，精简的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Dimi、安玲恒鑫 为专有名词，不可翻译成其他语言。"
    }, {
        "role": "user",
        "content": text
    }]
    param = {
        "prompt": "",
        "max_tokens": 2048,
        "temperature": 0.3,
        "top_p": 0.9,
        "model": "moonshot-v1-8k",
        "messages": messageList,
        "tools": None
    }
    # sk-OL2CeOdOK98uhuK1dbeAlA6ZePIWoSbj8iEWip02bwgLGD0A
    url = 'https://api.moonshot.cn/v1/chat/completions'
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer sk-OL2CeOdOK98uhuK1dbeAlA6ZePIWoSbj8iEWip02bwgLGD0A'}
    response = requests.post(url, headers=headers, json=param, verify=False, stream=True)
    res = response.text
    res = json.loads(res.replace('```json', '').replace('```', ''))
    res = res['choices'][0]['message']['content']
    item = WxPublicMsg.query.filter_by(msgId=MsgId).first()
    item.anwser = res.replace('\n', '').replace('**', '')
    db.session.commit()

def getAnswer(MsgId):
    n = 0
    ans = ''
    while n < 6:
        db.session.commit()
        db.session.close()
        # 创建一个新的会话
        db.session = db.create_scoped_session()
        time.sleep(1)
        item = WxPublicMsg.query.filter_by(msgId=MsgId).first()
        ans_c = item.anwser
        if len(ans_c) > 0:
            ans = ans_c
            break

        n += 1

    return ans


@app.route('/api/chat_anling', methods=['GET', 'POST'])
def chat_anling():
    if request.method == 'GET':
        params = request.args
        param = params.to_dict()
        # 打印参数到控制台
        print(param)
        # 将参数作为响应返回
        return str(param['echostr'])
    # 解析XML数据
    else:
        xml_data = request.data
        try:
            root = ET.fromstring(xml_data)
            # 在这里你可以对XML数据进行处理
            print(ET.tostring(root, encoding='unicode'))

            # 示例：获取XML中的某个元素的值
            # 假设XML结构为：<data><name>John</name></data>
            ToUserName = root.find('.//ToUserName').text
            FromUserName = root.find('.//FromUserName').text
            CreateTime = root.find('.//CreateTime').text
            MsgType = root.find('.//MsgType').text
            Content = root.find('.//Content').text
            MsgId = root.find('.//MsgId').text
            print(f"Name: {Content}")
            arr = WxPublicMsg.query.filter_by(msgId=MsgId).all()
            if len(arr) == 0:
                id = int(db.session.query(db.func.max(WxPublicMsg.id)).scalar() or 0) + 1
                new_job = WxPublicMsg(
                    id=id,
                    msgId=MsgId,
                    anwser=''
                )
                db.session.add(new_job)
                db.session.commit()
                thread = threading.Thread(target=setAnwser, args=(Content, MsgId))
                thread.start()

            res = getAnswer(MsgId)

            if res:
                xml_str = generate_xml(ToUserName, FromUserName, CreateTime, res)
                print(xml_str)
                return Response(xml_str, content_type='application/xml')
            else:
                return str('success')
        except ET.ParseError:
            return str('success')


@app.route('/api/create_payment_details', methods=['POST'])
def create_new_payment_details():
    payload = json.loads(request.get_data(as_text=True))

    new_payment_details = create_payment_details(payload)

    db.session.add(new_payment_details)
    db.session.commit()

    return json.dumps({
        'code': 200,
        'status': 'true',
        'msg': 'PaymentDetails created for customer: ' + payload['user_id'],
        'data': new_payment_details.id
    })


@app.route('/api/checkout_webhook', methods=['POST'])
def checkout_webhook():
    event = validate_stripe_webhook(request)

    if (event.type != 'payment_intent.created' and event.type != 'payment_intent.succeeded'
            and event.type != 'charge.succeeded' and event.type != 'checkout.session.completed' and event.type != 'charge.updated'):
        return

    payload = event['data']['object']

    try:
        new_webhook = create_webhook_record(event)

        if event.type == 'payment_intent.created':
            payment_intent_details = PaymentIntentDetails.query.filter_by(external_id = payload['id']).first()
            if payment_intent_details is None:
                new_payment_intent = create_payment_intent(event)
                db.session.add(new_payment_intent)

        elif event.type == 'payment_intent.succeeded':
            payment_intent_details = PaymentIntentDetails.query.filter_by(external_id = payload['id']).first()
            if payment_intent_details is not None:
                if payload['status'] == 'succeeded':
                    payment_intent_details.status = 1
                else:
                    payment_intent_details.status = 2
                payment_intent_details.latest_charge = payload['latest_charge']
                payment_intent_details.amount_received = payload['amount_received']
            else:
                new_payment_intent = create_payment_intent(payload)
                db.session.add(new_payment_intent)

        elif event.type == 'charge.succeeded':
            new_payment_charge_details = create_payment_charge_details(event)
            db.session.add(new_payment_charge_details)

        elif event.type == 'checkout.session.completed':
            payment_details = PaymentDetails.query.filter_by(id = payload['client_reference_id']).first()
            customer_details = payload['customer_details']
            payment_intent_details = PaymentIntentDetails.query.filter_by(external_id = payload['payment_intent']).first()

            if payment_details is not None:
                if payload['payment_status'] == 'paid':
                    payment_details.status = 1
                else:
                    payment_details.status = 2
                if payment_intent_details is not None:
                    payment_details.payment_intent_id = payment_intent_details.id
                else:
                    payment_details.payment_intent_id = payload['payment_intent']
                payment_details.amount = payload['amount_total']
                payment_details.currency = payload['currency']
                payment_details.payment_email = customer_details['email']
                payment_details.name = customer_details['name']
                payment_details.country = customer_details['address']['country']
                payment_details.postal_code = customer_details['address']['postal_code']

            checkout_session = stripe.checkout.Session.list_line_items(payload['id'])

            if checkout_session is not None:
                print(checkout_session['data'][0])
                lookup_key = checkout_session['data'][0]['price']['lookup_key']
                payment_details.product_type = lookup_key
                user = User.query.filter_by(id = payment_details.user_id).first()
                if lookup_key == 'starter':
                    user.credit += 100000
                    payment_details.credits += 100000
                elif lookup_key == 'professional':
                    user.credit += 500000
                    payment_details.credits += 500000
                else:
                    pass

        elif event.type == 'charge.updated':
            payment_charge_details = PaymentChargeDetails.query.filter_by(external_id = payload['id']).first()
            if payment_charge_details is not None:
                payment_intent_details = PaymentIntentDetails.query.filter_by(external_id = payload['payment_intent']).first()
                if payload['status'] == 'succeeded':
                    payment_charge_details.status = 1
                else:
                    payment_charge_details.status = 2
                if payment_intent_details is not None:
                    payment_charge_details.payment_intent_id = payment_intent_details.id
                payment_charge_details.amount_authorized = payload['payment_method_details']['card']['amount_authorized']
                payment_charge_details.amount_captured = payload['amount_captured']
                payment_charge_details.receipt_url = payload['receipt_url']

        else:
            print("Unhandled event: " + event.type)
            return

        db.session.add(new_webhook)

        db.session.commit()

    except SQLAlchemyError as e:
        print("e: " + json.dumps(e))
        db.session.rollback()

    return json.dumps({
        'code': 200,
        'status': 'true',
        'msg': 'Payment webhook processed',
        'webhook': event.type
    })


@app.route('/api/get_bill', methods=["GET", 'POST'])
def get_bill():
    token = request.headers.get('token')
    user = User.query.filter_by(username=token).first()
    data = PaymentDetails.query.filter_by(user_id=user.id).all()
    res = []
    total = len(data)
    for item in data:
        obj = {
            'id': item.id,
            'create_time': str(item.created_at),
            'price': item.amount,
            'add_credit': item.credits,
        }
        res.append(obj)
    return json.dumps({
        'code': 200,
        'status': 'true',
        'msg': '请求成功',
        'data': {
            "rows": res,
            "total": total
        }
    })
