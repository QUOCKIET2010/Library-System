import hashlib
from datetime import datetime
import random
import string

def make_hash(password):
    return hashlib.sha256(str(password).encode()).hexdigest()

def safe_parse_date(date_input):
    if isinstance(date_input, datetime): return date_input
    if not date_input: return None
    str_date = str(date_input).strip()
    formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
    for fmt in formats:
        try: return datetime.strptime(str_date, fmt)
        except ValueError: continue
    return datetime.now()

def get_captcha_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))