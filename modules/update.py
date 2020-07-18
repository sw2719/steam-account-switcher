import tkinter as tk
import tkinter.ttk as ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox as msgbox
import gettext
import os
import queue as q
import requests as req
import shutil
import zipfile as zf
import subprocess
import sys
import threading
from time import sleep
from packaging import version
from ruamel.yaml import YAML
from modules.config import get_config
from modules.errormsg import error_msg

yaml = YAML()

LOCALE = get_config('locale')

t = gettext.translation('steamswitcher',
                        localedir='locale',
                        languages=[LOCALE],
                        fallback=True)
_ = t.gettext

update_frame = None

#  Update code is a real mess right now. You have been warned.


def start_checkupdate(master, cl_ver_str, URL, bundle, debug=False, **kw):
    '''Check if application has update'''
    global update_frame

    try:
        exception = kw['exception']
    except KeyError:
        exception = False

    if update_frame is not None:
        update_frame.destroy()

    update_frame = tk.Frame(master)
    update_frame.config(bg='white')

    if not bundle and not debug:
        ttk.Separator(update_frame, orient='horizontal').pack(side='top', pady=(0, 0), fill='x')
        update_frame.pack(side='bottom', fill='x')
        return
    else:
        update_frame.pack(side='bottom', fill='x')

    ttk.Separator(update_frame, orient='horizontal').pack(side='top', pady=(0, 0), fill='x')
    master.update()

    def update(sv_version, changelog, mirror_url):
        nonlocal debug

        updatewindow = tk.Toplevel(master)
        updatewindow.title(_('Update'))
        updatewindow.geometry("400x300+650+300")
        updatewindow.resizable(False, False)
        updatewindow.focus()

        button_frame = tk.Frame(updatewindow)
        button_frame.pack(side=tk.BOTTOM, pady=3, fill='x')

        cancel_button = ttk.Button(button_frame, text=_('Cancel'),
                                   command=updatewindow.destroy)
        update_button = ttk.Button(button_frame, width=28, text=_('Update now'))

        text_frame = tk.Frame(updatewindow)
        text_frame.pack(side=tk.TOP, pady=3)
        text = tk.Label(text_frame,
                        text=_('New version %s is available.') % sv_version)
        text.pack()

        changelog_box = ScrolledText(updatewindow, width=57)
        changelog_box.insert(tk.CURRENT, changelog)
        changelog_box.configure(state=tk.DISABLED)
        changelog_box.pack(padx=5)

        updatewindow.grab_set()

        def start_update(mirror_url):
            '''Withdraw main window and start update download'''
            nonlocal button_frame
            nonlocal cancel_button
            nonlocal update_button
            nonlocal debug
            nonlocal sv_version

            master.withdraw()
            try:
                os.remove('update.zip')
            except OSError:
                pass

            install = True

            # For development purposes
            if not bundle and debug:
                if not msgbox.askyesno('', 'Install update?'):
                    install = False

            cancel_button.destroy()
            update_button.destroy()

            def cancel():
                if msgbox.askokcancel(_('Cancel'), _('Are you sure to cancel?')):
                    os._exit(0)

            # There's no cancel button so we use close button as one instead
            updatewindow.protocol("WM_DELETE_WINDOW", cancel)

            # Define progress variables
            dl_p = tk.IntVar()
            dl_p.set(0)
            dl_pbar = ttk.Progressbar(button_frame,
                                      length=150,
                                      orient=tk.HORIZONTAL,
                                      variable=dl_p)
            dl_pbar.pack(side='left', padx=5)

            dl_prog_var = tk.StringVar()
            dl_prog_var.set('-------- / --------')
            dl_prog = tk.Label(button_frame, textvariable=dl_prog_var)

            dl_speed_var = tk.StringVar()
            dl_speed_var.set('---------')
            dl_speed = tk.Label(button_frame, textvariable=dl_speed_var)

            dl_prog.pack(side='right', padx=5)
            dl_speed.pack(side='right', padx=5)
            master.update()

            download_q = q.Queue()

            try:  # Check if mirror is available and should we use it
                if mirror_url:
                    mirror = req.get(mirror_url + 'mirror.yml', timeout=4)
                    mirror.raise_for_status()

                    r_time = mirror.elapsed.total_seconds()
                    print(f'Mirror server took {str(r_time)} seconds to respond.')

                    if r_time >= 0.5:
                        print('Mirror is too slow.')
                        raise req.RequestException

                    mirror_yml = yaml.load(mirror.text)

                    if mirror_yml['mirror_available'] == 'true' and mirror_yml['mirror_version'] == sv_version:
                        if msgbox.askyesno(_('Mirror available'), _('Do you want to download from Mirror?') + '\n' +
                                           _("If you live outside South East Asia, it is advised not to use it.") + '\n' +
                                           _('(Note that mirror is located in South Korea.)')):
                            print('Using mirror for downloading update...')
                            dl_url = f'{mirror_url}mirror/{mirror_yml["mirror_filename"]}'
                        else:
                            print('User cancelled mirror download.')
                            raise req.RequestException
                    else:
                        print('Mirror validation error.')
                        raise req.RequestException
                else:
                    print('Cannot reach mirror or mirror is not online.')
                    raise req.RequestException
            except (req.RequestException, KeyError):
                print('Reverting to GitHub for downloading update...')
                dl_url = f'https://github.com/sw2719/steam-account-switcher/releases/download/v{sv_version}/Steam_Account_Switcher_v{sv_version}.zip'

            def download(URL):
                nonlocal download_q

                try:
                    r = req.get(URL, stream=True)
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length'))
                    total_in_MB = round(total_size / 1048576, 1)
                except req.RequestException:
                    msgbox.showerror(_('Error'),
                                     _('Error occured while downloading update.'))
                    os._exit(1)

                if round(total_in_MB, 1).is_integer():
                    total_in_MB = int(total_in_MB)

                def save():
                    nonlocal r
                    with open('update.zip', 'wb') as f:
                        shutil.copyfileobj(r.raw, f)

                dl_thread = threading.Thread(target=save)
                dl_thread.start()

                last_size = 0

                # This download speed calculation is not really accurate.
                # This is my best effort to make real-time one instad of average one.
                while True:
                    try:
                        current_size = os.path.getsize('update.zip')
                        current_in_MB = round(current_size / 1048576, 1)

                        if round(current_in_MB, 1).is_integer():
                            current_in_MB = int(current_in_MB)

                        size_delta = current_size - last_size
                        bps = size_delta * 2  # Multiply size delta by 2 since we calculate speed every 0.5s

                        if bps >= 1048576:  # Above 1MiB/s
                            dl_spd = bps / 1048576
                            if round(dl_spd, 1).is_integer():
                                dl_spd = int(dl_spd)
                            else:
                                dl_spd = round(dl_spd, 1)
                            dl_spd_str = f'{dl_spd}MB/s'
                        elif bps >= 1024:  # Above 1KiB/s
                            dl_spd = bps / 1024
                            if round(dl_spd, 1).is_integer():
                                dl_spd = int(dl_spd)
                            else:
                                dl_spd = round(dl_spd, 1)
                            dl_spd_str = f'{dl_spd}KB/s'
                        else:
                            dl_spd = bps
                            dl_spd_str = f'{dl_spd}B/s'

                        perc = int(current_size / total_size * 100)

                        prog = f'{current_in_MB}MB / {total_in_MB}MB'

                        download_q.put((perc, prog, dl_spd_str))
                        if perc == 100:
                            break
                        else:
                            last_size = current_size
                            sleep(0.5)
                    except OSError:
                        sleep(0.5)
                        continue

            def update_pbar():
                nonlocal download_q
                nonlocal dl_p
                nonlocal dl_speed_var
                nonlocal dl_prog_var
                while True:
                    try:  # Update tk variables
                        q_tuple = download_q.get_nowait()
                        p = q_tuple[0]
                        dl_p.set(p)
                        dl_prog_var.set(q_tuple[1])
                        dl_speed_var.set(q_tuple[2])
                        master.update()
                        if p == 100:
                            return
                    except q.Empty:
                        master.update()

            dl_thread = threading.Thread(target=lambda url=dl_url: download(url))
            dl_thread.start()

            update_pbar()
            if install:
                try:
                    archive = os.path.join(os.getcwd(), 'update.zip')

                    f = zf.ZipFile(archive, mode='r')
                    f.extractall(members=(member for member in f.namelist() if 'updater' in member))

                    subprocess.run('start updater/updater.exe', shell=True)
                    sys.exit(0)
                except (FileNotFoundError, zf.BadZipfile, OSError):
                    error_msg(_('Error'), _("Couldn't perform automatic update.") + '\n' +
                              _('Update manually by extracting update.zip file.'))

        update_button['command'] = lambda: start_update(mirror_url)
        if LOCALE == 'fr_FR':
            padx_int = 80
        else:
            padx_int = 110
        cancel_button.pack(side='left', padx=(padx_int, 0))
        update_button.pack(side='right', padx=(0, padx_int))

    queue = q.Queue()

    def checkupdate():
        '''Fetch version information from GitHub and
        return different update codes'''
        print('Update check start')
        update = None
        try:
            if exception:
                raise req.RequestException
            response = req.get(URL)
            response.encoding = 'utf-8'
            text = response.text
            version_data = yaml.load(text)
            sv_version_str = str(version_data['version'])

            if LOCALE == 'ko_KR':
                changelog = version_data['changelog_ko']
            else:
                changelog = version_data['changelog_en']

            try:
                critical_msg = version_data['msg'][str(cl_ver_str)]
                if critical_msg:
                    if LOCALE == 'ko_KR':
                        msgbox.showinfo(_('Info'),
                                        critical_msg['ko'])
                    else:
                        msgbox.showinfo(_('Info'),
                                        critical_msg['en'])
            except (KeyError, TypeError):
                pass

            try:
                mirror_url = version_data['mirror_baseurl']
            except KeyError:
                print('No mirror data')
                mirror_url = None

            print('Server version is', sv_version_str)
            print('Client version is', cl_ver_str)

            sv_version = version.parse(sv_version_str)
            cl_version = version.parse(cl_ver_str)

            if sv_version > cl_version:
                update = 'avail'
            elif sv_version == cl_version:
                update = 'latest'
            elif sv_version < cl_version:
                update = 'dev'

        except (req.RequestException, req.ConnectionError,
                req.Timeout, req.ConnectTimeout):
            update = 'error'
            sv_version_str = '0'
            changelog = None
            mirror_url = None

        queue.put((update, sv_version_str, changelog, mirror_url))

    update_code = None
    sv_version = None
    changelog = None
    mirror_url = None

    def get_output():
        '''Get version info from checkupdate() and draw UI accordingly.'''
        global update_frame
        nonlocal update_code
        nonlocal sv_version
        nonlocal changelog
        nonlocal mirror_url
        nonlocal debug
        try:
            v = queue.get_nowait()
            update_code = v[0]
            sv_version = v[1]
            changelog = v[2]
            mirror_url = v[3]

            if debug:
                print('Update debug mode')

                update_frame.destroy()

                update_frame = tk.Frame(master, bg='white')
                ttk.Separator(update_frame, orient='horizontal').pack(side='top', pady=(0, 3), fill='x')
                update_frame.pack(side='bottom', fill='x')

                update_label = tk.Label(update_frame,
                                        text=f'Client: {cl_ver_str} / Server: {sv_version} / {update_code} / Click to open UI',
                                        bg='white')
                update_label.pack(side='bottom')

                update_label.bind('<ButtonRelease-1>', lambda event: update(sv_version=sv_version,
                                                                            changelog=changelog,
                                                                            mirror_url=mirror_url))

                update_frame.bind('<ButtonRelease-1>', lambda event: update(sv_version=sv_version,
                                                                            changelog=changelog,
                                                                            mirror_url=mirror_url))
                return

            if update_code == 'avail':
                print('Update Available')

                update_frame.destroy()

                update_frame = tk.Frame(master, bg='white')
                ttk.Separator(update_frame, orient='horizontal').pack(side='top', pady=(0, 3), fill='x')
                update_frame.pack(side='bottom', fill='x')

                update_label = tk.Label(update_frame,
                                        text=_('Version %s is available. Click here to update!') % sv_version,
                                        bg='white',
                                        fg='green')  # NOQA
                update_label.pack(side='bottom')
                update_label.bind('<ButtonRelease-1>', lambda event: update(sv_version=sv_version, changelog=changelog, mirror_url=mirror_url))
                update_frame.bind('<ButtonRelease-1>', lambda event: update(sv_version=sv_version, changelog=changelog, mirror_url=mirror_url))
            elif update_code == 'latest':
                print('On latest version')

                update_frame.destroy()

                update_frame = tk.Frame(master, bg='white')
                ttk.Separator(update_frame, orient='horizontal').pack(side='top', pady=(0, 0), fill='x')
                update_frame.pack(side='bottom', fill='x')
            elif update_code == 'dev':
                print('Development version')

                update_frame.destroy()

                update_frame = tk.Frame(master, bg='white')
                ttk.Separator(update_frame, orient='horizontal').pack(side='top', pady=(0, 3), fill='x')
                update_frame.pack(side='bottom', fill='x')

                update_label = tk.Label(update_frame,
                                        text=_('Development version'),
                                        bg='white')
                update_label.pack(side='bottom')
            else:
                print('Exception while getting server version')

                update_frame.destroy()

                update_frame = tk.Frame(master, bg='white')
                ttk.Separator(update_frame, orient='horizontal').pack(side='top', pady=(0, 3), fill='x')
                update_frame.pack(side='bottom', fill='x')

                update_label = tk.Label(update_frame,
                                        text=_('Failed checking for updates. Click here to try again.'),
                                        bg='white',
                                        fg='red')
                update_frame.bind('<ButtonRelease-1>', lambda event: start_checkupdate(master, cl_ver_str, URL, bundle, debug=debug))
                update_label.bind('<ButtonRelease-1>', lambda event: start_checkupdate(master, cl_ver_str, URL, bundle, debug=debug))
                update_label.pack(side='bottom')
        except q.Empty:
            master.after(300, get_output)

    t = threading.Thread(target=checkupdate)
    t.start()
    master.after(300, get_output)


def hide_update():
    global update_frame
    update_frame.pack_forget()


def show_update():
    global update_frame
    update_frame.pack(side='bottom', fill='x')
