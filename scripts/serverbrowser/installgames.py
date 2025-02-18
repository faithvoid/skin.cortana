import xbmc
import xbmcgui
import os
import re

GAMES_FILE = xbmc.translatePath('Q://games.txt')

def load_games():
    games = []
    if os.path.exists(GAMES_FILE):
        with open(GAMES_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if line.startswith('"') and line.endswith('"'):
                    try:
                        name, path = line[1:-1].split('", "')
                        games.append((name, path))
                    except ValueError:
                        xbmc.log("Skipping malformed line: {}".format(line), xbmc.LOGERROR)
    return games

def save_games(games):
    with open(GAMES_FILE, "w") as file:
        for name, path in games:
            file.write('"{}", "{}"\n'.format(name, path))

def edit_game_name(games, index):
    old_name = games[index][0]
    keyboard = xbmc.Keyboard(old_name, "Enter New Game Name")
    keyboard.doModal()
    if keyboard.isConfirmed():
        new_name = keyboard.getText().strip()
        if new_name:
            games[index] = (new_name, games[index][1])
            save_games(games)
            xbmcgui.Dialog().ok("Success", "Game name updated successfully!")

def edit_game_path(games, index):
    dialog = xbmcgui.Dialog()
    new_path = dialog.browse(1, "Select New Game Path", 'files', '.xbe', False, False, '')
    if new_path:
        games[index] = (games[index][0], new_path)
        save_games(games)
        xbmcgui.Dialog().ok("Success", "Game path updated successfully!")

def remove_game(games, index):
    game_name = games[index][0]
    confirm = xbmcgui.Dialog().yesno("Confirm", "Are you sure you want to remove '{}' from the list?".format(game_name))
    if confirm:
        del games[index]
        save_games(games)
        xbmcgui.Dialog().ok("Success", "'{}' has been removed.".format(game_name))

def edit_game_menu(games, index):
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
    games = load_games()
    if not games:
        xbmcgui.Dialog().ok("Error", "No games found in games.txt!")
        return
    dialog = xbmcgui.Dialog()
    game_list = ["{} - {}".format(name, path) for name, path in games]
    selected = dialog.select("Select Game to Edit", game_list)
    if selected != -1:
        edit_game_menu(games, selected)

def browse_for_xbe():
    dialog = xbmcgui.Dialog()
    xbe_path = dialog.browse(1, 'Select default.xbe', 'files', 'default.xbe', False, False)
    return xbe_path if xbe_path.endswith('default.xbe') else None

def get_game_name(default_name):
    keyboard = xbmc.Keyboard(default_name, "Enter Game Name")
    keyboard.doModal()
    return keyboard.getText().strip() if keyboard.isConfirmed() else None

def install_game():
    xbe_path = browse_for_xbe()
    if not xbe_path:
        xbmcgui.Dialog().ok("Error", "No default.xbe selected!")
        return
    game_name = get_game_name(os.path.basename(os.path.dirname(xbe_path)))
    if game_name:
        games = load_games()
        games.append((game_name, xbe_path))
        save_games(games)
        xbmcgui.Dialog().ok("Success", "Game installed successfully!")

def install_game_bulk():
    root_dir = xbmcgui.Dialog().browse(0, "Select Game Directory", 'files')
    if not root_dir:
        xbmcgui.Dialog().ok("Error", "No directory selected!")
        return
    games_installed = []
    game_entries = []
    for subdir, _, files in os.walk(root_dir):
        if "default.xbe" in files:
            xbe_path = os.path.join(subdir, "default.xbe")
            folder_name = os.path.basename(subdir)
            game_name = re.sub(r'\s*\(.*?\)', '', folder_name).strip()
            if game_name:
                game_entries.append((game_name, xbe_path))
                games_installed.append(game_name)
    if game_entries:
        game_entries.sort(key=lambda x: x[0])
        for game_name, xbe_path in game_entries:
            games = load_games()
            games.append((game_name, xbe_path))
            save_games(games)
        xbmcgui.Dialog().ok("Games Installed", "The following games were installed:\n" + "\n".join(sorted(games_installed)))
    else:
        xbmcgui.Dialog().ok("No Games Found", "No valid games were found in the selected directory.")

def main():
    dialog = xbmcgui.Dialog()
    options = ["Add Game", "Edit Games", "Bulk Install Games"]
    choice = dialog.select("Game Manager", options)
    if choice == 0:
        install_game()
    elif choice == 1:
        edit_games()
    elif choice == 2:
        install_game_bulk()

if __name__ == '__main__':
    main()
