import sys
import os
import zipfile as zf
import shutil
import locale

locale_buf = locale.getdefaultlocale()
LOCALE = locale_buf[0]


def pprint(content):
    print('    ' + content)


if not getattr(sys, 'frozen', False):
    print()
    pprint("Running on Python interpreter not supported")
    print()
    input('    Press Enter to exit')
    sys.exit(0)


def invalidzip():
    print()
    if locale == 'ko_KR':
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
pprint('Current working directory: ' + cwd)
print()
archive = os.path.join(cwd, 'update.zip')

if not os.path.isfile(archive) or not zf.is_zipfile(archive):
    invalidzip()
else:
    try:
        f = zf.ZipFile(archive, mode='r')
    except zf.BadZipFile:
        invalidzip()

if 'Steam Account Switcher.exe' not in f.namelist():
    invalidzip()

whitelist = ('accounts.txt', 'updater')

parent_dir = os.path.dirname(os.getcwd())

print()
if LOCALE == 'ko_KR':
    pprint('현재 버전 삭제 중...')
else:
    pprint('Deleting current version...')

for item in os.listdir(cwd):
    if item not in whitelist:
        try:
            item = os.path.join(cwd, item)
            if os.path.isdir(item):
                shutil.rmtree(item)
            elif os.path.isfile(item):
                os.remove(item)
        except Exception:
            pprint(f'Could not delete item {item}')

print()
if LOCALE == 'ko_KR':
    pprint('새 버전 압축 해제 중...')
else:
    pprint('Extracting new version...')

f.extractall()

print()
if LOCALE == 'ko_KR':
    pprint('업데이트 완료. 업데이터를 종료하고 프로그램을 다시 실행하세요.')
    print()
    pprint('----------------------------------------------------------')
    print()
    input('    Enter 키를 눌러서 나가기...')
else:
    pprint('Update complete. Please launch the application now.')
    print()
    pprint('----------------------------------------------------------')
    print()
    input('    Press Enter to exit...')

sys.exit(0)
