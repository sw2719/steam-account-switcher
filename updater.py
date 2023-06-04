import sys
import os


def exc_hook(type, value, traceback, oldhook=sys.excepthook):
    oldhook(type, value, traceback)
    input('    Press Enter to exit...')


sys.excepthook = exc_hook

import zipfile as zf
import locale
import shutil

LOCALE = locale.getdefaultlocale()[0]
FILES_TO_PRESERVE = ('config.yml', 'config.json', 'accounts.yml', 'accounts.json', 'salt')


def pprint(content):
    print('   ', content)


def clear():
    os.system('cls')


pprint(f'Launch arguments: {" ".join(sys.argv)}')

if '--force-update' in sys.argv:
    force = True
elif "__compiled__" not in globals():
    print()
    pprint("Running on Python interpreter not supported")
    print()
    input('    Press Enter to exit...')
    sys.exit(0)
else:
    force = False


def invalidzip():
    print()
    if LOCALE == 'ko_KR':
        pprint('업데이트 압축 파일이 유효하지 않습니다.')
        pprint('프로그램을 재시작 하여 업데이트를 다시 시도하십시오.')
        print()
        pprint('----------------------------------------------------------')
        print()
        input('    Enter 키를 눌러서 나가기...')
    else:
        pprint('Update archive is invalid.')
        pprint('Restart the application and try again.')
        print()
        pprint('----------------------------------------------------------')
        print()
        input('    Press Enter to exit...')
    sys.exit(1)


cwd = os.getcwd()

if LOCALE == 'ko_KR':
    pprint('현재 작업 디렉토리: ' + cwd)
    pprint('업데이트 압축 파일 확인 중...')
else:
    pprint('Current working directory: ' + cwd)
    pprint('Verifying update archive...')

print()
archive = os.path.join(cwd, 'update.zip')

if not os.path.isfile(archive):
    pprint("Error: Archive file doesn't exist")
    invalidzip()
elif not zf.is_zipfile(archive):
    pprint("Error: Archive file is not a zip file")
    invalidzip()
else:
    try:
        f = zf.ZipFile(archive, mode='r')
    except zf.BadZipFile:
        pprint('Error: Bad zip file')
        invalidzip()

if 'Steam Account Switcher.exe' not in f.namelist():
    pprint(f.namelist())
    invalidzip()

print()
if LOCALE == 'ko_KR':
    pprint('업데이트 설치 중...')
else:
    pprint('Installing update...')

for name in os.listdir(os.getcwd()):
    if os.path.isdir(os.path.join(os.getcwd(), name)):
        if name != 'avatar':
            try:
                shutil.rmtree(name)
                pprint('Deleted a directory: ' + name)
            except OSError:
                pass
    elif os.path.isfile(os.path.join(os.getcwd(), name)):
        if name not in FILES_TO_PRESERVE:
            try:
                os.remove(name)
                pprint('Deleted a file: ' + name)
            except OSError:
                pass

while True:
    try:
        pprint('Extracting...')
        f.extractall(members=(member for member in f.namelist() if 'updater' not in member))
        break
    except OSError:
        print()
        if LOCALE == 'ko_KR':
            pprint('업데이트 도중 오류가 발생하였습니다.')
            pprint('다른 앱이 파일을 사용 중이지 않은지 확인하세요.')
            print()
            pprint('----------------------------------------------------------')
            print()
            input('    다시 시도하려면 Enter키를 누르세요...')
        else:
            pprint('Error occured during update process.')
            pprint('Make sure that other applications are not using any of the files')
            print()
            pprint('----------------------------------------------------------')
            print()
            input('    Press Enter to try again...')
        clear()

f.close()

if not force:
    os.execv('Steam Account Switcher.exe', sys.argv)
else:
    input('Forced update complete. Press Enter to exit...')
