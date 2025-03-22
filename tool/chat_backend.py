import requests
import json
def chat_backend(question,model_name=0,file=''):
    url = 'http://chat.s7.tunnelfrp.com/chat'
    file_type = file.split('.')[-1] if file else ''
    file_data = open(file, 'rb') if file else ''
    data = {'question':question, 'model_name':model_name,'file_type':file_type,}
    files = {'file': ("file", file_data)}
    response = requests.post(url, data=data, files=files, verify=False, stream=True)
    answer = response.text
    return answer
if __name__ == "__main__":
    question='20个字，简单说明一下，这个文档 讲了什么'
    file = '/root/杨子伟.pdf'
    res = chat_backend(question,model_name=2,file = file)
    print(res)