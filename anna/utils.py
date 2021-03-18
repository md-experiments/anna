import string
import os
from hashlib import sha256, md5
import datetime
import yaml

def read_yaml(path):
    with open(path) as file:
        read_configs = yaml.load(file, Loader=yaml.FullLoader)
    return read_configs

def files_in_dir(path):
    fls = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
    fls = [os.path.join(path,f) for f in fls]
    return fls

def remove_punctuation(s):
    return s.translate(str.maketrans('', '', string.punctuation))

def normalize_name(text):
    return remove_punctuation(text).lower().replace(' ','_')

def hash_text(txt,mode = 'md5'):
    """
    Defaults md5, also takes sha256. Converts input to string
    >>> hash_text('hey')
    '6057f13c496ecf7fd777ceb9e79ae285'    
    >>> hash_text('hey',mode = 'sha256')
    'fa690b82061edfd2852629aeba8a8977b57e40fcb77d1a7a28b26cba62591204'
    >>> hash_text(1,mode = 'md5')
    'c4ca4238a0b923820dcc509a6f75849b'

    """
    
    if not isinstance(txt,str):
        txt = str(txt)
    txt_bytes = bytes(txt, 'utf-8')
    if mode == 'md5':
        txt_hash = md5(txt_bytes.rstrip()).hexdigest()
    elif mode == 'sha256':
        txt_hash = sha256(txt_bytes.rstrip()).hexdigest()
    return txt_hash