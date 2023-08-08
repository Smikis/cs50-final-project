# FireMessage
### Video Demo:  https://www.youtube.com/watch?v=atqHEVjnXaI
### Description:

FireMessage is a web-based chat application, which allows users to communicate through chat messages. It was made using `Python`, `JavaScript`, `HTML` and `CSS`.

# `app.py`

This file is the ***brains*** of the web-app. It contains all the nesccessary logic that runs the web-app.

This file is split into several sectors:
* Initial setup
* Sockets
* Authentication
* Message control
* Friend control
* Extras

At the very top are all the `imported` files. You can find all the requirements in `requirements.txt`

`Initial setup` contains the application's initialization, application's configuration, websocket and multithreading variable set-up.

`Sockets` contains functions, that are used for displaying user's friends, messages and notifications when they first open the page. Messages are emmited to the client-side where they are worked with.

`Authentication` contains functions used for authenticating users. *login()* and *register()* make use of `SQL` tables to check for users identity and make certains decisions according to the data received.

  * If in `login()`, an incorrect password or username is entered, an error is displayed to the user, notifying them that the data they entered is incorrect.

`Message control` includes everything that is needed for gathering and displaying messages sent/received by the user.

  * `stop_threads()` is executed, when the `/dashboard` route is exited. It kills the thread that is running in `dashboard()`.
  * `dashboard()` functionality is starting a background thread which runs a `while` loop to check for updates in the database. If changes have been found, a message is emmited to the client-side where notifications get updated.
  * `messages()` is used to insert the latest message sent into the database.
   
`Friend control` is where adding and searching for friends takes place.
  * `add()` is executed when `"Add friend"` is clicked in the `/add` route. The function checks for friend request records in the database and if none are found related to those two users, new data is inserted into the database.
  * `search()` is used for displaying users that have an account on the website AND are not yet in the user's friends list.
  * `inbox()` is used for displaying friend requests that the user has received and for accepting those requests. 
  
`Extras` includes pages that don't need any logic (`/about`, `/bug_report`) except for the `index` page.
* The `index` route, every time the main page is opened, starts a new `thread` (if it hasn't yet been started) which checks for database changes and emmits a message to the client-side if changes are found.
  
# `DATABASE.py`

This file is used for connecting to the database and has one custom function written by me.

``` python
def SQL(query, args={}):
    if "SELECT" in query:
        data = db.execute(text(query), args).mappings().all()
        return data
    else:
        db.execute(text(query), args)
```

This `SQL()` function allows me to use standart `SQL` syntax in my python queries since I don't quite like the `SQLAlchemy` syntax. The only thing it does is convert my `text query` into `SQLAlchemy` query and returns data if the `SELECT` keyword is used inside the query. If not, nothing is being `returned`.

# `helper.py`

This file is used for `helper` functions that are important, but don't require being in the main file.

`login_required` decorator requires the user to be logged in, in order to see other pages that require authentication. Example of usage:
``` python
@app.route("/foo")
@login_required
def foo():
  return bar
```

`get_friends()` is used to retrieve the list of friends that the user has. It does so by querying the DB for information and then re-formatting the data into a ``list of dicts``, instead of a ``SQLAlchemy object``.

`get_notifications()` retrieves the number of messages that the user hasn't read yet (marked as `seen = false` in the DB) for each friend.

# `script.js`

JavaScript was heavily used for client and backend communication, sending and receiving data to/from the controller.

`display_notifications()` receives `data`, which is the number of notifications (messages and friends requests) and then displays those numbers with `HTML` elements.

`send_request()` is used in `/inbox`. It sends a `POST` request to the controller. The request includes a body: the answer (either accept or decline) and the username of the user whose friend request was accepted.
When the response is received, the notifications on the page get updated and the row of the new friend is removed from the `/inbox` table.

`load_all_users()` is used in `/add`. It sends a `POST` request to the controller and waits for a response, which will have the list of all the users that need to be shown at the current moment. From there `load_users()` is called. 

`load_users` displays all the usernames that `load_all_users()` has provided in the function call.

`send_id()` is used in `/add`. It sends a `POST` request whose body content is the username of the user that should receive the friend request. When response is received, a success message is shown, displaying `"Request sent"`.

`scroll_bottom()` is a helper function, whose purpose is to keep the focus at the bottom of the element.

`sent_message()` is used for sending a new message in the chat window. It is executed when the `Send` button is clicked. 

`display_messages()` is used for displaying all the messages with the user that has been selected. It sends a `POST` request to the controller, to which the controller responds with the messages send and received. Then all the messages are appended to the `chat-window` element.

`display_friends()` is used for displaying all the user's friends on the side of `/dashboard`. 

# `styles.css`

This file includes all the styling elements that were used. For most of the design [bootstrap](https://getbootstrap.com/) was used, but for certain elements, the default bootstrap styles had to be edited. A custom scrollbar was created.

# `Challenges`

From the very begining I got struck with a problem of how to use `SQLAlchemy` data and how to make my life easier. After hours of research I came up with the `SQL()` function. It made working with the database so much easier and more enjoyable for me.

Another issue I came across was working with `threads`. Since I wanted to use `threads` for database checking, I needed to use Flask `session` in them, because that's where I was storing the data that was needed. The problem was that Flask `session` has a thing called `request context` and `application context`. Those two things were giving me trouble, because the new threads were outside of `request context`. The workaround that I found, was using `copy_current_request_context` decorator on the functions that were being used in `threads`. By doing so, I was able to finaly have background threads that do database checking.

## `Last thoughts`

It was a pleasure working on this project and it was a really good lesson to me of what coding really is and how it feels to sit for hours trying to debug my code and finally finding that stupid semicolon or indentation inconsistency which was causing all the program to crash :-).