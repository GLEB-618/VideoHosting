from flask import Flask

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.secret_key = 'I-do-not-know-what-to-write-here-lol'

from app import routes