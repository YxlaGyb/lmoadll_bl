# -*- coding: utf-8 -*-
"""数据验证工具"""
import re

def isValidTimestamp(timestamp):
    return len(str(timestamp)) == 10 or len(str(timestamp)) == 13

def isValidURL(url):
    regex = re.compile(
        r"^(https?|http):\/\/([a-zA-Z0-9.-]+(:[a-zA-Z0-9.&%$-]+)*@)*((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}|([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.(com|edu|gov|int|net|org|biz|moe|info|name|pro|[a-zA-Z]{2}))(:[0-9]+)*(\/($|[a-zA-Z0-9.,?'\\+&%$#=~_-]+))*$"
    )
    return regex.match(url) is not None

def isValidEmail(email):
    regex = re.compile(r"^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{1,24}$")
    return regex.match(email) is not None

def isValidName(name):
    regex = re.compile(r"^[\u4e00-\u9fa5\w~_]{1,17}$")
    return regex.match(name) is not None

def isValidPassword(pwd):
    regex = re.compile(r"^(?=.*[a-zA-Z])(?=.*[0-9])[\w!@#$%^&*()+\-=\\/]{6,107}$")
    return regex.match(pwd) is not None

def isValidMailConfirmCode(code):
    regex = re.compile(r"^[a-zA-Z0-9]{7}$")
    return regex.match(code) is not None
