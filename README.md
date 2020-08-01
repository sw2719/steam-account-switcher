<img align="right" src="https://user-images.githubusercontent.com/22590718/89107236-861eaa80-d46a-11ea-8d1e-0a126823e01a.PNG">

# Steam Account Switcher
Lightweight, fast account switcher for Steam.

Written in Python

Note that I manage this project to get experience with Python. This is my first Python project.

[이 문서는 한국어로도 읽을 수 있습니다.](https://github.com/sw2719/steam-account-switcher/blob/master/README_ko.md)

[Download in releases](https://github.com/sw2719/steam-account-switcher/releases)

STEAM is a trademark of Valve Corporation.

This app has no affiliation with Steam and Valve.

# Features
* Switch between your accounts with just few clicks.

* No more entering ID, password and Steam Guard code every time you login to another account.

* Restarting Steam with single click.

* Unlike some other programs, your passwords are **NOT** required. Only uses your usernames.

* Auto-importing your Steam accounts. Do more clicking, less typing.

* Auto-updating is built-in, and it's fast. (Unless GitHub's server is having a hard time..)

# Requirements
* 64-bit Windows
* Steam installed correctly
* And that's pretty much it.

# How to use
1. Unpack the archive to desired folder
2. Run the exe
**(Because this program alters your registry values AND is not code-signed, Windows SmartScreen or your Anti-virus might detect it as harmful software. You can just ignore it.)**

3. Import accounts from Steam or add them manually via Menu > Add accounts
* Your account names are saved in accounts.yml located in the same folder where exe file is.

4. Click one of the buttons to change to desired account.
* Steam login prompt might appear if you are using this program for the first time. Just check 'Remember password' and login. It will work next time. 
  - You need to do this for every account except the one you have been using as autologin account prior to using this program.
  - **If you ever add more accounts, you have to do this for them as well. And if you don't login to certain account for a while, you will have to do this again for that account due to Steam revoking autologin access.**

# FAQ
* Login prompt appears! Fake program!
  - See How to use-4. Right above.

* Windows SmartScreen says this program is potentially harmful!
  - That's because I didn't sign my executable with EV certificate which is expensive as f#@!. Great job, M$.

* I have a request! / I found a bug!
  - Bug reports and requests are always welcome. Please submit a issue.

* Some of the elements in settings are missing!
  - Delete config.yml and launch application again.

# Source code information
* All other branches except master are considered as acitve-development branch and might have issues, bugs, WIP features, or might not just work at all.
* Written in Python 3.8
* Do not run updater.py in python interpreter. It's designed to run only in frozen environment.
* Use requirements.txt to install dependencies.
* Source code is written in English. Translation to other languages is done with gettext.
* My code is probably a low-quality, poorly written mess. But hey, at least it works right?
