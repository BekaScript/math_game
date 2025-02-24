from flask import Flask, request, render_template, jsonify, redirect, url_for
from flask_cors import CORS
from random import randint
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
CORS(app)
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    correct = db.Column(db.Integer, default=0)
    incorrect = db.Column(db.Integer, default=0)
    question_count = db.Column(db.Integer, default=0)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

ops = "+-"

@app.route("/")
@login_required
def entrance():
    return render_template("game.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400
        
        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        return jsonify({"message": "Registration successful"}), 200
    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('entrance'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify({"message": "Login successful"}), 200
        return jsonify({"error": "Invalid username or password"}), 401
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/get_question")
@login_required
def generate_question():
    try:
        first = randint(0, 100)
        second = randint(0, 100)
        first, second = max(first, second), min(first, second)
        op = ops[randint(0, 1)]
        question = f'{first}{op}{second}'
        current_user.question_count += 1
        db.session.commit()
        return jsonify({"question": question})
    except:
        return jsonify({"error": "Server error"}), 500

@app.route('/check_result')
@login_required
def check_result():
    try:
        answer = int(request.args.get("answer"))
        question = request.args.get("question")
        
        # Add spaces around operator for eval
        question = question.replace("+", " + ").replace("-", " - ")
        correct_answer = eval(question)
        
        if answer == correct_answer:
            current_user.correct += 1
            db.session.commit()
            return jsonify({"correct": True})
        current_user.incorrect += 1
        db.session.commit()
        return jsonify({"correct": False})
    except Exception as e:
        print(f"Error: {str(e)}")  # For debugging
        return jsonify({"error": "Server error"}), 500

@app.route('/stats')
@login_required
def get_stats():
    return jsonify({
        "username": current_user.username,
        "correct": current_user.correct,
        "incorrect": current_user.incorrect,
        "question_count": current_user.question_count
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080)