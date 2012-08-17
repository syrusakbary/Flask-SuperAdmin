from flask import Flask
from flask.ext.superadmin import Admin


app = Flask(__name__)

admin = Admin(app)
app.run()
