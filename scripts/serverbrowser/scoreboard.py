# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcplugin
import requests
import re

# Base URL for Insignia
BASE_URL = "https://insignia.live/games/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0"}
PAGE_SIZE = 100

# Function to fetch webpage content
def fetch_url(url):
    response = requests.get(url, headers=HEADERS)
    return response.text

# Function to extract games with leaderboards using regex
def get_games_with_leaderboards():
    games = []
    content = fetch_url(BASE_URL)
    game_blocks = re.findall(r'<tr>(.*?)</tr>', content, re.DOTALL)
    
    for block in game_blocks:
        if '<i class="fa fa-trophy ml-2 visible" title="Leaderboards"></i>' in block and '<i class="fa fa-trophy ml-2 invisible" title="Leaderboards"></i>' not in block:
            match = re.search(r'<a href="(https://insignia.live/games/[^"]+)">.*?<img .*? alt="([^\"]+)"', block, re.DOTALL)
            if match:
                game_link, game_name = match.groups()
                games.append((game_name.strip(), game_link.strip()))
    
    return games

# Function to extract leaderboard data using regex
def get_leaderboard_data(game_url):
    content = fetch_url(game_url)
    matches = re.findall(r'<tr>\s*<td>(\d+)</td>\s*<td>([^<]+)</td>\s*<td class="text-right">.*?<img.*?title="Level (\d+)"', content, re.DOTALL)
    leaderboard = [(rank.strip(), player.strip(), level.strip()) for rank, player, level in matches]
    return leaderboard

# XBMC Plugin Menu
def show_games():
    games = get_games_with_leaderboards()
    
    if not games:
        xbmcgui.Dialog().ok("Insignia Leaderboards", "No games found with leaderboards.")
        return
    
    game_names = [game[0] for game in games]
    selected = xbmcgui.Dialog().select("Select a Game", game_names)
    
    if selected != -1:
        show_leaderboard(games[selected][1])

def show_leaderboard(game_url):
    leaderboard = get_leaderboard_data(game_url)
    
    if not leaderboard:
        xbmcgui.Dialog().ok("Leaderboard", "No leaderboard data found.")
        return
    
    page = 0
    total_pages = (len(leaderboard) + PAGE_SIZE - 1) // PAGE_SIZE
    
    while True:
        start_index = page * PAGE_SIZE
        end_index = min(start_index + PAGE_SIZE, len(leaderboard))
        menu_items = ["#" + rank + " " + player + " - Level " + level for rank, player, level in leaderboard[start_index:end_index]]
        
        navigation_map = {}
        if page < total_pages - 1:
            navigation_map[len(menu_items)] = "next"
            menu_items.append("Next Page")
        if page > 0:
            navigation_map[len(menu_items)] = "previous"
            menu_items.append("Previous Page")
        navigation_map[len(menu_items)] = "exit"
        menu_items.append("Exit")
        
        selected = xbmcgui.Dialog().select("Leaderboard Rankings (Page " + str(page + 1) + " of " + str(total_pages) + ")", menu_items)
        
        if selected == -1 or navigation_map.get(selected) == "exit":  # Exit if the user cancels
            break
        elif navigation_map.get(selected) == "previous":  # Previous Page
            page -= 1
        elif navigation_map.get(selected) == "next":  # Next Page
            page += 1

if __name__ == "__main__":
    show_games()
