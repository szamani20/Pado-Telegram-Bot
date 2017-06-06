import requests
import json
import os

# if not os.path.exists('./static/1'):
#     os.makedirs('./static/1')

a = (1, 2)
print(a[1])

# requests.get('http://localhost:5000/add_user')
# from delta_flask import db
# db.create_all()

# url = "http://localhost:5000/send_file"
# files = {'file': ('img.jpg', open('img.jpg', 'rb'), 'application/vnd.ms-excel', {'Expires': '0'})}
# data = {'username': 'Alice', 'image': 'img.jpg'}
# headers = {'Content-type': 'multipart/form-data'}
# r = requests.post(url, files=files, data=data)
# print(r.content)
# print(r.status_code)


# class Redos:
#     def __init__(self, val):
#         self.val = val
#
#     def __str__(self):
#         return self.val
#
#
# r = Redos('asd')
# s = json.JSONEncoder().encode(r.__dict__)
# r2 = Redos(**json.JSONDecoder().decode(s))
# print(s)
# print(r2)
