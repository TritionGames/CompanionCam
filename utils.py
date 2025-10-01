import os
import json

def load_json(path):
    with open(path, 'r') as file:
        return json.load(file)

def load_file(path):
    with open(path, 'r') as file:
        return file.read()

def list_dir(path):
    files = []

    for file in os.listdir(path):
        if not os.path.isfile(os.path.join(path, file)):
            continue

        filename, filetype = file.split('.')
    
        if not filetype in ("png", "jpg"):
            continue

        files.append(file)

    return files