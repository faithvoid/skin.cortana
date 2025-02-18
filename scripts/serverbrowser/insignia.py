import xbmc
import xbmcgui
import xml.etree.ElementTree as ET
import urllib2
import re
import os
from datetime import datetime, timedelta

def fetch_and_parse_rss(url):
    try:
        request = urllib2.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
        request.add_header('Referer', 'http://www.google.com')
        
        response = urllib2.urlopen(request)
        data = response.read().decode('utf-8')
        root = ET.fromstring(data.encode('utf-8'))
        return root
    except Exception as e:
        xbmc.log("Failed to fetch or parse the feed: {}".format(str(e)), xbmc.LOGERROR)
        return None

def clean_html(text):
    return re.sub(r'<[^>]+>', '', text).strip()

def clean_game_name(game_name):
    # Regex to match and remove the pattern ": number player(s)" and anything that follows
    pattern = r':\s*\d+\s*players?.*$'
    # Using regex to search and replace the part that matches the pattern with an empty string
    clean_name = re.sub(pattern, '', game_name, flags=re.IGNORECASE)
    return clean_name.strip()

def load_game(game_name):
    filtered_game_name = clean_game_name(game_name)
    if os.path.exists("special://home/games.txt"):
        with open("special://home/games.txt", "r") as file:
            for line in file:
                line = line.strip()
                name, path = line[1:-1].split('", "')
                if name == filtered_game_name:
                    return path
    return None

def save_game(game_name, game_path):
    filtered_game_name = clean_game_name(game_name)
    with open("special://home/games.txt", "a") as file: 
        file.write('"{}", "{}"\n'.format(filtered_game_name, game_path))

def launch_game(game_path):
    xbmc.executebuiltin('XBMC.RunXBE({})'.format(game_path))

def process_game_selection(dialog, items, selected):
    if selected != -1:
        selected_item = items[selected].split(' - ')[0]
        game_path = load_game(selected_item)
        if not game_path:
            game_path = dialog.browse(1, "Select Game Path", 'files', '.xbe', False, False, '')
            if game_path:
                save_game(selected_item, game_path)
                launch = dialog.yesno("Launch Game", "Do you want to launch the game now?")
                if launch:
                    xbmc.executebuiltin('XBMC.RunXBE({})'.format(game_path))
                else:
                    return
            else:
                xbmcgui.Dialog().ok("Error", "No game path selected!")
        else:
            xbmc.executebuiltin('XBMC.RunXBE({})'.format(game_path))

def display_stats(dialog, channel, args=None):
    stats = ['...']
    for item in channel.findall('item'):
        title_elem = item.find('title')
        if title_elem is not None and any(prefix in title_elem.text for prefix in ["Users Online", "Registered Users", "Games Supported", "Active Games"]):
            stats.append(title_elem.text.strip())
    selected = dialog.select("Stats", stats)
    if selected == 0:
        main()
    elif selected > 0:
        xbmcgui.Dialog().ok("Statistics", stats[selected])

def display_feed_items(dialog, channel, args=None):
    regular_items = ['...']
    excluded_titles = ["Users Online", "Registered Users", "Games Supported", "Active Games", "Game Event"]  # List of titles to exclude
    
    for item in channel.findall('item'):
        title_elem = item.find('title')
        if title_elem is not None:
            title = title_elem.text.strip()  # Remove leading/trailing whitespace from title
            
            # Check if title starts with any excluded phrases
            if not any(title.startswith(excluded) for excluded in excluded_titles):
                game_name = clean_game_name(title.split(' - ')[0])
                game_path = load_game(game_name)
                
                # Prepare the description, ensuring correct formatting
                description = "Installed - {}".format(game_path) if game_path else "Not Installed"
                
                # Strip and replace extra spaces in the final formatted item
                formatted_item = "{} - {}".format(title.strip(), description.strip())
                formatted_item = re.sub(r'\s+', ' ', formatted_item).strip()  # Replace multiple spaces with one
                
                # Append the cleaned and formatted item
                regular_items.append(formatted_item)

    # Present the user with the selection dialog
    selected_game = dialog.select("Cortana Server Browser - Insignia", regular_items)
    if selected_game == 0:
        return
    else:
        process_game_selection(dialog, regular_items, selected_game)

def parse_event_date(title):
    today = datetime.today().strftime('%a, %b %d')
    tomorrow = (datetime.today() + timedelta(days=1)).strftime('%a, %b %d')
    
    if "Today:" in title:
        return (0, title)  # Prioritize "Today"
    elif "Tomorrow:" in title:
        return (1, title)  # Prioritize "Tomorrow"
    else:
        # Extract actual date from title using regex (assuming format "Sat, Feb 23rd")
        match = re.search(r'(\w{3}),\s(\w{3})\s(\d{1,2})', title)
        if match:
            day, month, date = match.groups()
            try:
                event_date = datetime.strptime(month + " " + date, "%b %d")
                event_date = event_date.replace(year=datetime.today().year)
                return (2, event_date)  # Assign priority for sorting
            except ValueError:
                pass
    return (3, title)  # Default fallback priority

def display_events(dialog, channel, args=None):
    events = []
    for item in channel.findall('item'):
        title_elem = item.find('title')
        description_elem = item.find('description')
        if title_elem is not None and title_elem.text.startswith("Game Event"):
            description = clean_html(description_elem.text) if description_elem is not None else "No description available"
            event_text = title_elem.text.replace("Game Event - ", "") + " - " + description
            events.append((parse_event_date(title_elem.text), event_text))
    
    # Sort events by parsed date priority
    events.sort()
    
    # Extract sorted event texts
    sorted_event_texts = [event[1] for event in events]
    
    selected = dialog.select("Game Events", sorted_event_texts)
    if selected == 0:
        main()
    elif selected > 0:
        xbmcgui.Dialog().ok("Event Details", sorted_event_texts[selected])

def display_events(dialog, channel, args=None):
    events = []
    for item in channel.findall('item'):
        title_elem = item.find('title')
        description_elem = item.find('description')
        if title_elem is not None and title_elem.text.startswith("Game Event"):
            description = clean_html(description_elem.text) if description_elem is not None else "No description available"
            event_text = "{} - {}".format(title_elem.text.replace("Game Event - ", ""), description)
            events.append((parse_event_date(title_elem.text), event_text))
    
    # Sort events by parsed date priority
    events.sort()
    
    # Extract sorted event texts
    sorted_event_texts = [event[1] for event in events]
    
    selected = dialog.select("Game Events", sorted_event_texts)
    if selected == 0:
        main()
    elif selected > 0:
        xbmcgui.Dialog().ok("Event Details", sorted_event_texts[selected])

def main():
    dialog = xbmcgui.Dialog()
    feeds = {
        "Sessions": display_feed_items,
        "Statistics": display_stats,
        "Events": display_events,
    }
    
    if len(sys.argv) > 1 and sys.argv[1].capitalize() in feeds:
        selected_function = feeds[sys.argv[1].capitalize()]
        url = "http://ogxbox.org/rss/insignia.xml"
        root = fetch_and_parse_rss(url)
        if root is not None:
            channel = root.find('channel')
            if channel is not None:
                selected_function(dialog, channel, sys.argv)
            else:
                xbmc.log("No channel element found", xbmc.LOGERROR)
        else:
            xbmcgui.Dialog().ok("Error", "Failed to load information!")
    else:
        feed_list = list(feeds.keys())
        selected = dialog.select("Cortana Server Browser - Insignia", feed_list)
        if selected >= 0:
            name = feed_list[selected]
            selected_function = feeds[name]
            url = "http://ogxbox.org/rss/insignia.xml"
            root = fetch_and_parse_rss(url)
            if root is not None:
                channel = root.find('channel')
                if channel is not None:
                    selected_function(dialog, channel)
                else:
                    xbmc.log("No channel element found", xbmc.LOGERROR)
            else:
                xbmcgui.Dialog().ok("Error", "Failed to load information!")

if __name__ == '__main__':
    main()
