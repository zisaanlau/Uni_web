import requests
from requests.exceptions import Timeout
import json
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import io
import subprocess
import platform
# from PIL import Image
import base64
from tool.img_util import image2byte,byte2image
from core.models import User,ProcessQueue
from core import db
from tool.file_backend import get_file_type
import time
def get_first_frame(video,frame_path):

    videoCapture = cv2.VideoCapture(video)
    _, frame = videoCapture.read()
    cv2.imwrite(frame_path,frame)

def is_file_object(obj):
    return type(obj) != dict

def add_watermark(video_path,output_path,watermark_text):
    # 打开视频
    cap = cv2.VideoCapture(video_path)
    # 获取视频的宽度和高度
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 设置视频编码器和创建VideoWriter对象
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (width, height))
    font = ImageFont.truetype("core/static/image/video/STSong.ttf", 20)
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # 设置水印文本
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(image)
            text_width, text_height = draw.textsize(watermark_text, font=font)
            draw.text((width - text_width -10, height - text_height-10), watermark_text, fill=(255, 255, 255), font=font)
            out.write(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR))
    
            # 将帧写入输出视频
            #out.write(frame)
    
            # 显示帧（可选）
            # cv2.imshow('Video', frame)
    
            # 按'q'退出循环
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
      
      # 释放资源
    cap.release()
    out.release()
    cv2.destroyAllWindows()

def video_backend(
        id ,
        username ,
        cost,
        create_time ,
        input_file_path ,
        input_audio_path ,
        credit_cost ,
        input_text ,
        ):
    try:
        file_type = get_file_type(input_file_path)
        dir_path,basename = os.path.split(input_file_path)
        if file_type=="Image":
            output_img_path = input_file_path
        else:
            output_img_path = os.path.join(dir_path, basename.split('.')[0] + "_.jpg")
            get_first_frame(input_file_path,output_img_path)
        unprocessed = ProcessQueue(
            id = id,
            username = username,
            cost = cost,
            create_time = create_time,
            input_file_path = input_file_path,
            input_audio_path = input_audio_path,
            credit_cost = credit_cost,
            output_img_path = output_img_path[5:],
            output_video_path = '',
            input_text = input_text
            )
        db.session.add(unprocessed)
    
        db.session.commit()
        # print('ProcessQueue.process_running',ProcessQueue.process_running)
        if ProcessQueue.process_running==True:
            return
        need_process = ProcessQueue.query.filter(ProcessQueue.output_video_path == '').first()
        # print(need_process)
        while need_process:
            ProcessQueue.process_running = True
            input_file_path_w = need_process.input_file_path
            input_audio_path_w = need_process.input_audio_path
            # print('input_file_path',input_file_path)
            file_type = get_file_type(input_file_path_w)
            dir_path,basename = os.path.split(input_file_path_w)
            video_file_path = os.path.join(dir_path, basename.split('.')[0] + "_.mp4")
            video_file_path_new = os.path.join(dir_path, basename.split('.')[0] + "_new.mp4")
            first_frame = os.path.join(dir_path, basename.split('.')[0] + "_new.jpg")
            # watermark_video = os.path.join(dir_path, basename.split('.')[0] + "_w.mp4")
            # add_watermark('core/static/file_from_user/gandong/2024-07-22T13-49-38/adc7b32970b6418f8a44671204ce5e26_.mp4',watermark_video,'视频由锋伟网络AI数字人服务生成')
            try:
                url = ''             
                if file_type=='Image':
                    url = 'http://chat.s7.tunnelfrp.com/fomm_server'
                    files = {'img': ("img", open(input_file_path_w, 'rb')),
                            'audio': ("audio", open(input_audio_path_w, 'rb'))}        
                else:
                    url = 'http://chat.s7.tunnelfrp.com/retalk_server'
                    files = {'video': ("video", open(input_file_path_w, 'rb')),
                            'audio': ("audio", open(input_audio_path_w, 'rb'))}
                # print(file_type)            
                response = requests.post(url, timeout =(2100.05,2100.05),data=None, files=files, verify=False, stream=True)
                # print(response.content)
                # print(is_file_object(response.content))
                if( response.status_code == 200 and is_file_object(response.content)):
                    with open(video_file_path, 'wb') as f: # 保存视频文件
                        f.write(response.content)
                    watermark_video = os.path.join(dir_path, basename.split('.')[0] + "_w.mp4")
                    add_watermark(video_file_path,watermark_video,'视频由锋伟网络AI数字人服务生成')
                    command = "/usr/local/ffmpeg/bin/ffmpeg -loglevel quiet -i {} -i {} -acodec copy -vcodec h264 {} -y".format(watermark_video,input_audio_path_w,video_file_path_new)
                    subprocess.call(command, shell=platform.system() != 'Windows')
                    get_first_frame(video_file_path_new,first_frame)
                    # print(video_file_path_new)

                    #将要修改的值赋给title
                    need_process.output_img_path = first_frame[5:]
                    need_process.output_video_path = video_file_path_new[5:]
                else:
                    # print('视频制作超时,'+str(need_process.credit_cost)+'积分已返还')
                    need_process.output_img_path = 'error'
                    need_process.output_video_path = '非常抱歉，素材不合规,制作失败。视频所花费的'+str(need_process.credit_cost)+'积分已返还至您的账户中。'
                    item = User.query.filter_by(username = need_process.username).first()
                    item.credit += need_process.credit_cost
            except requests.exceptions.Timeout:
                # print('视频制作超时,'+str(need_process.credit_cost)+'积分已返还')
                need_process.output_img_path = 'error'
                need_process.output_video_path = '非常抱歉，素材不合规,制作失败。视频所花费的'+str(need_process.credit_cost)+'积分已返还至您的账户中。'
                item = User.query.filter_by(username = need_process.username).first()
                item.credit += need_process.credit_cost
            db.session.commit()
            need_process = ProcessQueue.query.filter(ProcessQueue.output_video_path == '').first()
        ProcessQueue.process_running = False
    except Exception as e:
        print(e)


if __name__ == "__main__":
    filename='/root/digital_human_web_online/core/static/image/demo1.jpeg'
    video_backend(filename)