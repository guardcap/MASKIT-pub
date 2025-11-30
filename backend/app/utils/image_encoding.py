import base64 
from PIL import Image
import io 

def base64_encoding(path:str):
    with open(path, 'rb') as img:
        encodingimg=base64.b64encode(img.read())
    imgformat=img.splite(".")[-1]
    