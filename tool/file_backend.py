import os

def get_file_type(filename):
    filetype = os.path.splitext(filename)[1]  # 获取文件扩展名
    if filetype in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:  # 图片格式
        return "Image"
    elif filetype in ['.mp4', '.avi', '.mov', '.mkv', '.flv']:  # 视频格式
        return "Video"
    else:  # 无法识别的文件格式
        return "Unknown format"