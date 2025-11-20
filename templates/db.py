from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)

# PostgreSQL connection string
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:yourpassword@localhost:5432/mydb"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
