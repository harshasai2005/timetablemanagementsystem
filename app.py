from flask import Flask, render_template, request, jsonify, send_file, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import csv, io, os

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # REQUIRED for login sessions

# Configure the database URI. Using SQLite for local development flexibility.
# NOTE: If you switch back to PostgreSQL, uncomment your original line:
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://myuser:mypassword123@localhost:5432/timetabledb'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timetable.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ---------- USER MODEL ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)


# ---------- Timetable Models (Full Definitions) ----------
class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    availability = db.Column(db.String, default='')


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, unique=True, nullable=False)
    title = db.Column(db.String, nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    size = db.Column(db.Integer, default=30)
    faculty = db.relationship('Faculty')


class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weekday = db.Column(db.String, nullable=False)
    hour = db.Column(db.Integer, nullable=False)

    def key(self):
        return f"{self.weekday}-{self.hour}"


class ScheduledClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    timeslot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    course = db.relationship('Course')
    timeslot = db.relationship('TimeSlot')
    room = db.relationship('Room')


# ---------- Constants ----------
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
HOURS = list(range(9, 17))


# ---------- Helper ----------
def parse_availability(av_str):
    return set([s.strip() for s in av_str.split(',') if s.strip()])


# ---------- LOGIN PAGE ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for('home'))  # Redirects already logged-in users away from the login form

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user"] = user.username
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('home'))  # Successful login redirects to home route
        else:
            flash("Invalid username or password", "error")
            return render_template("login.html")

    return render_template("login.html")


# ---------- REGISTER PAGE ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
            return render_template("register.html")

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template("register.html")


@app.route('/home')
def home():
    if "user" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('login'))  # ACCESS CONTROL: If no session, redirect to login

    return render_template('home.html', username=session["user"])


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


# ---------- ROUTES ----------
@app.route('/')
def index():
    if "user" in session:
        return redirect(url_for('home'))  # If authenticated, show home interface
    return redirect(url_for('login'))  # If unauthenticated, redirect to login page


@app.route('/admin')
def admin():
    if "user" not in session:
        flash("Admin access requires login.", "warning")
        return redirect(url_for('login'))

    # In a production app, add role-based access control here
    return render_template('admin.html', username=session["user"])


@app.route('/generate', methods=['POST'])
def generate():
    # Placeholder for the complex timetable generation logic
    return jsonify({"status": "ok"})


@app.route('/timetable')
def timetable():
    if "user" not in session:
        flash("Please log in to view the timetable.", "warning")
        return redirect(url_for('login'))  # ACCESS CONTROL: If no session, redirect to login

    # Dummy timetable data (needs to be replaced with data queried from ScheduledClass model)
    timetable_data = [
        {"day": "Monday", "9:00": "Math 101 (Room A)", "10:00": "Physics 205 (Room B)", "11:00": "Break",
         "12:00": "Lunch"},
        {"day": "Tuesday", "9:00": "Chemistry 301 (Room C)", "10:00": "Math 101 (Room A)",
         "11:00": "English 100 (Room D)", "12:00": "Lunch"},
        {"day": "Wednesday", "9:00": "Physics 205 (Room B)", "10:00": "Chemistry 301 (Room C)", "11:00": "Break",
         "12:00": "Lunch"},
        {"day": "Thursday", "9:00": "Biology 101 (Room D)", "10:00": "Advanced Physics (Room B)",
         "11:00": "Seminar (Room A)", "12:00": "Lunch"},
        {"day": "Friday", "9:00": "CS Theory (Room C)", "10:00": "Elective 1 (Room A)", "11:00": "Review Session",
         "12:00": "Lunch"},
    ]

    return render_template("timetable.html", timetable=timetable_data, hours=HOURS, username=session["user"])


# ---------- Initialize and Run App ----------
if __name__ == "__main__":
    with app.app_context():
        # 1. Ensure all tables are created first
        db.create_all()

        # 2. Add a default test user if one doesn't exist
        if not User.query.filter_by(username='testuser').first():
            test_password = generate_password_hash('password123')
            test_user = User(username='testuser', email='test@example.com', password=test_password)
            db.session.add(test_user)
            db.session.commit()
            print("--- Test user 'testuser' with password 'password123' created. ---")

    app.run(debug=True)
