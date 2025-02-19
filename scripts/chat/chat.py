# Cortana Chat v2.0 by faithvoid - https://github.com/faithvoid/script.cortanachatv2

import xbmc
import xbmcgui
import requests
import os
import sys
import json
import datetime
import re
from datetime import timedelta
import time

# BlueSky API endpoints
BASE_URL = 'https://bsky.social/xrpc/'
CHAT_URL = 'https://api.bsky.chat/xrpc/'
GAMES_FILE = xbmc.translatePath('Q://games.txt')
HANDLES_FILE = xbmc.translatePath('special://home/userdata/profiles/{}/handles.txt'.format(xbmc.getInfoLabel('System.ProfileName')))

# Load login credentials
def load_credentials():
    login_file = xbmc.translatePath('special://home/userdata/profiles/{}/login.txt'.format(xbmc.getInfoLabel('System.ProfileName')))
    if os.path.exists(login_file):
        with open(login_file, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                return lines[0].strip(), lines[1].strip()
    return None, None

# Authenticate with BlueSky
def authenticate(username, app_password):
    url = BASE_URL + 'com.atproto.server.createSession'
    data = {'identifier': username, 'password': app_password}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok('Cortana Chat', 'Authentication failed: ' + str(e))
        return None

# Fetch home feed
def fetch_home_feed(session, cursor=None):
    url = BASE_URL + 'app.bsky.feed.getTimeline'
    headers = {'Authorization': 'Bearer ' + session['accessJwt']}
    params = {'limit': 25}
    if cursor:
        params['cursor'] = cursor
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        feed = data.get('feed', [])
        next_cursor = data.get('cursor', None)
        
        dids = {post['post']['author']['did'] for post in feed if 'post' in post and 'author' in post['post'] and 'did' in post['post']['author']}
        profiles = fetch_profiles(session, dids)
        
        for post in feed:
            author = post.get('post', {}).get('author', {})
            if 'did' in author:
                author['handle'] = profiles.get(author['did'], 'Unknown')
        
        return feed, next_cursor
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok('Cortana Chat', 'Failed to fetch home feed: ' + str(e))
        return [], None

# Fetch user profile to resolve handle
def fetch_profile(session, did):
    handle = read_handle_from_file(did)
    if handle:
        return handle
    
    url = BASE_URL + 'app.bsky.actor.getProfile'
    headers = {'Authorization': 'Bearer ' + session['accessJwt']}
    params = {'actor': did}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        handle = response.json().get('handle', 'Unknown')
        write_handle_to_file(did, handle)
        return handle
    except requests.exceptions.RequestException:
        return 'Unknown'

# Fetch user profiles in bulk
def fetch_profiles(session, dids):
    profiles = {}
    for did in dids:
        profiles[did] = fetch_profile(session, did)
    return profiles

# Read handle from file
def read_handle_from_file(did):
    if os.path.exists(HANDLES_FILE):
        with open(HANDLES_FILE, 'r') as f:
            for line in f:
                stored_did, handle = line.strip().split(',')
                if stored_did == did:
                    return handle
    return None

# Write handle to file
def write_handle_to_file(did, handle):
    with open(HANDLES_FILE, 'a') as f:
        f.write('{},{}\n'.format(did, handle))

# Fetch notifications
def fetch_notifications(session):
    url = BASE_URL + 'app.bsky.notification.listNotifications'
    headers = {'Authorization': 'Bearer ' + session['accessJwt']}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('notifications', [])
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok('Cortana Chat', 'Failed to fetch notifications: ' + str(e))
        return []

# Fetch followers
def fetch_followers(session):
    url = BASE_URL + 'app.bsky.graph.getFollowers'
    headers = {'Authorization': 'Bearer ' + session['accessJwt']}
    params = {'actor': session['handle']}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('followers', [])
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok('Cortana Chat', 'Failed to fetch followers: ' + str(e))
        return []

# Fetch following
def fetch_following(session):
    url = BASE_URL + 'app.bsky.graph.getFollows'
    headers = {'Authorization': 'Bearer ' + session['accessJwt']}
    params = {'actor': session['handle']}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('follows', [])
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok('Cortana Chat', 'Failed to fetch following: ' + str(e))
        return []

def fetch_mutuals(session):
    followers = {f.get('did') for f in fetch_followers(session)}
    following = {f.get('did') for f in fetch_following(session)}

    mutual_dids = followers.intersection(following)

    # Resolve handles for mutuals
    mutuals = []
    for did in mutual_dids:
        handle = fetch_profile(session, did)
        mutuals.append(handle)

    return mutuals

def fetch_blocked_users(session):
    url = BASE_URL + "app.bsky.graph.getBlocks"
    headers = {"Authorization": "Bearer " + session["accessJwt"]}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("blocks", [])
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Error", "Failed to fetch blocked users: " + str(e))
        return []

# Fetch conversations with proper user handles in bulk
def fetch_conversations(session):
    url = CHAT_URL + 'chat.bsky.convo.listConvos'
    headers = {'Authorization': 'Bearer ' + session['accessJwt']}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        conversations = response.json().get('convos', [])
        
        # Collect all unique DIDs to fetch in bulk
        dids = {participant['did'] for convo in conversations for participant in convo.get('members', []) if 'did' in participant}
        profiles = {did: fetch_profile(session, did) for did in dids}
        
        # Assign resolved handles to conversations
        for convo in conversations:
            participants = convo.get('members', [])
            for participant in participants:
                if 'did' in participant:
                    participant['handle'] = profiles.get(participant['did'], 'Unknown')
            convo['user_handle'] = next(
                (p['handle'] for p in participants if p['handle'] != session['handle']),
                'Unknown'
            )
        
        return conversations
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok('Cortana Chat', 'Failed to fetch conversations: ' + str(e))
        return []

# Fetch messages for a conversation
def fetch_messages(session, convo_id):
    url = CHAT_URL + 'chat.bsky.convo.getMessages'
    headers = {'Authorization': 'Bearer ' + session['accessJwt']}
    params = {'convoId': convo_id}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        messages = response.json().get('messages', [])
        
        # Collect all unique DIDs to fetch in bulk
        dids = {message['sender']['did'] for message in messages if 'sender' in message and 'did' in message['sender']}
        profiles = {did: fetch_profile(session, did) for did in dids}
        
        # Assign resolved handles to messages
        for message in messages:
            if 'sender' in message and 'did' in message['sender']:
                message['sender']['handle'] = profiles.get(message['sender']['did'], 'Unknown')
        
        return messages
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok('Cortana Chat', 'Failed to fetch messages: ' + str(e))
        return []

# Create a new post
def create_post(session):
    keyboard = xbmc.Keyboard('', 'Enter your post')
    keyboard.doModal()
    if keyboard.isConfirmed():
        post_text = keyboard.getText()
        
        # trailing "Z" is preferred over "+00:00"
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        # Detect facets for hashtags and mentions
        facets = detect_facets(post_text, session)

        post = {
            "$type": "app.bsky.feed.post",
            "text": post_text,
            "facets": facets,
            "createdAt": now,
        }

        url = BASE_URL + 'com.atproto.repo.createRecord'
        headers = {
            'Authorization': 'Bearer ' + session['accessJwt']
        }
        data = {
            'repo': session['did'],
            'collection': 'app.bsky.feed.post',
            'record': post
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raise an error for bad status codes
            xbmcgui.Dialog().ok('Cortana Chat', 'Post created successfully!')
        except requests.exceptions.RequestException as e:
            xbmcgui.Dialog().ok('Cortana Chat', 'Failed to create post. Error: {}'.format(str(e)))

# Create a new post with media
def create_post_media(session):
    keyboard = xbmc.Keyboard('', 'Enter your post')
    keyboard.doModal()
    if keyboard.isConfirmed():
        post_text = keyboard.getText()
        
        # trailing "Z" is preferred over "+00:00"
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        # Detect facets for hashtags and mentions
        facets = detect_facets(post_text, session)

        # Prompt user to select image files
        dialog = xbmcgui.Dialog()
        image_paths = []
        while True:
            image_path = dialog.browse(1, 'Select Image', 'files', '.jpg|.jpeg|.png|.webp', False, False, '')
            if image_path:
                image_paths.append(image_path)
                if len(image_paths) >= 4:  # Limit to 4 images
                    break
                if not dialog.yesno('Cortana Chat', 'Do you want to add another image?'):
                    break
            else:
                break

        # Upload images and prepare the media structure
        images = []
        for image_path in image_paths:
            with open(image_path, 'rb') as f:
                img_bytes = f.read()
            # this size limit is specified in the app.bsky.embed.images lexicon
            if len(img_bytes) > 1000000:
                xbmcgui.Dialog().ok('Cortana Chat', 'Image file size too large. 1000000 bytes (1MB) maximum, got: {}'.format(len(img_bytes)))
                return
            blob = upload_file(BASE_URL, session['accessJwt'], image_path, img_bytes)
            images.append({"alt": "", "image": blob})

        post = {
            "$type": "app.bsky.feed.post",
            "text": post_text,
            "facets": facets,
            "createdAt": now,
            "embed": {
                "$type": "app.bsky.embed.images",
                "images": images
            }
        }

        url = BASE_URL + 'com.atproto.repo.createRecord'
        headers = {
            'Authorization': 'Bearer ' + session['accessJwt']
        }
        data = {
            'repo': session['did'],
            'collection': 'app.bsky.feed.post',
            'record': post
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raise an error for bad status codes
            xbmcgui.Dialog().ok('Cortana Chat', 'Post created successfully!')
        except requests.exceptions.RequestException as e:
            xbmcgui.Dialog().ok('Cortana Chat', 'Failed to create post. Error: {}'.format(str(e)))

# Function to create a game invite post
def create_post_invite(session):
    games = load_games()
    if not games:
        xbmcgui.Dialog().ok('Cortana Chat', 'No games found in games.txt.')
        return
    
    dialog = xbmcgui.Dialog()
    selected_game = dialog.select('Select a game to invite', list(games.keys()))
    if selected_game >= 0:
        game_title = list(games.keys())[selected_game]
        invite_text = "{} would like to play '{}' (Xbox)".format(session['handle'], game_title)

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        post = {
            "$type": "app.bsky.feed.post",
            "text": invite_text,
            "createdAt": now,
        }

        url = BASE_URL + 'com.atproto.repo.createRecord'
        headers = {
            'Authorization': 'Bearer ' + session['accessJwt']
        }
        data = {
            'repo': session['did'],
            'collection': 'app.bsky.feed.post',
            'record': post
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            xbmcgui.Dialog().ok('Cortana Chat', 'Beacon for {} posted successfully!'.format(game_title))
        except requests.exceptions.RequestException as e:
            xbmcgui.Dialog().ok('Cortana Chat', 'Failed to post beacon: {}'.format(str(e)))

def search_for_beacon(session, game_title=None):
    """Search for game invite beacons on Bluesky."""
    games = load_games()
    
    url = BASE_URL + "app.bsky.feed.searchPosts"
    headers = {'Authorization': 'Bearer ' + session['accessJwt']}
    
    if game_title:
        params = {'q': "would like to play '{}' (Xbox)".format(game_title)}
    else:
        params = {'q': "would like to play"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        posts = response.json().get("posts", [])
        
        results = ["Search For Game"]
        post_data = []
        
        for p in posts:
            post_text = p["record"].get("text", "")
            match = re.match(r"(.*) would like to play '(.*)' \(Xbox\)", post_text)
            if match:
                author = p["author"].get("handle", "Unknown")
                results.append("{}: {}".format(author, post_text))
                post_data.append(p)
        
        if len(results) == 1:
            xbmcgui.Dialog().ok("No Results", "No matching beacons found.")
            return
        
        choice = xbmcgui.Dialog().select("Beacon Search Results", results)
        
        if choice == -1:
            return
        elif choice == 0:
            game_choice = xbmcgui.Dialog().select("Select a game to search for", list(games.keys()))
            if game_choice == -1:
                return
            game_title = list(games.keys())[game_choice]
            search_for_beacon(session, game_title)
            return
        
        selected_post = post_data[choice - 1]
        author_handle = selected_post["author"].get("handle", "Unknown")
        post_text = selected_post["record"].get("text", "No content")
        
        match = re.match(r"(.*) would like to play '(.*)' \(Xbox\)", post_text)
        if match:
            game_title = match.group(2)
            if game_title in games:
                join_choice = xbmcgui.Dialog().yesno("Game Invite", "{} has invited you to play '{}'. Join?".format(author_handle, game_title))
                if join_choice:
                    launch_game(game_title)
            else:
                xbmcgui.Dialog().ok("Game Not Found", "{} is not installed.".format(game_title))
        else:
            xbmcgui.Dialog().ok(author_handle, post_text)
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Error", "Failed to search beacons: " + str(e))



# Function to upload files
def upload_file(base_url, access_token, filename, img_bytes):
    suffix = filename.split(".")[-1].lower()
    mimetype = "application/octet-stream"
    if suffix in ["png"]:
        mimetype = "image/png"
    elif suffix in ["jpeg", "jpg"]:
        mimetype = "image/jpeg"
    elif suffix in ["webp"]:
        mimetype = "image/webp"

    resp = requests.post(
        base_url + "com.atproto.repo.uploadBlob",
        headers={
            "Content-Type": mimetype,
            "Authorization": "Bearer " + access_token,
        },
        data=img_bytes,
    )
    resp.raise_for_status()
    return resp.json()["blob"]

# Detects mention / tag facets and hyperlinks them accordingly.
def detect_facets(text, session):
    facets = []
    utf16_text = text

    def utf16_index_to_utf8_index(i):
        return len(utf16_text[:i].encode('utf-8'))

    # Detect mentions
    mention_pattern = re.compile(r'(^|\s|\()(@[a-zA-Z0-9.-]+)(\b)')
    for match in mention_pattern.finditer(utf16_text):
        mention = match.group(2)
        handle = mention[1:]  # Remove the '@' character
        start = match.start(2)
        end = match.end(2)
        did = resolve_did(handle, session)
        if did:
            facets.append({
                'index': {
                    'byteStart': utf16_index_to_utf8_index(start),
                    'byteEnd': utf16_index_to_utf8_index(end),
                },
                'features': [{
                    '$type': 'app.bsky.richtext.facet#mention',
                    'did': did
                }]
            })

    # Detect hashtags
    hashtag_pattern = re.compile(r'(#[^\d\s]\S*)')
    for match in hashtag_pattern.finditer(utf16_text):
        hashtag = match.group(1)
        start = match.start(1)
        end = match.end(1)
        facets.append({
            'index': {
                'byteStart': utf16_index_to_utf8_index(start),
                'byteEnd': utf16_index_to_utf8_index(end),
            },
            'features': [{
                '$type': 'app.bsky.richtext.facet#tag',
                'tag': hashtag[1:]
            }]
        })

    return facets

# Display menu
def display_menu(session):
    while True:
        dialog = xbmcgui.Dialog()
        options = ['Chat', 'Friends', 'Notifications', 'Settings']
        choice = dialog.select('Cortana Chat', options)
        if choice == -1:
            return  # User backed out
        elif choice == 0:
            display_conversations(session)
        elif choice == 1:
            display_friends_menu(session)
        elif choice == 2:
            display_notifications(session)
        elif choice == 3:
            display_settings_menu(session)

# Display menu
def display_friends_menu(session):
    while True:
        dialog = xbmcgui.Dialog()
        options = ["Followers", "Following", "Mutuals", "Blocked", "Follow User", "Block User"]
        choice = dialog.select("Friends", options)
        
        if choice == -1:
            return  # User backed out
        elif choice == 0:
            display_followers(session)
        elif choice == 1:
            display_following(session)
        elif choice == 2:
            display_mutuals(session)
        elif choice == 3:
            display_blocked(session)  # New blocked users section
        elif choice == 4:
            follow_user(session)
        elif choice == 5:
            block_user(session)

def get_did_from_handle(session, handle):
    """Fetches the DID of a user from their handle."""
    url = BASE_URL + "app.bsky.actor.getProfile?actor=" + handle
    headers = {"Authorization": "Bearer " + session["accessJwt"]}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("did")  # Extract DID
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Error", "Could not find DID for @" + handle + ": " + str(e))
        return None

def follow_user(session, handle=None):
    if handle is None:  # If no handle is given, ask for one
        keyboard = xbmc.Keyboard("", "Enter the handle of the user to follow")
        keyboard.doModal()
        if keyboard.isConfirmed():
            handle = keyboard.getText().strip()
    
    if not handle:
        xbmcgui.Dialog().ok("Error", "No handle entered.")
        return

    did = get_did_from_handle(session, handle)
    if not did:
        return  # Stop if DID lookup fails

    url = BASE_URL + "com.atproto.repo.createRecord"
    headers = {"Authorization": "Bearer " + session["accessJwt"]}
    data = {
        "repo": session["did"],  # Your own DID (not the target user)
        "collection": "app.bsky.graph.follow",
        "record": {
            "$type": "app.bsky.graph.follow",
            "subject": did,  # Target user's DID
            "createdAt": datetime.datetime.utcnow().isoformat() + "Z"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        xbmcgui.Dialog().ok("Success", "You are now following @" + handle)
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Error", "Failed to follow @" + handle + ": " + str(e))

def get_follow_record_uri(session, did):
    url = BASE_URL + "com.atproto.repo.listRecords"
    headers = {"Authorization": "Bearer " + session["accessJwt"]}
    params = {
        "repo": session["did"],  # Your own repository
        "collection": "app.bsky.graph.follow",
        "limit": 100  # Fetch up to 100 follow records
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        records = response.json().get("records", [])

        for record in records:
            if record.get("value", {}).get("subject") == did:
                return record["uri"]  # Get follow record URI

        return None  # No follow record found
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Error", "Failed to fetch follow records: " + str(e))
        return None

def get_block_record_uri(session, did, handle):
    url = BASE_URL + "com.atproto.repo.listRecords"
    headers = {"Authorization": "Bearer " + session["accessJwt"]}
    params = {
        "repo": session["did"],  # Your own repo
        "collection": "app.bsky.graph.block",
        "limit": 100  # Fetch up to 100 block records
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        records = response.json().get("records", [])

        for record in records:
            if record.get("value", {}).get("subject") == did:
                if "uri" in record:
                    return record["uri"].split("/")[-1]  # Extract rkey from URI
                else:
                    xbmcgui.Dialog().ok("Error", "Block record for @" + handle + " is missing 'uri'.")
                    return None

        xbmcgui.Dialog().ok("Error", "Block record for @" + handle + " not found.")
        return None
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Error", "Failed to fetch block records: " + str(e))
        return None

def unfollow_user(session, handle):
    did = get_did_from_handle(session, handle)
    if not did:
        return

    # Fetch the follow record URI
    follow_uri = get_follow_record_uri(session, did)
    if not follow_uri:
        xbmcgui.Dialog().ok("Error", "Follow record for @" + handle + " not found.")
        return

    url = BASE_URL + "com.atproto.repo.deleteRecord"
    headers = {"Authorization": "Bearer " + session["accessJwt"]}
    data = {
        "repo": session["did"],
        "collection": "app.bsky.graph.follow",
        "rkey": follow_uri.split("/")[-1]  # Extract rkey from URI
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        xbmcgui.Dialog().ok("Success", "You have unfollowed @" + handle)
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Error", "Failed to unfollow @" + handle + ": " + str(e))


def block_user(session, handle=None):
    if handle is None:  # If no handle is given, prompt user
        keyboard = xbmc.Keyboard("", "Enter the handle of the user to block")
        keyboard.doModal()
        if keyboard.isConfirmed():
            handle = keyboard.getText().strip()

    if not handle:
        xbmcgui.Dialog().ok("Error", "No handle entered.")
        return

    did = get_did_from_handle(session, handle)
    if not did:
        return  # Stop if DID lookup fails

    url = BASE_URL + "com.atproto.repo.createRecord"
    headers = {"Authorization": "Bearer " + session["accessJwt"]}
    data = {
        "repo": session["did"],
        "collection": "app.bsky.graph.block",
        "record": {
            "$type": "app.bsky.graph.block",
            "subject": did,
            "createdAt": datetime.datetime.utcnow().isoformat() + "Z"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        xbmcgui.Dialog().ok("Success", "You have blocked @" + handle)
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Error", "Failed to block @" + handle + ": " + str(e))

def unblock_user(session, handle=None):
    if handle is None:
        keyboard = xbmc.Keyboard("", "Enter the handle of the user to unblock")
        keyboard.doModal()
        if keyboard.isConfirmed():
            handle = keyboard.getText().strip()

    if not handle:
        xbmcgui.Dialog().ok("Error", "No handle entered.")
        return

    did = get_did_from_handle(session, handle)
    if not did:
        return  # Stop if DID lookup fails

    # Fetch the block record rkey
    block_rkey = get_block_record_uri(session, did, handle)
    if not block_rkey:
        xbmcgui.Dialog().ok("Error", "Could not find block record for @" + handle)
        return

    url = BASE_URL + "com.atproto.repo.deleteRecord"
    headers = {"Authorization": "Bearer " + session["accessJwt"]}
    data = {
        "repo": session["did"],
        "collection": "app.bsky.graph.block",
        "rkey": block_rkey  # Use correct rkey
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        xbmcgui.Dialog().ok("Success", "You have unblocked @" + handle)
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Error", "Failed to unblock @" + handle + ": " + str(e))

# Display menu
def display_settings_menu(session):
    while True:
        dialog = xbmcgui.Dialog()
        options = ['Enable Notifications', 'Disable Notifications', 'Follow User', 'Block User', 'Game Settings']
        choice = dialog.select('Settings', options)
        if choice == -1:
            return  # User backed out
        elif choice == 0:
            enable_notifications()
        elif choice == 1:
            disable_notifications()
        elif choice == 2:
            follow_user(session)
        elif choice == 3:
            block_user(session)
        elif choice == 4:
            display_game_settings_menu(session)

# Display menu
def display_game_settings_menu(session):
    while True:
        dialog = xbmcgui.Dialog()
        options = ['Install Game', 'Bulk Install', 'Edit Games (ignore crash!)']
        choice = dialog.select('Game Settings', options)
        if choice == -1:
            return  # User backed out
        elif choice == 0:
            install_game()
        elif choice == 1:
            install_game_bulk()
        elif choice == 2:
            edit_games_menu()

# Display home feed
def display_home_feed(session):
    cursor = None
    while True:
        feed, next_cursor = fetch_home_feed(session, cursor)
        items = ["Post", "Post Media", "Set Beacon", "Search for Beacon"]
        items += [post['post']['author'].get('handle', 'Unknown') + ': ' + post['post']['record'].get('text', 'No content') 
                  for post in feed if 'post' in post and 'author' in post['post'] and 'record' in post['post']]

        if next_cursor:
            items.append("Next Page")

        dialog = xbmcgui.Dialog()
        choice = dialog.select("Beacons & Activity", items)

        if choice == -1:
            break  # User backed out
        elif choice == 0:
            create_post(session)
        elif choice == 1:
            create_post_media(session)
        elif choice == 2:
            create_post_invite(session)
        elif choice == 3:
            search_for_beacon(session)
        elif next_cursor and choice == len(items) - 1:
            cursor = next_cursor
        else:
            selected_post = feed[choice - 4].get("post", {})
            author_handle = selected_post.get("author", {}).get("handle", "Unknown")
            post_text = selected_post.get("record", {}).get("text", "No content")
            
            match = re.match(r"(.*) would like to play '(.*)'", post_text)
            if match:
                game_title = match.group(2)
                if game_title in load_games():
                    dialog = xbmcgui.Dialog()
                    join_choice = dialog.yesno("Game Invite", "{} has invited you to play '{}'. Join?".format(author_handle, game_title))
                    if join_choice:
                        launch_game(game_title)
                else:
                    xbmcgui.Dialog().ok("Game Not Found", "{} is not installed.".format(game_title))
            else:
                xbmcgui.Dialog().ok(author_handle, post_text)

def display_user_feed(session, handle):
    url = BASE_URL + "app.bsky.feed.getAuthorFeed"
    headers = {"Authorization": "Bearer " + session["accessJwt"]}
    params = {"actor": handle, "limit": 10}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        posts = data.get("feed", [])
        profile = data.get("profile", {})
        
        display_name = profile.get("displayName", "Unknown")
        bio = " | ".join(profile.get("description", "").splitlines())
        
        items = ["@{} - {}".format(handle, display_name)]
        if bio:
            items.append(bio)
        items += [p["post"]["record"].get("text", "No content") for p in posts]
        
        xbmcgui.Dialog().select("@" + handle + "'s Feed", items)
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Error", "Failed to fetch feed: " + str(e))

# Fetch post content by URI
def fetch_post_content(session, uri):
    url = BASE_URL + "app.bsky.feed.getPosts"
    headers = {"Authorization": "Bearer " + session["accessJwt"]}
    params = {"uris": uri}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        posts = response.json().get("posts", [])
        if posts:
            return posts[0].get("record", {}).get("text", "No content")
    except requests.exceptions.RequestException:
        return "Failed to load content"

    return "No content"

# Display notifications with post content
def display_notifications(session):
    notifications = fetch_notifications(session)
    items = []

    for n in notifications:
        author = n.get("author", {}).get("handle", "Unknown")
        reason = n.get("reason", "Unknown")
        text = n.get("record", {}).get("text", "")

        # Fetch referenced post content if it's a like or repost
        if reason in ["like", "repost"]:
            post_uri = n.get("reasonSubject", "")
            text = fetch_post_content(session, post_uri) if post_uri else "No content"

        items.append("{} - {} - {}".format(reason, author, text))

    xbmcgui.Dialog().select("Notifications", items)

# Display followers
def display_followers(session):
    followers = fetch_followers(session)
    items = [f.get("displayName", "No Name") + " (" + f.get("handle", "Unknown") + ")" for f in followers]

    choice = xbmcgui.Dialog().select("Followers", items)
    if choice >= 0:
        handle = followers[choice].get("handle")
        show_user_options(session, handle)

# Display following
def display_following(session):
    following = fetch_following(session)
    items = [f.get("displayName", "No Name") + " (" + f.get("handle", "Unknown") + ")" for f in following]

    choice = xbmcgui.Dialog().select("Following", items)
    if choice >= 0:
        handle = following[choice].get("handle")
        show_user_options(session, handle)

def display_mutuals(session):
    mutuals = fetch_mutuals(session)
    items = mutuals if mutuals else ["No mutuals found."]

    choice = xbmcgui.Dialog().select("Mutual Followers", items)
    if choice >= 0:
        handle = mutuals[choice]
        show_user_options(session, handle)

def display_blocked(session):
    blocked_users = fetch_blocked_users(session)
    items = [b.get("handle", "Unknown") for b in blocked_users]

    choice = xbmcgui.Dialog().select("Blocked Users", items)
    if choice >= 0:
        handle = blocked_users[choice].get("handle")
        show_user_options(session, handle)

def show_user_options(session, handle):
    options = ["View Feed", "Follow / Unfollow User", "Invite to Game", "Send Message", "Block / Unblock User"]
    choice = xbmcgui.Dialog().select("User Options - @" + handle, options)

    if choice == 0:
        display_user_feed(session, handle)
    elif choice == 1:
        toggle_follow(session, handle)
    elif choice == 2:
        invite_user_to_game(session, handle)
    elif choice == 3:
        send_message(session, handle)
    elif choice == 4:
        toggle_block(session, handle)  # Now supports unblocking

def toggle_follow(session, handle):
    following_users = set(f.get("handle") for f in fetch_following(session))

    if handle in following_users:
        unfollow_user(session, handle)  # Now correctly calls unfollow
    else:
        follow_user(session, handle)  # Calls follow function

def toggle_block(session, handle):
    blocked_users = set(f.get("handle") for f in fetch_blocked_users(session))

    if handle in blocked_users:
        unblock_user(session, handle)  # Call the existing function
    else:
        block_user(session, handle)  # Call the existing function

def invite_user_to_game(session, handle):
    games = load_games()
    if not games:
        xbmcgui.Dialog().ok("Cortana Chat", "No games found in games.txt.")
        return

    dialog = xbmcgui.Dialog()
    selected_game = dialog.select("Select a game to invite", list(games.keys()))
    if selected_game >= 0:
        game_title = list(games.keys())[selected_game]
        invite_text = "[CORTANALIVE] " + session["handle"] + " invited @" + handle + " to play '" + game_title + "'!"

        now = datetime.datetime.utcnow().isoformat() + "Z"
        post = {
            "$type": "app.bsky.feed.post",
            "text": invite_text,
            "createdAt": now,
        }

        url = BASE_URL + "com.atproto.repo.createRecord"
        headers = {"Authorization": "Bearer " + session["accessJwt"]}
        data = {"repo": session["did"], "collection": "app.bsky.feed.post", "record": post}

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            xbmcgui.Dialog().ok("Cortana Chat", "Game invite sent to @" + handle)
        except requests.exceptions.RequestException as e:
            xbmcgui.Dialog().ok("Cortana Chat", "Failed to send game invite: " + str(e))

# Display conversations
def display_conversations(session):
    conversations = fetch_conversations(session)
    items = [c.get('user_handle', 'Unknown') + ': ' + c.get('lastMessage', {}).get('text', 'No message') for c in conversations]
    dialog = xbmcgui.Dialog()
    choice = dialog.select('Conversations', items)
    if choice >= 0:
        convo_id = conversations[choice].get('id')
        display_messages(session, convo_id)

# Display messages in a conversation
def display_messages(session, convo_id):
    messages = fetch_messages(session, convo_id)
    items = ['Reply', 'Nudge', 'Invite To Game'] + [m.get('sender', {}).get('handle', 'Unknown') + ': ' + m.get('text', '') for m in messages]
    dialog = xbmcgui.Dialog()
    choice = dialog.select('Messages', items)
    
    if choice == -1:
        display_conversations(session)  # User backed out
    elif choice == 0:
        reply_to_conversation(session, convo_id)
    elif choice == 1:
        send_nudge(session, convo_id)
    elif choice == 2:
        invite_to_game(session, convo_id)
    elif choice > 2:
        message_text = messages[choice - 3].get('text', '')
        match = re.match(r"(.*) would like to play '(.*)'", message_text)
        if match:
            game_title = match.group(2)
            display_message_options(session, convo_id, game_title)

# Display message options
def display_message_options(session, convo_id, game_title):
    dialog = xbmcgui.Dialog()
    options = ['Reply', 'Accept Invite', 'Decline Invite']
    choice = dialog.select('Message Options', options)
    if choice == 0:
        reply_to_conversation(session, convo_id)
    elif choice == 1:
        launch_game(game_title)
    elif choice == 2:
        display_messages(session, convo_id)

# Display game invite options in home feed
def display_game_invite_options(game_title):
    options = ["Accept Invite", "Decline Invite"]
    dialog = xbmcgui.Dialog()
    invite_choice = dialog.select("Game Invite", options)
    
    if invite_choice == 0:  # Accept Invite
        if game_title in load_games():
            launch_game(game_title)
        else:
            xbmcgui.Dialog().ok("Game Not Found", "{} is not installed.".format(game_title))
    elif invite_choice == 1:  # Decline Invite
        return

# Send a message
def send_message(session, handle):
    keyboard = xbmc.Keyboard('', 'Enter your message')
    keyboard.doModal()
    
    if keyboard.isConfirmed():
        message_text = keyboard.getText().strip()
        if not message_text:
            xbmcgui.Dialog().ok("Error", "No message entered.")
            return

        # Find the conversation ID (or start a new conversation)
        convo_id = get_or_create_conversation(session, handle)
        if not convo_id:
            xbmcgui.Dialog().ok("Error", "Failed to find or start conversation with @" + handle)
            return

        now = datetime.datetime.utcnow().isoformat() + 'Z'
        message = {'$type': 'chat.bsky.convo.message', 'text': message_text, 'createdAt': now}
        url = CHAT_URL + 'chat.bsky.convo.sendMessage'
        headers = {'Authorization': 'Bearer ' + session['accessJwt']}
        data = {'convoId': convo_id, 'message': message}

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            xbmcgui.Dialog().ok("Success", "Message sent to @" + handle)
        except requests.exceptions.RequestException as e:
            xbmcgui.Dialog().ok("Error", "Failed to send message: " + str(e))

# Check if a conversation already exists, otherwise makes a new one.
def get_or_create_conversation(session, handle):
    # Fetch existing conversations
    conversations = fetch_conversations(session)

    # Look for an existing conversation with this handle
    for convo in conversations:
        if convo.get('user_handle') == handle:
            return convo.get('id')

    # If no conversation exists, start a new one
    did = get_did_from_handle(session, handle)
    if not did:
        return None

    url = CHAT_URL + 'chat.bsky.convo.createConversation'
    headers = {'Authorization': 'Bearer ' + session['accessJwt']}
    data = {'participants': [did]}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get('convoId')
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Error", "Failed to start conversation with @" + handle + ": " + str(e))
        return None



# Reply to a conversation and return to message list
def reply_to_conversation(session, convo_id):
    keyboard = xbmc.Keyboard('', 'Enter your reply')
    keyboard.doModal()
    if keyboard.isConfirmed():
        reply_text = keyboard.getText()
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        message = {'$type': 'chat.bsky.convo.message', 'text': reply_text, 'createdAt': now}
        url = CHAT_URL + 'chat.bsky.convo.sendMessage'
        headers = {'Authorization': 'Bearer ' + session['accessJwt']}
        data = {'convoId': convo_id, 'message': message}
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            xbmcgui.Dialog().ok('Cortana Chat', 'Reply sent successfully!')
        except requests.exceptions.RequestException as e:
            xbmcgui.Dialog().ok('Cortana Chat', 'Failed to send reply: ' + str(e))
    display_messages(session, convo_id)

# Nudge function
def send_nudge(session, convo_id):
    nudge_text = session['handle'] + " has sent you a nudge!"
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    message = {'$type': 'chat.bsky.convo.message', 'text': nudge_text, 'createdAt': now}
    url = CHAT_URL + 'chat.bsky.convo.sendMessage'
    headers = {'Authorization': 'Bearer ' + session['accessJwt']}
    data = {'convoId': convo_id, 'message': message}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        xbmcgui.Dialog().ok('Cortana Chat', 'Nudge sent successfully!')
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok('Cortana Chat', 'Failed to send nudge: ' + str(e))

# Invite to a game
def invite_to_game(session, convo_id):
    games = load_games()
    if not games:
        xbmcgui.Dialog().ok('Cortana Chat', 'No games found in games.txt.')
        return
    
    dialog = xbmcgui.Dialog()
    selected_game = dialog.select('Select a game to invite', list(games.keys()))
    if selected_game >= 0:
        game_title = list(games.keys())[selected_game]
        reply_text = session['handle'] + " would like to play '" + game_title + "'"
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        message = {'$type': 'chat.bsky.convo.message', 'text': reply_text, 'createdAt': now}
        url = CHAT_URL + 'chat.bsky.convo.sendMessage'
        headers = {'Authorization': 'Bearer ' + session['accessJwt']}
        data = {'convoId': convo_id, 'message': message}
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            xbmcgui.Dialog().ok('Cortana Chat', 'Invite sent successfully!')
	    return
        except requests.exceptions.RequestException as e:
            xbmcgui.Dialog().ok('Cortana Chat', 'Failed to send invite: ' + str(e))

def load_games():
    games = {}
    if os.path.exists(GAMES_FILE):
        with open(GAMES_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if line.startswith('"') and line.endswith('"'):
                    try:
                        name, path = line[1:-1].split('", "')
                        games[name] = path  # Store in dictionary
                    except ValueError:
                        xbmc.log("Skipping malformed line: {}".format(line), xbmc.LOGERROR)
    return games
	
def save_games(games):
    """Save updated games list back to games.txt."""
    with open(GAMES_FILE, "w") as file:
        for name, path in games:
            file.write('"{}", "{}"\n'.format(name, path))

def edit_game_name(games, index):
    """Open a keyboard dialog to rename the game."""
    old_name = games[index][0]
    keyboard = xbmc.Keyboard(old_name, "Enter New Game Name")
    keyboard.doModal()
    if keyboard.isConfirmed():
        new_name = keyboard.getText().strip()
        if new_name:
            games[index] = (new_name, games[index][1])  # Update name
            save_games(games)
            xbmcgui.Dialog().ok("Success", "Game name updated successfully!")

def edit_game_path(games, index):
    """Open a file browser to select a new .xbe path."""
    dialog = xbmcgui.Dialog()
    new_path = dialog.browse(1, "Select New Game Path", 'files', '.xbe', False, False, '')
    if new_path:
        games[index] = (games[index][0], new_path)  # Update path
        save_games(games)
        xbmcgui.Dialog().ok("Success", "Game path updated successfully!")

def edit_game_menu(games, index):
    """Show a submenu to allow the user to edit or remove a game."""
    dialog = xbmcgui.Dialog()
    options = ["Edit Name", "Edit Path", "Remove Game", "Cancel"]
    choice = dialog.select("Edit Game Entry", options)

    if choice == 0:
        edit_game_name(games, index)
    elif choice == 1:
        edit_game_path(games, index)
    elif choice == 2:
        remove_game(games, index)

def edit_games():
    """Main game editing menu."""
    games = load_games()
    if not games:
        xbmcgui.Dialog().ok("Error", "No games found in games.txt!")
        return

    dialog = xbmcgui.Dialog()
    game_list = ["{} - {}".format(name, path) for name, path in games]
    game_list.append("Cancel")  # Add cancel option
    selected = dialog.select("Select Game to Edit", game_list)

    if selected != -1 and selected < len(games):  # If valid selection
        edit_game_menu(games, selected)

def remove_game(games, index):
    """Remove a game from the list after user confirmation."""
    game_name = games[index][0]
    
    confirm = xbmcgui.Dialog().yesno("Confirm", "Are you sure you want to remove '{}' from the list?".format(game_name))
    if confirm:
        del games[index]  # Remove the game
        save_games(games)  # Save the updated list
        xbmcgui.Dialog().ok("Success", "'{}' has been removed.".format(game_name))

# Launch a game
def launch_game(game_title):
    games = load_games()
    if game_title in games:
        game_path = games[game_title]
        xbmc.executebuiltin('XBMC.RunXBE("' + game_path + '")')
        sys.exit()  # Ensures the script exits after launching the game
    else:
        dialog = xbmcgui.Dialog()
        choice = dialog.yesno('Game Not Found', '' + game_title + ' not found. Would you like to locate it?')
        if choice:
            install_game(game_title)

# Clean game name by removing bracketed text
def clean_game_name(folder_name):
    return re.sub(r"\s*\(.*?\)", "", folder_name).strip()

# Prompt user to browse for XBE file
def browse_for_xbe():
    dialog = xbmcgui.Dialog()
    xbe_path = dialog.browse(1, 'Select default.xbe', 'files', 'default.xbe', False, False)
    return xbe_path if xbe_path.endswith('default.xbe') else None

# Extract folder name from path
def get_folder_name_from_path(path):
    return os.path.basename(os.path.dirname(path))

# Prompt user to confirm or edit the game name
def get_game_name(default_name):
    clean_name = clean_game_name(default_name)
    keyboard = xbmc.Keyboard(clean_name, "Enter Game Name")
    keyboard.doModal()
    return keyboard.getText() if keyboard.isConfirmed() else None

# Write game entry to games.txt
def write_to_games_txt(game_name, xbe_path):
    games_file = xbmc.translatePath('special://home/games.txt')
    entry = '"{}", "{}"\n'.format(game_name, xbe_path)

    try:
        # Ensure the file ends with a newline
        if os.path.exists(games_file):
            with open(games_file, "rb") as f:
                f.seek(-1, os.SEEK_END)
                last_char = f.read(1)
            if last_char != b"\n":
                with open(games_file, "ab") as f:
                    f.write(b"\n")

        # Append new entry
        with open(games_file, "a") as f:
            f.write(entry)

    except Exception as e:
        xbmcgui.Dialog().ok("Error", "Failed to write to games.txt:\n{}".format(str(e)))

# Install a game
def install_game(game_title=None):
    xbe_path = browse_for_xbe()
    if not xbe_path:
        xbmcgui.Dialog().ok("Error", "No default.xbe selected!")
        return

    folder_name = get_folder_name_from_path(xbe_path)
    game_name = get_game_name(game_title if game_title else folder_name)

    if game_name:
        write_to_games_txt(game_name, xbe_path)
        
        # Combine success and launch prompt into one dialog
        launch_choice = xbmcgui.Dialog().yesno("Game Added", "{} has been installed!".format(game_name), "Would you like to launch it now?")

        if launch_choice:
            launch_game(game_name)
    else:
        xbmcgui.Dialog().ok("Cancelled", "No game name entered.")

def install_game_bulk():
    # Let the user pick a directory
    root_dir = xbmcgui.Dialog().browse(0, "Select Game Directory", 'files')
    if not root_dir:
        xbmcgui.Dialog().ok("Error", "No directory selected!")
        return
    
    games_installed = []
    game_entries = []
    
    # Walk through the directory recursively to find all .xbe files
    for subdir, _, files in os.walk(root_dir):
        if "default.xbe" in files:
            xbe_path = os.path.join(subdir, "default.xbe")
            folder_name = os.path.basename(subdir)
            
            # Remove anything in brackets (e.g., "Halo 2 (GLO)" -> "Halo 2")
            game_name = re.sub(r'\s*\(.*?\)', '', folder_name).strip()
            
            if game_name:
                game_entries.append((game_name, xbe_path))
                games_installed.append(game_name)
    
    if game_entries:
        # Sort games alphabetically before writing to games.txt
        game_entries.sort(key=lambda x: x[0])
        for game_name, xbe_path in game_entries:
            write_to_games_txt(game_name, xbe_path)
        
        xbmcgui.Dialog().ok("Games Installed", "The following games were installed:\n" + "\n".join(sorted(games_installed)))
    else:
        xbmcgui.Dialog().ok("No Games Found", "No valid games were found in the selected directory.")

# Enable notifications
def enable_notifications():
    enable_script_path = os.path.join(os.path.dirname(__file__), 'notifier.py')
    xbmc.executebuiltin('RunScript("{}")'.format(enable_script_path.replace("\\", "\\\\")))

# Disable notifications
def disable_notifications():
    disable_script_path = os.path.join(os.path.dirname(__file__), 'stop_notifier.py')
    xbmc.executebuiltin('RunScript("{}")'.format(disable_script_path.replace("\\", "\\\\")))

# Edit games
def edit_games_menu():
    edit_games()

# Main function with direct menu navigation
def main():
    username, app_password = load_credentials()
    if not username or not app_password:
        xbmcgui.Dialog().ok('Cortana Chat', 'Enter your BlueSky username and app password in login.txt.')
        return

    session = authenticate(username, app_password)
    if not session:
        return

    # Check for arguments passed from XBMC
    if len(sys.argv) > 1:
        option = sys.argv[1]
        if option == "Chat":
            display_conversations(session)
        elif option == "Notifications":
            display_notifications(session)
        elif option == "Friends":
            display_friends_menu(session)
        elif option == "Activity":
            display_home_feed(session)
        elif option == "Settings":
            display_settings_menu(session)
    else:
        display_menu(session)

if __name__ == '__main__':
    main()
