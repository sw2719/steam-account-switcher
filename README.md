# Steam Account Switcher
Steam Account Switching made easy

No more Steam Guard code.

Works without your passwords!

[Download in releases](https://github.com/sw2719/steam-account-switcher/releases)

[See this program in action](https://youtu.be/WFtv10RZ_UA)

# Changelogs (for last 3 versions)
* Reduced UI flickering (v1.3)
* Multi language support (v1.3)

  Supported languages: Korean(한국어), English
* Automatic update checking (v1.2)

* Intial Release (v1.1)

# Upcoming Features / Changes
* Gracefully shutting down Steam (Maybe v1.4)
* Import account names from Steam (v1.4)
* Improving code & readability (Continuous)

# About the code
* Written in Python 3.7
* Requests and gettext module are required.
* Keep in mind that I'm _quite_ new to Python. I'm sorry if my code is dirty, hard to read, or poorly written.
* Lots of global keywords. Yeah I know. They are bad. I just don't know how to do it without them. I could use parameters but to call a function with parameters in tkinter widgets, I need to use lambda or whatever. And I thought using globals would be better than lambdas. Any advice is appreciated.
* Strings in source code are in Korean. I used gettext to translate Korean strings into English. po files are avaliable in /locale. I will add English comments soon. I'm considering that I write source code in English.

# How to use
1. Unpack the archive
2. Save it to some folder
3. Run the exe
(Because this program alters your registry value, Windows SmartScreen or your Anti-virus might detect it as harmful software.)
4. Add accounts via Menu > Add accounts
* Your account names are saved in accounts.txt located in the same folder where exe is.
* They are saved in Plain text. (Steam also saves your account names in plain text as well.
* Warning: Do NOT add accounts by manually editing accounts.txt
* Account limit is 12
5. Click one of the buttons to change to desired account.
* If you previously set auto-login for that account, It just works.
* It might show login prompt if you didn't login for a while. Steam doesn't let you auto-login after certain period of time.

* If you did not, Login prompt will appear when Steam launches. Make sure that the 'Remember my Password' is checked. Then enter your password and login as you normally would. You will need to enter your Steam Guard code if Mobile Authenticator is enabled. Next time you switch to that account, it will login automatically without entering Username / Password and Steam Guard code.

# Guide
![window_instruction](https://user-images.githubusercontent.com/22590718/63221815-78c8cb80-c1d9-11e9-829d-c4f1ef855285.png)

# Screenshots
![window](https://user-images.githubusercontent.com/22590718/63221824-87af7e00-c1d9-11e9-96e2-87508d2128b5.png)
![windowremove](https://user-images.githubusercontent.com/22590718/63221825-87af7e00-c1d9-11e9-8887-ed530c305166.png)
![windowadd](https://user-images.githubusercontent.com/22590718/63221826-88481480-c1d9-11e9-82eb-2b78dc9d528d.png)

# How it works
When you launch the program for the first time, the program fetches current auto-login user from registry and then adds it to accounts.txt.
When you add account(s), it saves your username(s) to accounts.txt in plain text.
(Steam saves your usernames in plain text as well)
When you press one of the 'account-changing' buttons, code below runs.

(slightly modified to incrase readability)
```
reg_key = winreg.OpenKey(HCU, r"Software\Valve\Steam", 0, winreg.KEY_ALL_ACCESS)
winreg.SetValueEx(reg_key, 'AutoLoginUser', 0, winreg.REG_SZ, your_username)
winreg.CloseKey(reg_key)
```
It changes key 'AutoLoginUser' located at Steam registry path, tricking Steam to autologin with that username.