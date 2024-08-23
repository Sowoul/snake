import eventlet
eventlet.monkey_patch(thread=True, time=True)
from random import randint
from flask_socketio import SocketIO, emit, join_room
from flask import Flask, render_template, request, url_for, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from string import ascii_uppercase
from random import choice
from snake import Snake, Board

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"
app.config["SECRET_KEY"] = "OJASWA"
socket = SocketIO(app, async_mode="eventlet")
db = SQLAlchemy(app)

class User(db.Model):
    name = db.Column(db.String(16), primary_key=True)
    pswd = db.Column(db.String(200))

    def __init__(self, name, pswd):
        self.name = name
        self.pswd = pswd

rooms = {}

def gen_room(ln):
    while True:
        temp = "".join(choice(ascii_uppercase) for _ in range(ln))
        if temp not in rooms:
            return temp

@app.route("/")
def index():
    username = session.get("username", "")
    room = session.get("room", "")
    if (
        room not in rooms
        or username == ""
        or db.session.query(User).filter_by(name=username).first() is None
    ):
        return redirect(url_for("login"))
    return redirect(url_for("game"))

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        room = request.form.get("room", "")
        if room == "":
            room = gen_room(8)
            rooms[room] = {
                "members": 0,
                "board": Board(),
                "snakes": {},
            }
        existing = db.session.query(User).filter_by(name=username).first()
        if existing is None:
            return render_template("login.html", error="The given user does not exist")
        if not check_password_hash(existing.pswd, password):
            return render_template(
                "login.html", error="The entered password is incorrect"
            )
        session["username"] = username
        session["room"] = room
        rooms[room]["members"] += 1
        if len(rooms[room]["snakes"]) == 0:
            rooms[room]["board"].gen_item()
        return redirect(url_for("game"))
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if db.session.query(User).filter_by(name=username).first() is not None:
            return render_template("signup.html", error="The username is taken")
        if " " in username or len(username) < 4 or len(username) > 16:
            return render_template(
                "signup.html", error="The entered username is not valid"
            )
        newuser = User(username, generate_password_hash(password))
        db.session.add(newuser)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/game")
def game():
    username = session.get("username", "")
    room = session.get("room", "")
    if username == "" or room == "":
        return redirect(url_for('login'))
    if username not in rooms[room]["snakes"]:
        snake_id = len(rooms[room]["snakes"])
        snake = Snake(snake_id)
        rooms[room]["snakes"][username] = snake
        rooms[room]["board"].add_snake(snake)
    return render_template("game.html", room=room)

@socket.on('connect')
def connected():
    room = session.get("room", "")
    if room in rooms:
        join_room(room)
        emit('update', {"board": rooms[room]["board"].to_list()})

@socket.on("move")
def handle_move(data):
    room = session.get("room", "")
    username = session.get("username", "")
    if room in rooms and username in rooms[room]["snakes"]:
        snake = rooms[room]["snakes"][username]
        direction = data.get("direction")
        direction_map = {
            "up": (-1, 0),
            "down": (1, 0),
            "left": (0, -1),
            "right": (0, 1)
        }
        board=rooms[room]["board"]
        if direction in direction_map:
            try:
                snake.change_direction(direction_map[direction])
                snake.move(board)
                emit("update", {"board": board.to_list()}, broadcast=True, room=room)
            except Exception as e:
                for i,j in snake.body:
                    board.board[i][j]=4
                    board.count+=1
                emit("death", {"dead":username, "board":board.to_list()}, broadcast=True, room=room)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socket.run(app=app, host='0.0.0.0', port=8000, debug=True)
