# Steam Account Switcher
Steam Account Switching made easy (on Windows)

Written in Python

Note that I manage this project to get experience with Python. This is my first Python project.

[이 문서는 한국어로도 읽을 수 있습니다.](https://github.com/sw2719/steam-account-switcher/blob/master/README_ko.md)

[Download in releases](https://github.com/sw2719/steam-account-switcher/releases)

[See this program in action (Doesn't represent the latest version.)](https://youtu.be/WFtv10RZ_UA)

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
* IMPORTANT: If it's your first time using account switcher with selected account or login prompt appears, Make sure that the 'Remember my Password' is checked. Then enter your password and login as you normally would. You will need to enter your Steam Guard code if Mobile Authenticator is enabled. Next time you switch to that account, it will login automatically without entering Username / Password and Steam Guard code. 
  - **You need to do this EVERY TIME you add new accounts. And if you don't login for certain amount of time, you will have to do this again due to Steam revoking your autologin access.**

# FAQ
* Login prompt appears! Fake program!
  - See How to use-4. Right above.

* Windows SmartScreen says this program is potentially harmful!
  - I didn't sign my executable with EV certificate which is expensive as f#@!. Great job, M$.

* I have a request! / I found a bug!
  - Bug reports and requests are always welcome. Please submit a issue.

# Source code information
* All other branches except master are considered as acitve-development branch and might have issues, bugs, WIP features, or might not just work at all.
* Written in Python 3.7 64-bit
* Do not run updater.py in python interpreter. It's designed to run only in frozen environment.
* Requests, packaging, psutil, ruamel.yaml and gettext module are required.
* threading module needs to be installed if you are using Python version under 3.7.
* Source code is written in English. Translation to other languages is done with gettext.
* My code is probably a low-quality, poorly written mess. But hey, at least it works right?
