import xbmc
import xbmcgui
import time
import urllib2
import xml.etree.ElementTree as ET
import re
from collections import deque
import os

# Separate queues for different types of notification messages
game_event_queue = deque()
regular_notification_queue = deque()

def clear_notifications_file():
    """ Clear the notifications file at the start of the script. """
    open("Q:\\scripts\\Cortana Server Browser\\XLink\\notifications.txt", "w").close()

def load_notifications():
    """ Load previous notifications from file """
    if os.path.exists("Q:\\scripts\\Cortana Server Browser\\XLink\\notifications.txt"):
        with open("Q:\\scripts\\Cortana Server Browser\\XLink\\notifications.txt", "r") as f:
            return set(f.read().strip().split("\n"))
    return set()

def save_notifications(notifications):
    """ Save current notifications to file """
    with open("Q:\\scripts\\Cortana Server Browser\\XLink\\notifications.txt", "w") as f:
        for notification in notifications:
            f.write("%s\n" % notification)

def clean_title(title):
    """ Clean the title to remove excessive spaces and ensure correct formatting """
    # Replace multiple spaces with a single space, and strip leading/trailing spaces
    return re.sub(r'\s+', ' ', title.strip())

def check_rss_only_once():
    """ Check RSS feed for game events only once at script launch """
    current_notifications = load_notifications()
    new_notifications = set()
    try:
        url = 'http://ogxbox.org/rss/xlinkkai'
        req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib2.urlopen(req)
        data = response.read()
        root = ET.fromstring(data)

        for item in root.findall('.//item'):
            title = item.find('title').text
            if title.startswith("Team XLink Discord Game Event - Today") or title.startswith("Team XLink Discord Game Event - Tomorrow"):
                clean_title_text = re.sub(r'^Team XLink Discord Game Event - ', '', title)
                clean_title_text = clean_title(clean_title_text)  # Clean the title here
                if clean_title_text not in current_notifications:
                    game_event_queue.append(("XLink Kai Event(s)", clean_title_text, 5000, True))
                    new_notifications.add(clean_title_text)

        save_notifications(new_notifications)
    except Exception as e:
        error_msg = "RSS Error: " + str(e)
        regular_notification_queue.append(("RSS Feed Error", error_msg, 5000, False))
        new_notifications.add(error_msg)

def check_rss_regular():
    """ Check RSS feed for all other notifications regularly """
    current_notifications = load_notifications()
    new_notifications = set()
    try:
        url = 'http://ogxbox.org/rss/xlinkkai'
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
                if players > 0 and title not in current_notifications:
                    clean_title_text = clean_title(title)  # Clean the title here
                    new_notifications.add(clean_title_text)
                    regular_notification_queue.append(("Found XLink Session(s)!", clean_title_text, 5000, True))

        save_notifications(new_notifications)
    except Exception as e:
        error_msg = "RSS Error: " + str(e)
        regular_notification_queue.append(("RSS Feed Error", error_msg, 5000, False))
        new_notifications.add(error_msg)

def process_notifications():
    """ Process and display queued notifications """
    while game_event_queue:
        header, message, duration, should_scroll = game_event_queue.popleft()
        display_notification(header, message, duration, should_scroll)

    while regular_notification_queue:
        header, message, duration, should_scroll = regular_notification_queue.popleft()
        display_notification(header, message, duration, should_scroll)

def display_notification(header, message, duration, should_scroll):
    """ Display notifications based on their type and content """
    if should_scroll:
        scroll_notification(header, message, duration)
    else:
        xbmc.executebuiltin('Notification("{}", "{}", {})'.format(header, message, duration))
        time.sleep(duration / 1000.0)

def scroll_notification(header, message, duration):
    """ Handle long message scrolling """
    chunk_size = 32
    length = len(message)
    if length <= chunk_size:
        xbmc.executebuiltin('Notification("{}", "{}", {})'.format(header, message, duration))
        time.sleep(duration / 1000.0)
    else:
        step_size = 2
        step_duration = 1000
        total_steps = (length - chunk_size + step_size) // step_size if length > chunk_size else 1
        
        for i in range(0, total_steps):
            start_index = i * step_size
            end_index = start_index + chunk_size
            current_chunk = message[start_index:end_index]
            xbmc.executebuiltin('Notification("{}", "{}", {})'.format(header, current_chunk, step_duration))
            time.sleep(step_duration / 1000.0)
        
        last_chunk_duration = 2500 if message.endswith(')') else 1000
        xbmc.executebuiltin('Notification("{}", "{}", {})'.format(header, message[-chunk_size:], last_chunk_duration))
        time.sleep(last_chunk_duration / 1000.0)

# Clear notifications file at the start
clear_notifications_file()
# Check RSS feed for game events only once at start
check_rss_only_once()
process_notifications()

while True:
    check_rss_regular()
    process_notifications()
    time.sleep(60)
