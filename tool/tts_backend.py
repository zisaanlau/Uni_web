#coding=utf-8

'''
requires Python 3.6 or later
pip install requests
'''
import base64
import json
import uuid
import requests
def voice_clone_backend(answer,audio_path,voice_clone):
    url = 'https://v1.reecho.cn/api/tts/simple-generate'
    headers = {'Content-Type': 'application/json','Authorization': 'Bearer sk-2e0aaf36a6d8897478d17785736f1386'} 
    params = {'voiceId': voice_clone, 'text': answer,'stream':False}
    response = requests.post(url, headers=headers, json=params,verify=True,stream=True)
    res = json.loads(response.text)
    if res['status']==200:
        res_audio =  res['data']['audio']
        credit_used = res['data']['credit_used']
        down_res = requests.get(res_audio)
        with open(audio_path,'wb') as file:
            file.write(down_res.content)
        
def tts_backend(text,output_path,voice_type="BV007_streaming"):
    # 填写平台申请的appid, access_token以及cluster
    appid = "1444163919"
    access_token = "rF0RqwjRo4BcfOmacDfIGZo_a4AEfeSi"
    cluster = "volcano_tts"
    
    host = "openspeech.bytedance.com"
    api_url = f"https://{host}/api/v1/tts"

    header = {"Authorization": f"Bearer;{access_token}"}

    request_json = {
        "app": {
            "appid": appid,
            "token": "access_token",
            "cluster": cluster
        },
        "user": {
            "uid": "388808087185088"
        },
        "audio": {
            "voice_type": voice_type,
            "encoding": "mp3",
            "speed_ratio": 1.0,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query",
            "with_frontend": 1,
            "frontend_type": "unitTson"

        }
    }
    try:
        resp = requests.post(api_url, json.dumps(request_json), headers=header)
        # print(f"resp body: \n{resp.json()}")
        if "data" in resp.json():
            data = resp.json()["data"]
            file_to_save = open(output_path, "wb")
            file_to_save.write(base64.b64decode(data))
            
    except Exception as e:
        e.with_traceback()

if __name__ == "__main__":
    voice_type_list = [
    {
        "voice_type": "BV001_streaming",
        "name": "通用女声"
    },
    {
        "voice_type": "BV002_streaming",
        "name": "通用男声"
    },
    {
        "voice_type": "BV007_streaming",
        "name": "亲切女声"
    },
    {
        "voice_type": "BV019_streaming",
        "name": "重庆小伙"
    },
    {
        "voice_type": "BV005_streaming",
        "name": "活泼女声"
    },
    {
        "voice_type": "BV504_streaming",
        "name": "活力男声-Jackson"
    },
    {
        "voice_type": "BV115_streaming",
        "name": "古风少御"
    },
    {
        "voice_type": "BV701_streaming",
        "name": "擎苍"
    },
    {
        "voice_type": "BV051_streaming",
        "name": "奶气萌娃"
    },
    {
        "voice_type": "BV113_streaming",
        "name": "甜宠少御"
    },
    {
        "voice_type": "BV056_streaming",
        "name": "阳光男声"
    },
    {
        "voice_type": "BV033_streaming",
        "name": "温柔小哥"
    },
    {
        "voice_type": "BV102_streaming",
        "name": "儒雅青年"
    },
    {
        "voice_type": "BV522_streaming",
        "name": "气质女生"
    },
    {
        "voice_type": "BV119_streaming",
        "name": "通用赘婿"
    },
    {
        "voice_type": "BV524_streaming",
        "name": "日语男声"
    },
    {
        "voice_type": "BV213_streaming",
        "name": "广西表哥"
    },
    {
        "voice_type": "BV034_streaming",
        "name": "知性姐姐-双语"
    },
    {
        "voice_type": "BV021_streaming",
        "name": "东北老铁"
    },
    {
        "voice_type": "BV503_streaming",
        "name": "活力女声-Ariana"
    },
    {
        "voice_type": "BV700_streaming",
        "name": "灿灿"
    },
    {
        "voice_type": "BV705_streaming",
        "name": "炀炀"
    }
]
    new_items = []
    for item in voice_type_list:
        text = '星光不问赶路人,时光不负有心人。大概没去过的地方都叫远方,没得到的人都比较难忘'
        output_path = '/root/digital_human_web_Fengwei/core/static/audio/'+item['voice_type']+'.mp3'
        tts_backend(text,output_path,voice_type=item['voice_type'])
        print(item['voice_type'],'done')
        item['url'] = 'core/static/audio/'+item['voice_type']+'.mp3'
        new_items.append(item)
    print(new_items)
