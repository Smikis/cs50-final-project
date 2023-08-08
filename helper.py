from functools import wraps
from flask import session, redirect
from DATABASE import SQL

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def get_friends():
    friends = SQL("""SELECT DISTINCT * FROM friends WHERE user1 = :user OR user2 = :user""", {'user':session["username"]})
    friend_list = []

    for friend in friends:
        friend_list.append(friend["user1"])
        friend_list.append(friend["user2"])

    # Remove duplicate names
    friend_list = list(dict.fromkeys(friend_list))

    if session["username"] in friend_list:
        friend_list.remove(session["username"])

    if len(friend_list) == 0:
        friend_list.append("")

    return friend_list

def get_notifications(friends):
    notific = []
    if len(friends) > 0:
        for friend in friends:
            notifs = SQL("""SELECT COUNT(seen) FROM messages WHERE seen = false AND sender = :sender AND receiver = :receiver""", {'sender':friend, 'receiver': session["username"]})
            notific.append(notifs[0]['count'])
    
    return notific