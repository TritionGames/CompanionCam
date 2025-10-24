import os
import subprocess
import json

import numpy as np
import pygame as pg

from datetime import datetime

def load_json(path):
    with open(path, 'r') as file:
        return json.load(file)

def load_file(path):
    with open(path, 'r') as file:
        return file.read()

def calculate_brightness(color):
    return (color.r * 2.99 + color.g * 0.587 + color.b * 0.114)

def format_seconds(timestamp):
    hours, remainder = divmod(int(timestamp), 3600)
    minutes, seconds = divmod(int(remainder), 60)
    miliseconds = int((timestamp % 1) * 100)
    return f"{minutes:02d}:{seconds:02d}.{miliseconds:02d}"

def convert_unix_to_date(unix_time):
    return datetime.fromtimestamp(unix_time).strftime('%d %b %Y %H:%M:%S')

def convert_to_mp3(path):
    name = f"{path[:-4]}.mp3"

    if os.path.isfile(name):
        os.system(f"rm {name}")
    
    os.system(f"ffmpeg -i {path} {name}")

def return_estimated_file_size(path):
    size = os.path.getsize(path)

    order = ['bytes', 'KB', 'MB', 'GB', 'how fucking big is this file??']
    index = 0

    while size > 1000 and index < len(order)-1:
        size /= 1000
        index += 1

    return f"{round(size, 2)} {order[index]}"

def get_creation_date(path):
    creation_timestamp = os.path.getctime(path)
    return datetime.fromtimestamp(creation_timestamp).strftime('%d %b %Y %H:%M:%S')  

def list_dir(path):
    files = []

    for file in os.listdir(path):
        if not os.path.isfile(os.path.join(path, file)):
            continue

        filename, filetype = file.split('.')[:2]
    
        if not filetype in ("png", "jpg", "webp", "mp4"):
            continue

        files.append(file)

    return files

def get_sharpness_index(surface: pg.Surface):
    array = pg.surfarray.array2d(surface)

    gy, gx = np.gradient(array)
    gnorm = np.sqrt(gx**2 + gy**2)
    sharpness = np.average(gnorm)
    
    return sharpness / 10000
