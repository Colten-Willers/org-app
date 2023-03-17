from flask import Flask, render_template, redirect, request, session, flash
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import pbkdf2_sha256
from other_functions import login_required

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config['SECRET_KEY'] = 'ultra_secret_key'

app.config['SESSION_TYPE'] = 'filesystem'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database2.db'

# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

Session(app)

class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(20), nullable=False)
    user_password = db.Column(db.String(20), nullable=False)
    user_email = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'User: {self.user_name}'

class prak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant = db.Column(db.String(20), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(800))
    user_name = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'participant: {self.participant}'

db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    if request.method == "POST":
        user_name = request.form.get('user_name')
        user_password = request.form.get('user_password')
        user_email = request.form.get('user_email')

        password_hash = pbkdf2_sha256.hash(str(user_password))

        user_data = user(user_name=user_name, user_password=password_hash, user_email=user_email)

        if user.query.filter_by(user_name=user_name).first():
            return render_template("apology.html", message="User already exists.")

        db.session.add(user_data)
        db.session.commit()

        return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    if request.method == "POST":
        user_name = request.form.get('user_name')
        user_password = request.form.get('user_password')

        if not user_name or not user_password:
            return render_template("apology.html", message="Must enter all data.")

        if user.query.filter_by(user_name=user_name).first():
            user_data = user.query.filter_by(user_name=user_name).first()
            if pbkdf2_sha256.verify(str(user_password), user_data.user_password): #str(user_data.user_password) == str(user_password)
                session['user_name'] = user_name
                flash("Succesfully logged in.")
                return render_template("index.html")
            return render_template("apology.html", message="Wrong Name or Password.")
        return render_template("apology.html", message="User doesn't exist.")

@login_required
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@login_required
@app.route("/data")
def data():
    prak_data_dict = dict()

    prak_data = prak.query.all()

    for record in prak_data:
        prak_data_dict[record.participant] = [record.rating, record.comment, record.user_name, record.id]

    if len(prak_data) == 0:
        return render_template("apology.html", message="No data recorded yet.")
    

    return render_template("data.html", data=prak_data_dict)

@login_required
@app.route("/add_data", methods=["GET", "POST"])
def add_data():
    if request.method == "GET":
        return render_template("add_data.html")
    
    if request.method == "POST":
        participant = request.form.get('participant')
        rating = request.form.get('rating')
        comment = request.form.get('comment')


        if not participant or not rating or not comment:
            return render_template("apology.html", message="Must enter all data.")
        
        new_entry = prak(participant=participant, rating=rating, comment=comment, user_name=session['user_name'])

        db.session.add(new_entry)
        db.session.commit()
        
        return redirect("/data")

@login_required
@app.route("/update_data", methods=["GET", "POST"])
def update_data():
    if request.method == "GET":
        return render_template("update_data.html")
    
    if request.method == "POST":
        print(request.form.get('Delete'))
        if request.form.get('Delete') == 'delete':
            # session['delete_id'] = id_t #request.form.get('delete_id')
            return redirect("/delete_data")

        rating = request.form.get('rating')
        comment = request.form.get('comment')
        user_id = request.form.get('user_id')


        if not rating or not comment:
            return render_template("apology.html", message="Must enter all data.")
        
        entry = prak.query.filter_by(user_name=session['user_name'], id=user_id).first()

        if not entry:
            return render_template("apology.html", message="Not your comment.")
        
        entry.rating = rating

        entry.comment = comment

        db.session.commit()
        
        return redirect("/data")

@login_required
@app.route("/delete_data", methods=["GET", "POST"])
def delete_data():
    if request.method == "GET":
        return render_template("delete_data.html")
    
    if request.method == "POST":
        user_id = request.form.get('user_id')

        if not user_id:
            return render_template("apology.html", message="Must enter  data.")
        
        check = prak.query.filter_by(user_name=session['user_name'], id=user_id).first()

        if not check:
            return render_template("apology.html", message="Not your comment.")

        entry = prak.query.filter_by(id=user_id).first()

        db.session.delete(entry)
        db.session.commit()

        flash("Succesfully deleted the data.")
        return redirect("/data")