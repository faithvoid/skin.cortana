# cortanaOS - A modern, sleek "Xbox 180" style theme for XBMC4Xbox, with an emphasis on social / multiplayer feature integration.
## Requires [Cortana Server Browser](https://github.com/faithvoid/script.cortanaserverbrowser), [Cortana Chat](https://github.com/faithvoid/script.cortanachatv2), [Cortana Wireless (optional)](https://github.com/faithvoid/script.cortanawireless) & [xSky](https://github.com/faithvoid/plugin.programs.xSky) to function correctly!

## Menu Screenshots:
![cortanaOS1](screenshots/1.png)
![cortanaOS2](screenshots/2.png)
![cortanaOS3](screenshots/3.png)
![cortanaOS4](screenshots/4.png)
![cortanaOS5](screenshots/5.png)
![cortanaOS6](screenshots/6.png)
![cortanaOS7](screenshots/7.png)

## Cortana Server Browser:
![Cortana Server Browser - 1](screenshots/csb1.png)
![Cortana Server Browser - 2](screenshots/csb2.png)
![Cortana Server Browser - 3](screenshots/csb3.png)

## Cortana Chat
![Cortana Chat - 1](screenshots/cc1.png)
![Cortana Chat - 2](screenshots/cc2.png)
![Cortana Chat - 3](screenshots/cc3.png)
![Cortana Chat - 4](screenshots/cc4.png)

## Themes
### Aero (WIP)
![Aero](screenshots/aero-test.png)
### Aero Lite (WIP)
![Aero Lite](screenshots/aerolite-test.png)

## Features:
- Replaced the broken Weather page with **Cortana**, a series of scripts that allows you to view & join active Insignia/XLink Kai sessions, events, view server statistics, get new match notifications, get Cortana/Insignia/XLink Kai news, check your Insignia DNS settings, send/receive messages, and more!

- Get social on your Xbox again! Using **Cortana Chat**, you can use the AT protocol (aka Bluesky) to chat with fellow gamers, invite them to games, set beacons to find other players, and more, as well as quick access to Xbox Video Chat for voice/video chat over Insignia!

- Show off your gamerscore and reputation with **Cortana ID**, a reimplementation of gamertags from MC360! Set it manually, or pull it from your Xbox Live profile manually (or automatically on startup)!

- Paired with **Cortana Wireless**, you can easily connect a Raspberry Pi or similar SBC as a wireless network card for your Xbox and easily manage your Wi-Fi settings!

- **Per-profile save games and social features!** Share your Xbox with friends and family? Everyone gets their own accounts and saves!

- **"Guide button"** feature that reimplements most of the features you know and love from the 360, using Cortana Chat! Just click in the right stick and you have full access to social features, matchmaking features, media controls, settings, and more!

- **Toast notifications** for messages and notifications via Cortana Chat, and toast notifications for current XLink Kai / Insignia sessions via Cortana Server Browser!
  
- **Added quality-of-life functions to the Applications page** (Renamed certain items to seem more "official", added "Addons" & "Scripts" buttons, "Dashboard" button, "Xbox Live" (Network Settings) button, and "Detach Virtual Disk").
  
- **Added quality-of-life functions to the Media page** (added Video/Music/Photo add-ons!), as well as watched media indicators that were missing from the original JX 720!

- Use **Cortana Marketplace** to quickly download homebrew games & emulators! If stored in a .zip/.rar file, Cortana Marketplace will automatically extract the homebrew to your Homebrew folder so you can instantly hop into the action!
  
- Neon wallpapers have been swapped out for pastel abstract shapes (based off of old macOS 9 wallpapers), making the UI easier on the eyes.

- Multiple open-source font options for accessibility, with the primary font now being changed to Open Sans for better readability on smaller screens!
    
- Need to fix something? **cortanaOS Settings Menu** has you covered! With shortcuts to the **Dashboard, Internet Connection Test utilities, Notification Settings, Clear Cache, XBMC4Gamers Scripts, Updates,** and more, cortanaOS can help you out of most pickles!

- Easily boot into reactOS / Linux via the "otherOS" option in Settings!

- Every single option you see can be toggled and configured in the settings menu! Don't like the logos? You can turn them off, or replace them with Xbox logos! Don't use XLink Kai? You can disable everything XLink Kai related! Don't use Cortana Chat? You can disable that, too! 

- Instantly access the Insignia & XLink Kai websites from your phone by enabling QR codes for the Cortana blade in the settings! You can also display additional QR codes such as local IP address & an XLink Kai webUI IP by enabling those in the settings menu, and the skin will take care of setting them up seamlessly!

- Speed improvements over the base JX720 skin, making it one of the lightest Xbox Media Centre themes, even with all these new features! All textures have been packaged into one file, meaning faster load times across the dashboard, and lower system resource usage (has 35-39MB of RAM free at idle on average)!

- Per-page RSS feeds! The Cortana blade shows Insignia & XLink session/server/event information & the Settings menu shows Cortana news by default, and the Games & Media blades are for your own RSS feeds! (These can all easily be modified in RssFeeds.xml in your UserData folder)

## How to install:
- Download latest release from the Releases category (if there isn't a release .zip, do NOT clone this skin from GitHub and expect support! The repo is ALWAYS under development so things may be broken even if most features work, especially script-related functionality!)
- Copy "Cortana" to "Q:\skins\"
- Change your skin to Cortana in the XBMC Appearance menu.
- ???
- Profit!

## TODO (High Priority)
- Fix up & release Cortana Server Browser & Cortana Chat.
- Reincorporate gamertag and media buttons from MC360 into guide menu somehow.

## TODO (Low-Med Priority):
- Further work on "Cortana Marketplace" (need to find a futureproof source for Xbox homebrew and possibly convert it from a script into an add-on for image previews)
- Add per-user autoexec files.
- Fix multi-user savegame script.
- Work on "Aero Lite" theme (a light pastel version of the default theme)

## Bugs:
- Cortana blade is currently a bit visually glitchy and visibly says "Refresh" when switching pages. It's a "blink and you'll mix it" issue but it's still present.
- Signing in to Cortana Chat can currently hang the system when launching a game right as the script refreshes. Looking into a fix for this ASAP before release.
- You tell me.
- Certain multi-tasking actions can crash 64MB Xbox systems if video/visualization transparency behind menus is enabled, such as going to the menu and launching a script via the guide menu. This shouldn't be an issue for 128mb systems, but YMMV. You can toggle this option under "cortanaOS -> Skin Settings" to find what works for you.

## Credits:
- Steve Matteson - Open Sans font
- Jezz_X & Team Blackbolt - JX720 & MC360, respectively (this project uses JX720 as a base, with MC360 assets reincorporated where possible)
