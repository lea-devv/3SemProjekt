from flask import Flask, flash, render_template, request, url_for, redirect
from flask_login import current_user, LoginManager, UserMixin, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from data_generation import get_chair_data
#from data_visualization import show_user_chair_data

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite"
app.config["SECRET_KEY"] = "grafisk_design"
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
db.init_app(app)

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    rfid_uuid = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(user_id)

@app.route("/")
def home():
    return redirect(url_for("index"))

@app.route("/index")
def index():
    if current_user.is_authenticated:
        return render_template('logged_in/index.html')
    else:
        return render_template('logged_out/index.html')

@app.route("/users")
@login_required
def users():
    users = Users.query.all()
    for user in users:
        print(user.rfid_uuid)
    print(users)
    return render_template('users.html', users=users)

@app.route("/co2")
def co2():
    if current_user.is_authenticated:
        return render_template('logged_in/co2.html')
    else:
        return render_template('logged_out/co2.html')

@app.route("/chair", methods=["GET", "POST"])
@login_required
def chair():
    user_chair_data = ""
    if request.method == "POST":
        username = request.form.get("user_search")
        user = Users.query.filter_by(username=username).first()
        if user is not None:
            user_chair_data = get_chair_data(user.rfid_uuid)           
        else:
            user_chair_data = "User does not exist in this database"
    return render_template('chair.html', user_chair_data=user_chair_data)

# Register site
@app.route('/register', methods=["GET", "POST"])
@login_required
def register():
    if request.method == "POST":
        hashed_password = bcrypt.generate_password_hash(request.form.get("password")).decode('utf-8')
        user = Users(username=request.form.get("username"), password=hashed_password, rfid_uuid=request.form.get("rfid_uuid"))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("register.html")

# Login site
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = Users.query.filter_by(username=request.form.get("username")).first()
        if user is None:
            flash("user does not exist")
            return render_template("login.html")
        if bcrypt.check_password_hash(user.password, request.form.get("password")):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash('Incorrect username or password')
    return render_template("login.html")

@app.route("/authentication")
def authentication():
    return render_template("authentication.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("authentication"))

@app.errorhandler(401)
def page_not_found(e):
    return redirect(url_for("authentication"))
    
@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for("authentication"))

if __name__ == '__main__':
    app.run(host='0.0.0.0')
