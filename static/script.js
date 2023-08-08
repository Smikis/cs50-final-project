// In /add, sends the button click response, which is either "accept" or "deny"
// and then it either adds the user to friends or removes friend request
function send_request(answer, button){
    fetch("/inbox", {
        method: "POST",
        headers: {"content-type": "application/json"},
        mode: "same-origin",
        credentials: "same-origin",
        body: JSON.stringify({"answer": answer, "user": button.id})
    }).then(response => {
        if (response.status != 200)
            console.log("Something went wrong");
        else {
            var i = button.parentNode.parentNode.rowIndex;
            document.getElementById("dtBasicExample").deleteRow(i);

            if ((($('#dtBasicExample tr').length) - 1) === 0)
                document.getElementById("display").innerHTML= '<tr><td colspan="2" style="font-style: italic;">No requests received</td></tr>';
        }
    }).catch(error => {
        console.log(error);
    });
    display_notifications();
}
// Loads all users in /add
function load_all_users(){
    fetch("/search", {
        method: "POST",
        headers: {"content-type": "application/json"},
        mode: "same-origin",
        credentials: "same-origin"
    }).then(response => {
        if (response.status != 200) console.log('Failed to send fetch request in /add');
        else return response.json();
    }).then(data => {
        load_users(data);
    }).catch(error => {
        console.log(error);
    });
}
// Loads individual usernames whilst the user is typing 
function load_users(users){
    let html = '';
    users = users.split(" ");
    users.pop();
    
    if (users.length > 0)
        for (let i = 0; i < users.length; i++)
            html += '<tr style="text-align: center;"><td style="font-size: 20px">'+users[i]+'</td><td><button id="'+users[i]+'" onclick="send_id(this)" class="btn btn-outline-light" type="submit">Add to friends</button></td></tr>';  
    else html += '<tr><td colspan = "2"><div style="text-align: center; font-style: italic;">There are no users to display</div></td></tr>';
    document.getElementById("display").innerHTML = html;
}

// Sends user id to server after user has clicked "Add to friends" button which then
// adds a friend request to the database
function send_id(user){
    fetch("/add", {
        method: "POST",
        headers: {"content-type": "application/json"},
        mode: "same-origin",
        credentials: "same-origin",
        body: JSON.stringify(user.id)
    }).then(response => {
        if (response.status != 200) console.log("Couldn't send id");
        else {
            var buttn = document.getElementById(user.id);
            buttn.innerHTML = "Request sent";
        }
    }).catch(error => {
        console.log(error);
    });
}

function scroll_bottom(elem){ 
    elem.scrollTop = elem.scrollHeight; 
}

// Sends the message that the user has typed inside the message box
function send_message(user){
    // Send message to controller
    fetch("/messages", {
        method: "POST",
        headers: {"content-type": "application/json"},
        mode: "same-origin",
        credentials: "same-origin",
        body: JSON.stringify({
            user:user,
            message:document.getElementById('bot_message_box').value
        })
    }).then(response => {
        if (response.status != 200) console.log("Couldn't send message");
        else return;
    }).then (() => {
        var elem = document.getElementById('chat-window');
        var today = new Date();
        var hours = today.getHours();
        var minutes = today.getMinutes();

        if (minutes < 10)
                minutes = '0' + minutes;
        if (hours < 10)
            hours = '0' + hours;

        var time = hours + ":" + minutes;

        if (document.getElementById('bot_message_box').value != "")
            elem.innerHTML += '<div id="sent"><div id="message" class="msg-sent">'+document.getElementById('bot_message_box').value+'<div id="sent" style="font-size:12px;">'+time+'</div></div></div>';
        scroll_bottom(elem);
        document.getElementById('bot_message_box').value="";
    }).catch(error => {
        console.log(error);
    });
}

var scrolled = false;
// Displays all user's messages with the current friend selected
function show_messages(data){
    // Display messages sent and received with the user
    if (data['data'].length === 0)
        document.getElementById('chat-window').innerHTML = '<div style="text-align: center; font-style: italic;">There are no messages this user</div>';
    else{
        document.getElementById('chat-window').innerHTML = "";

        for (let i = 0; i < data['data'].length; i++){
            var date = new Date(data['data'][i]['date_sent']);

            var hours = date.getHours();
            var minutes = date.getMinutes();

            if (minutes < 10)
                minutes = '0' + minutes;
            if (hours < 10)
                hours = '0' + hours;

            var time = hours + ":" + minutes;

            if (data['data'][i]['receiver'] === data['this_user']) document.getElementById('chat-window').innerHTML += '<div id="received"><div id="message" class="msg-rec">'+data['data'][i]['message']+'<div id="received" style="font-size:12px;">'+time+'</div></div></div>';
            else document.getElementById('chat-window').innerHTML += '<div id="sent"><div id="message" class="msg-sent">'+data['data'][i]['message']+'<div id="sent" style="font-size:12px;">'+time+'</div></div></div>';
        }
    }
    // Add form elements required for sending messages
    if (scrolled === false){
        a = "'"+data['receiver']+"'";
        document.getElementById('message-box').innerHTML = '<input type="text" id="bot_message_box" class="form-control" autocomplete="off" maxlength="1000" placeholder="message"><button onclick="send_message('+a+'); return false;" class="btn btn-outline-light">Send</button>';
        scroll_bottom(document.getElementById('chat-window'));
        scrolled = true;
    }

    display_notifications();
}

function display_friends(data){
    document.getElementById('friend-list').innerHTML = '';
    if (data.friends.length === 0 || data.friends == '')
        document.getElementById('friend-list').innerHTML = '<div style="font-style: italic; padding: .5rem; text-align: center; color: #777;">Nothing here...</div><form style="padding: .5rem; text-align: center;" action="/add" method="GET"><input type="submit" class="btn btn-outline-light" value="Add Friends"></form>'
    else {
        for (var friend in data.friends){
            if (data['notifications'][friend] === 0)
                document.getElementById("friend-list").innerHTML += '<div id="friend_box"><div id="friend" onclick="display_messages(`'+data.friends[friend]+'`); scrolled = false; update_messages(`'+data.friends[friend]+'`);"><table style="text-align: center;"><tr><td><div id="pfp_circle"></div></td><td><div id="friend_username" style="margin: .5rem; color: coral">'+data.friends[friend]+'</div></td></tr></table></div></div>';
            else
                document.getElementById("friend-list").innerHTML += '<div id="friend_box"><div id="friend" onclick="display_messages(`'+data.friends[friend]+'`); scrolled = false; update_messages(`'+data.friends[friend]+'`);"><table style="text-align: center;"><tr><td><div id="pfp_circle"></div></td><td><div id="friend_username" style="margin: .5rem; color: coral">'+data.friends[friend]+' ('+data.notifications[friend]+')</div></td></tr></table></div></div>';
        }
        document.getElementById("friend-list").innerHTML += '<form style="padding: .5rem; text-align: center;" action="/add" method="GET"><input type="submit" class="btn btn-outline-light" value="Add Friends"></form>'
    }
}