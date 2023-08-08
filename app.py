import ctypes
from time import sleep
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, session, request, redirect, flash, jsonify, copy_current_request_context
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import threading

from DATABASE import SQL # Imports a function to use SQL queries
from helper import get_notifications, login_required, get_friends # Additional funtions that help make the main functions cleaner

# ---------------------------------------------------------Initial Setup-------------------------------------------------------

# Initiate the application
app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Store session information in filesystem
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initiate a websocket
socketio = SocketIO(app)

# Intiate variables used for multithreading
index_thread = None
index_lock = threading.Lock()

dashboard_thread = None
dashboard_lock = threading.Lock()

messages_thread = None
messages_lock = threading.Lock()

# ---------------------------------------------------------Initial Setup-------------------------------------------------------

# ---------------------------------------------------------Sockets-------------------------------------------------------

@socketio.on('display_friends')
def update_friends():
    emit('response', {'friends': session["friends"], 'notifications': session["notifications"]})

@socketio.on('display_notifications')
def display_notifications():
    emit('new_notifications', {'inv_count': session['inv_count'], 'msg_count': session['msg_count']})

@socketio.on('display_messages')
def display_messages(user):
    messages = SQL("""SELECT message, receiver, date_sent, seen FROM messages WHERE sender = :sender AND receiver = :receiver OR sender = :receiver AND receiver = :sender ORDER BY date_sent""", {'sender': str(user), 'receiver':session['username']})
        
    SQL("""UPDATE messages SET seen = true WHERE sender = :sender AND receiver = :receiver""", {'sender': str(user), 'receiver':session['username']})

    if messages:
        data = [dict(r) for r in messages]
        _data = []
        for datas in data:
            datas['date_sent'] = datas['date_sent'].isoformat()
            _data.append(datas)
        data = _data
    else:
        data = []

    socketio.emit('messages_response', {'data': data, 'this_user':str(session['username']), 'receiver': user})

@socketio.on('update_messages')
def update_messages(user):
    global messages_thread

    if messages_thread == None:
        with messages_lock:
            messages_lock = threading.Thread(target=messages, daemon=True)
            messages_lock.start() # finished here

    emit('updated_messages', user)

# ---------------------------------------------------------Sockets-------------------------------------------------------

# ---------------------------------------------------------Authentification-------------------------------------------------------

# Logs the user into the website
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        # Check username
        if not request.form.get("username"):
            return render_template("login.html", error='Please enter your username')
        # Check password
        if not request.form.get("password"):
            return render_template("login.html", error='Please enter your password')

        user_info = SQL("SELECT * FROM users WHERE username = :username", {"username":request.form.get("username")})

        # Checks if the user is not in database or if the password hash doesn't match
        if len(user_info) != 1 or not check_password_hash(user_info[0]["pwd_hash"], request.form.get("password")):
            return render_template("login.html", error='Invalid username or password')
        
        # Store useful data in the session
        session["user_id"] = user_info[0]["id"]
        session["username"] = user_info[0]["username"]

        _friends = []

        for friend in get_friends():
            _friends.append(friend)

        if " " in _friends:
            _friends.remove("")

        session["friends"] = _friends

        _notifications = []

        for notification in get_notifications(_friends):
            _notifications.append(notification)

        session["notifications"] = _notifications

        inv_count = SQL("""SELECT COUNT(receiver) FROM friend_requests WHERE receiver = :receiver""", {"receiver":session["username"]})
        inv_count = inv_count[0]["count"]
        msg_count = SQL("""SELECT COUNT(seen) FROM messages WHERE receiver = :receiver AND seen = false""", {"receiver":session["username"]})
        msg_count = msg_count[0]["count"]

        session['inv_count'] = inv_count
        session['msg_count'] = msg_count

        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check for email
        if not request.form.get("email"):
            return render_template("register.html", error='Please enter your email address')
        # Check for username
        if not request.form.get("username"):
            return render_template("register.html", error='Please enter your username')
        # Check for password
        if not request.form.get("password"):
            return render_template("register.html", error='Please enter your password')
        # Check for password match
        if not request.form.get("confirm") or request.form.get("password") != request.form.get("confirm"):
            return render_template("register.html", error='Passwords must match')

        user_info = SQL("SELECT * FROM users WHERE username = :username", {"username":str(request.form.get("username"))})

        if len(user_info) == 0:
            # Insert user into DB
            SQL("""INSERT INTO users (email, username, pwd_hash) VALUES (:email, :username, :pwd_hash)""",
                {"email":str(request.form.get("email")), "username":str(request.form.get("username")), "pwd_hash":str(generate_password_hash(request.form.get("password")))})
            
            flash('Successfully registered')
            return redirect("/register")
        else:
            return render_template("register.html", error='This user already exists')
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    global index_thread, dashboard_thread

    items = threading.enumerate()

    for thread in items:
        if thread == index_thread:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident),ctypes.py_object(thread))
            index_thread = None
        elif thread == dashboard_thread:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident),ctypes.py_object(thread))
            dashboard_thread = None

    return redirect("/")

# ---------------------------------------------------------Authentification-------------------------------------------------------

# ---------------------------------------------------------Message control-------------------------------------------------------

@app.route("/stop_threads", methods=["GET", "POST"])
def stop_threads():
    items = threading._active.items()
    for id, thread in items:
        if thread == dashboard_thread:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(id),ctypes.py_object(thread))
    return "OK"

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    global dashboard_thread
    @copy_current_request_context
    def user_update_messages():
        while True:
            try:
                notifs = get_notifications(session["friends"])
                if notifs != session["notifications"]:
                    session["notifications"] = notifs
                    socketio.emit('response', {'friends': session["friends"], 'notifications': session["notifications"] })
                sleep(5)
            except:
                break
    
    dashboard_thread = threading.Thread(target=user_update_messages, daemon=True)
    dashboard_thread.start()

    return render_template("dashboard.html")

@app.route("/messages", methods=["POST", "GET"])
def messages():
    if request.method == 'POST':
        data = request.get_json()
        if data['message'] and data['user']:
            SQL("""INSERT INTO messages (sender, receiver, message) VALUES(:sender, :receiver, :message)""", {'sender':session['username'], 'receiver': data['user'], 'message':data['message']})
    return "OK", 200

# ---------------------------------------------------------Message control-------------------------------------------------------

# ---------------------------------------------------------Friend control-------------------------------------------------------

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == 'POST':
        # Get data from client-side
        data = request.get_json()

        count = SQL("""SELECT * FROM friend_requests WHERE sender = :sender AND receiver = :receiver""", {"sender":str(session["username"]), "receiver":str(data)})
        
        # Check if the user hasn't already sent a request to this person
        if count == 0 or not count:
            SQL("""INSERT INTO friend_requests (sender, receiver) VALUES (:sender, :receiver)""", {"sender":str(session["username"]), "receiver":str(data)})

        return "OK"
    else:
        return render_template("add.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == 'POST':

        users = SQL("SELECT username FROM users WHERE username != :user_name AND username NOT IN :friends ORDER BY LENGTH(username), username ASC",{'user_name':session['username'], 'friends':tuple(get_friends())})

        usernames = ""

        # Build username string
        for user in users:
            usernames += str(user["username"]) + " "

        return jsonify(usernames)

    # Check for arguments
    if request.args.get("q"):
        username = '%' + request.args.get("q") + '%'

        # Check that the usernames that are outputed don't include the user himself or his friends
        users = SQL("SELECT username FROM users WHERE username LIKE :username AND username != :user_name AND username NOT IN :friends ORDER BY LENGTH(username), username ASC", {"username":username, "user_name":session["username"], "friends":tuple(get_friends())})
        usernames = ""

        # Build username string
        for user in users:
            usernames += str(user["username"]) + " "

        # Send string to js
        return jsonify(usernames)

    # Send empty string
    else:
        return jsonify("")

@app.route("/inbox", methods=["POST", "GET"])
@login_required
def inbox():
    # Get users that sent a friend request
    if request.method == "POST":
        data = request.get_json()
        if data['answer'] == 'accept':
            # Add users as friends if the request was 'accept'
            SQL("""INSERT INTO friends (user1, user2) VALUES (:user1, :user2)""", {'user1':session["username"], 'user2':data["user"]})

            _friends = session['friends']

            _friends.append(data['user'])

            session['friends'] = _friends

        # Delete information from the friend request table
        SQL("""DELETE FROM friend_requests WHERE receiver = :receiver AND sender = :sender""", {'receiver':session["username"], 'sender':data["user"]})

        inv_count = SQL("""SELECT COUNT(receiver) FROM friend_requests WHERE receiver = :receiver""", {"receiver":session["username"]})
        inv_count = inv_count[0]["count"]
        msg_count = SQL("""SELECT COUNT(seen) FROM messages WHERE receiver = :receiver AND seen = false""", {"receiver":session["username"]})
        msg_count = msg_count[0]["count"]
        
        session['msg_count'] = msg_count
        session['inv_count'] = inv_count

        socketio.emit('display_notifications')

    received_requests = SQL("""SELECT sender FROM friend_requests WHERE receiver = :receiver""", {"receiver":str(session["username"])})

    return render_template("inbox.html", requests = received_requests)

# ---------------------------------------------------------Friend control-------------------------------------------------------

# ---------------------------------------------------------Extras-------------------------------------------------------

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/bug_report")
def bug_report():
    return render_template("bug_report.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/")
def index():
    global index_thread
    @copy_current_request_context
    def user_update_notif():
        while True:
            try:
                inv_count = SQL("""SELECT COUNT(receiver) FROM friend_requests WHERE receiver = :receiver""", {"receiver":session["username"]})
                inv_count = inv_count[0]["count"]
                msg_count = SQL("""SELECT COUNT(seen) FROM messages WHERE receiver = :receiver AND seen = false""", {"receiver":session["username"]})
                msg_count = msg_count[0]["count"]
                if inv_count != session['inv_count'] or msg_count != session['msg_count']:
                    session['inv_count'] = inv_count
                    session['msg_count'] = msg_count
                    socketio.emit('new_notifications', {'inv_count': session['inv_count'], 'msg_count': session['msg_count']})
                sleep(5)
            except:
                break

    if index_thread != None:
        items = threading.enumerate()
        for item in items:
            if item == index_thread:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(item.ident),ctypes.py_object(index_thread))
    else:
        with index_lock:
            index_thread = threading.Thread(target=user_update_notif, daemon=True)
            index_thread.start()

    return render_template("index.html")
# ---------------------------------------------------------Extras-------------------------------------------------------
