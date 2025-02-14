import xbmc
import xbmcgui
import requests
import os
import time
import unicodedata

# Script constants
SCRIPT_NAME = 'Cortana Chat'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the script's directory
BASE_URL = 'https://bsky.social/xrpc/'
CHAT_URL = 'https://api.bsky.chat/xrpc/'
CHECK_INTERVAL = 5  # Interval in seconds to check for new messages and notifications
LOGIN_FILE = xbmc.translatePath('special://home/userdata/profiles/{}/login.txt'.format(xbmc.getInfoLabel('System.ProfileName')))
MESSAGES_FILE = xbmc.translatePath('special://home/userdata/profiles/{}/messages.txt'.format(xbmc.getInfoLabel('System.ProfileName')))
HANDLES_FILE = xbmc.translatePath('special://home/userdata/profiles/{}/handles.txt'.format(xbmc.getInfoLabel('System.ProfileName')))
PID_FILE = os.path.join(SCRIPT_DIR, "notifier.pid")
NOTIFICATIONS_FILE = xbmc.translatePath('special://home/userdata/profiles/{}/notifications.txt'.format(xbmc.getInfoLabel('System.ProfileName')))
NUDGE_FILE = os.path.join(SCRIPT_DIR, "nudge.mp3")  # Construct full path to nudge.mp3
LAST_NUDGE_TIME = 0

# Create PID file
def create_pid_file():
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

# Check if PID file exists
def check_pid_file():
    return os.path.exists(PID_FILE)

# Function to delete the PID file
def delete_pid():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
        xbmc.log("{}: PID file removed, stopping the notifier.".format(SCRIPT_NAME), xbmc.LOGINFO)
    else:
        xbmc.log("{}: PID file not found.".format(SCRIPT_NAME), xbmc.LOGERROR)

# Load login credentials
def load_credentials():
    if os.path.exists(LOGIN_FILE):
        with open(LOGIN_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                return lines[0].strip(), lines[1].strip()
    return None, None

# Authenticate with BlueSky using app password
def authenticate(username, app_password):
    url = BASE_URL + 'com.atproto.server.createSession'
    data = {
        'identifier': username,
        'password': app_password
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        xbmc.log("{}: Authentication successful".format(SCRIPT_NAME), xbmc.LOGINFO)
        return response.json()
    except requests.exceptions.RequestException as e:
        xbmc.log("{}: Authentication failed. Error: {}".format(SCRIPT_NAME, str(e)), xbmc.LOGERROR)
        return None

# Fetch notifications from BlueSky
def fetch_notifications(session):
    url = BASE_URL + 'app.bsky.notification.listNotifications'
    headers = {
        'Authorization': 'Bearer ' + session['accessJwt']
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json().get('notifications', [])
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok(SCRIPT_NAME, 'Failed to fetch notifications. Error: {}'.format(str(e)))
        return []

# Fetch conversations from BlueSky
def fetch_conversations(session):
    url = CHAT_URL + 'chat.bsky.convo.listConvos'
    headers = {
        'Authorization': 'Bearer ' + session['accessJwt']
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        convos = response.json().get('convos', [])
        return convos
    except requests.exceptions.RequestException as e:
        xbmc.log("{}: Failed to fetch conversations. Error: {}".format(SCRIPT_NAME, str(e)), xbmc.LOGERROR)
        return []

# Fetch messages for a conversation from BlueSky
def fetch_messages(session, convo_id):
    url = CHAT_URL + 'chat.bsky.convo.getMessages'
    headers = {
        'Authorization': 'Bearer ' + session['accessJwt']
    }
    params = {
        'convoId': convo_id
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        messages = response.json().get('messages', [])
        
        # Collect all DIDs to fetch profiles in bulk
        dids = {message['sender']['did'] for message in messages if 'sender' in message and 'did' in message['sender']}
        profiles = load_profiles()
        new_profiles = {did: fetch_profile(session, did) for did in dids if did not in profiles}
        profiles.update(new_profiles)
        save_profiles(new_profiles)
        
        # Ensure each message has the sender's handle
        for message in messages:
            if 'sender' in message and 'did' in message['sender']:
                sender_profile = profiles.get(message['sender']['did'], {})
                message['sender']['handle'] = sender_profile.get('handle', 'Unknown')

        # Sanitize message text
        for message in messages:
            if 'text' in message:
                message['text'] = sanitize_text(message['text'])

        return messages
    except requests.exceptions.RequestException as e:
        xbmc.log("{}: Failed to fetch messages. Error: {}".format(SCRIPT_NAME, str(e)), xbmc.LOGERROR)
        return []

# Fetch profile information from BlueSky
def fetch_profile(session, did):
    url = BASE_URL + 'app.bsky.actor.getProfile'
    headers = {
        'Authorization': 'Bearer ' + session['accessJwt']
    }
    params = {
        'actor': did
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        xbmc.log("{}: Failed to fetch profile. Error: {}".format(SCRIPT_NAME, str(e)), xbmc.LOGERROR)
        return {}

# Load profiles from file
def load_profiles():
    if os.path.exists(HANDLES_FILE):
        with open(HANDLES_FILE, 'r') as f:
            return {line.split(",")[0]: {"handle": line.split(",")[1].strip()} for line in f}
    return {}

# Save profiles to file
def save_profiles(profiles):
    with open(HANDLES_FILE, 'a') as f:
        for did, profile in profiles.items():
            f.write("{},{}\n".format(did, profile.get('handle', 'Unknown')))

# Load old message IDs from file
def load_old_message_ids():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

# Save new message ID to file
def save_message_id(message_id):
    with open(MESSAGES_FILE, 'a') as f:
        f.write(message_id + '\n')

# Load old notification IDs from file
def load_old_notification_ids():
    if os.path.exists(NOTIFICATIONS_FILE):
        with open(NOTIFICATIONS_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

# Save new notification ID to file
def save_notification_id(notification_id):
    if notification_id is not None:
        with open(NOTIFICATIONS_FILE, 'a') as f:
            f.write(str(notification_id) + '\n')

# Sanitize text by removing non-ASCII characters
def sanitize_text(text):
    return ''.join(char for char in text if ord(char) < 128)

# Check sys.argv for "stop" argument
def check_stop():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "stop":
        delete_pid()
        sys.exit()  # Exit after stopping

# Run the script normally
def main():
    # First, check if the script was called with "stop"
    check_stop()

    create_pid_file()  # Create the PID file at the start of the script
    xbmc.log("{}: Notifier started with PID {}".format(SCRIPT_NAME, os.getpid()), xbmc.LOGINFO)

    # Start your actual logic before checking the PID file
    username, app_password = load_credentials()
    if not username or not app_password:
        xbmc.log("{}: Please enter your BlueSky username and app password in login.txt.".format(SCRIPT_NAME), xbmc.LOGERROR)
        return

    session = authenticate(username, app_password)
    if not session:
        return

    old_message_ids = load_old_message_ids()
    old_notification_ids = load_old_notification_ids()
    user_did = session.get('did')

    while True:
        # Check if the PID file exists, exit if it's removed
        if not check_pid_file():
            xbmc.log("{}: Notifier PID file removed, exiting...".format(SCRIPT_NAME), xbmc.LOGINFO)
            break  # Exit the loop if the PID file is deleted

        # Fetch conversations and messages from BlueSky
        convos = fetch_conversations(session)
        for convo in convos:
            messages = fetch_messages(session, convo.get('id'))
            for message in messages:
                message_id = message.get('id')
                if message_id not in old_message_ids:
                    # Skip messages sent by the logged-in user
                    if message.get('sender', {}).get('did') == user_did:
                        continue

                    old_message_ids.add(message_id)
                    save_message_id(message_id)
                    user_handle = message.get('sender', {}).get('handle', 'Unknown')
                    text = message.get('text', 'No text').strip().lower()

                    # Check for nudge message
                    nudge_message = "{} has sent you a nudge!".format(user_handle).lower()
                    current_time = time.time()

                    if text == nudge_message:
                        if current_time - LAST_NUDGE_TIME >= 30:  # 30-second cooldown
                            xbmc.executebuiltin('PlayMedia("{}")'.format(NUDGE_FILE))
                            LAST_NUDGE_TIME = current_time  # Update last nudge time

                    xbmc.executebuiltin('Notification("{}", "{}", 5000, "")'.format(user_handle, sanitize_text(text)))

            # Fetch notifications
            notifications = fetch_notifications(session)
            for notification in notifications:
                notification_id = notification.get('cid')
                if notification_id not in old_notification_ids:
                    old_notification_ids.add(notification_id)
                    save_notification_id(notification_id)
                    reason = notification.get('reason', 'No Title')
                    author = notification.get('author', {})
                    user_handle = author.get('handle', 'Unknown user')
                    message = notification.get('record', {}).get('text', '')

                    notification_text = "{}: {}".format(reason.capitalize(), user_handle, message)
                    xbmc.executebuiltin('Notification("Cortana Chat", "{}", 5000, "N/A")'.format(sanitize_text(notification_text)))

            # Sleep for the specified interval before checking again
            xbmc.sleep(CHECK_INTERVAL * 1000)

        xbmc.log("{}: Notifier stopped.".format(SCRIPT_NAME), xbmc.LOGINFO)

# Run the main function
if __name__ == '__main__':
    main()
