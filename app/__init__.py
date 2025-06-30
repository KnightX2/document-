from flask import Flask
from flask_mysqldb import MySQL

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your-secret-key-here'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'ArchiveSystem_v2'  

mysql = MySQL(app)

# Import routes after mysql is initialized
from . import routes

