# Steam Account Switcher
쉽고 빠른 스팀 계정 전환

Python으로 작성됨

[This document is also available in English.](https://github.com/sw2719/steam-account-switcher/blob/master/README.md)

[Releases 에서 다운로드 하기](https://github.com/sw2719/steam-account-switcher/releases)

[작동 영상 보기](https://youtu.be/WFtv10RZ_UA)

STEAM은 Valve Corporation 의 등록상표입니다.

이 프로그램은 Steam 및 Valve 와 아무런 연관이 없습니다.

# 특징
* 몇 번의 클릭만으로 스팀 계정간 전환

* 계정을 전환할때마다 ID, 비밀번호, 그리고 스팀가드 코드조차 입력 할 필요 없음

* 프로그램 사용시 아이디만 필요. 비밀번호가 필요 없으므로 안전

* 스팀에서 아이디 자동 불러오기

* 자동 업데이트 내장

# 사용 방법
1. 압축을 원하는 폴더 풀기
2. exe 파일을 실행
**(이 프로그램은 레지스트리를 수정하므로 유해한 프로그램으로 진단될 수 있습니다. 또한 코드 서명이 되지 않았으므로 SmartScreen 경고가 나타날 수 있습니다.)**

3. 나타나는 팝업 창으로 스팀 계정을 가져오거나 메뉴 > 계정 추가로 수동 추가
* 계정 정보는 accounts.yml 에 저장됩니다.

4. 원하는 계정 이름이 표시된 버튼을 눌러 그 계정으로 전환
* 이미 자동로그인이 설정된 계정인경우, 아무 것도 입력할 필요 없이 자동으로 로그인 됩니다.

* 로그인 창이 표시되는 경우, 비밀번호를 입력한 후 비밀번호 기억을 꼭 체크한후 로그인 하시면 다음부터는 자동으로 로그인이 됩니다.

# 소스 코드 정보
* master를 제외한 모든 branch 는 개발 branch이며 작동을 보장하지 않습니다.
* Python 3.7 64-bit 으로 작성되었습니다.
* updater.py 는 cx_freeze 로 번들된 배포용 프로그램에서 작동하게 설계되었으므로 Python 인터프리터로 실행하지 마십시오.
* Requests, packaging, psutil, ruamel.yaml, gettext 모듈이 필요합니다.
* 소스코드 원문은 영어이며 gettext 로 한글로 번역됩니다.
