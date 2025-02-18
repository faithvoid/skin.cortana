import xbmc
import xbmcgui
import time
import urllib2
import xml.etree.ElementTree as ET
import re
from collections import deque
import os

# Separate queues for storing different types of notification messages
game_event_queue = deque()
regular_notification_queue = deque()

def clear_notifications_file():
    """ Clear the notifications file at the start of the script. """
    open("Q:\\scripts\\Cortana Server Browser\\Insignia\\notifications.txt", "w").close()

def load_notifications():
    """ Load previous notifications from file """
    if os.path.exists("Q:\\scripts\\Cortana Server Browser\\Insignia\\notifications.txt"):
        with open("Q:\\scripts\\Cortana Server Browser\\Insignia\\notifications.txt", "r") as f:
            return set(f.read().strip().split("\n"))
    return set()

def save_notifications(notifications):
    """ Save current notifications to file """
    with open("Q:\\scripts\\Cortana Server Browser\\Insignia\\notifications.txt", "w") as f:
        for notification in notifications:
            f.write("%s\n" % notification)

def clean_title(title):
    """ Clean the title to remove excessive spaces and ensure correct formatting """
    # Replace multiple spaces with a single space, and strip leading/trailing spaces
    return re.sub(r'\s+', ' ', title.strip())

def check_rss_only_once():
    """ Check RSS feed only once for game events at script launch """
    current_notifications = load_notifications()
    new_notifications = set()
    try:
        url = 'http://ogxbox.org/rss/insignia.xml'
        req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib2.urlopen(req)
        data = response.read()
        root = ET.fromstring(data)

        for item in root.findall('.//item'):
            title = item.find('title').text
            if title.startswith("Game Event - Today") or title.startswith("Game Event - Tomorrow"):
                clean_title_text = re.sub(r'^Game Event - ', '', title)
                clean_title_text = clean_title(clean_title_text)  # Clean the title here
                if clean_title_text not in current_notifications:
                    game_event_queue.append(("Insignia Event(s)", clean_title_text))
                    new_notifications.add(clean_title_text)

        save_notifications(new_notifications)
    except Exception as e:
        error_msg = "RSS Error: " + str(e)
        regular_notification_queue.append(("RSS Feed Error", error_msg))
        new_notifications.add(error_msg)

def check_rss_regular():
    """ Check RSS feed regularly for all other notifications """
    current_notifications = load_notifications()
    new_notifications = set()
    try:
        url = 'http://ogxbox.org/rss/insignia.xml'
        req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib2.urlopen(req)
        data = response.read()
        root = ET.fromstring(data)

        for item in root.findall('.//item'):
            title = item.find('title').text
            if "(0 in 0 sessions)" in title:
                continue

            match = re.search(r'(\d+) players?', title)
            if match:
                players = int(match.group(1))
                if players > 0:
                    clean_title_text = clean_title(title)  # Clean the title here
                    new_notifications.add(clean_title_text)
                    if clean_title_text not in current_notifications:
                        regular_notification_queue.append(("Insignia Session(s)!", clean_title_text))

        save_notifications(new_notifications)
    except Exception as e:
        error_msg = "RSS Error: " + str(e)
        regular_notification_queue.append(("RSS Feed Error", error_msg))
        new_notifications.add(error_msg)

def process_notifications():
    """ Process and display queued notifications """
    while game_event_queue:
        header, message = game_event_queue.popleft()
        display_notification(header, message)

    while regular_notification_queue:
        header, message = regular_notification_queue.popleft()
        display_notification(header, message)

def display_notification(header, message):
    """ Display notifications based on their type and content """
    xbmc.executebuiltin('Notification("{}", "{}")'.format(header, message))
    time.sleep(10)

# Clear notifications file at the start
clear_notifications_file()
# Check RSS feed for game events only once at start
check_rss_only_once()
process_notifications()

while True:
    check_rss_regular()
    process_notifications()
    time.sleep(60)
