<img align="right" src="https://user-images.githubusercontent.com/22590718/89107306-1230d200-d46b-11ea-92ce-c4245d76f839.PNG">

# Steam Account Switcher
쉽고 빠르게 스팀 계정 간 전환

Python으로 작성됨

[This document is also available in English.](https://github.com/sw2719/steam-account-switcher/blob/master/README.md)

[Releases 에서 다운로드 하기](https://github.com/sw2719/steam-account-switcher/releases)

STEAM은 Valve Corporation 의 등록상표입니다.

이 프로그램은 Steam 및 Valve 와 아무런 연관이 없습니다.

# 특징
* 몇 번의 클릭만으로 스팀 계정간 전환

* 계정을 전환할때마다 ID, 비밀번호, 그리고 스팀가드 코드조차 입력 할 필요 없음

* 프로그램 사용시 비밀번호가 필요 없으므로 안전

* 스팀에서 아이디 자동 불러오기

* 자동 업데이트 내장

# 요구사항
* 64비트 Windows
* Steam 설치됨
* Visual Studio 2015 또는 2017용 Visual C++ 재배포 패키지
  - [다운로드](https://aka.ms/vs/16/release/vc_redist.x64.exe)

# 사용 방법
1. 압축을 원하는 폴더에 풀기
2. exe 파일을 실행
**(이 프로그램은 레지스트리를 수정하므로 유해한 프로그램으로 진단될 수 있습니다. 또한 코드 서명이 되지 않았으므로 SmartScreen 경고가 나타날 수 있습니다.)**

3. 나타나는 팝업 창으로 스팀 계정을 가져오거나 메뉴 > 계정 추가로 수동 추가
* 계정 정보는 accounts.yml 에 저장됩니다.

4. 원하는 계정 이름이 표시된 버튼을 눌러 그 계정으로 전환
* 처음 프로그램을 사용하는 경우, 로그인 창이 표시될 수 있습니다. 비밀번호 저장을 체크하고 로그인하면 다음에는 로그인 창없이 로그인됩니다.
  - 이 작업은 프로그램 사용 이전에 자동로그인하던 계정을 제외한 모든 계정에 필요합니다.
  - **계정을 더 추가할 경우, 그 계정에도 작업이 필요하며 일정 시간 로그인 하지 않으면, 자동로그인이 해제되어 다시 작업을 해주어야 합니다.**

# FAQ
* 로그인 창이 떠요!
  - 사용 방법-4를 보세요. 바로 위에 있네요.

* Windows SmartScreen 창이 떠요!
  - 추가 정보 누르고 실행을 누르세요. 코드 서명이 안 되있어서 그렇습니다. 왜 코드 서명을 안 했냐면, 돈이 들거든요. 아시다시피, 이 프로그램은 무료입니다.

* 요청 사항이 있습니다! / 문제가 있습니다!
  - 요청 사항이나 문제 보고는 언제나 환영입니다. Issue를 작성해주세요.

* 설정창이 이상합니다! (일부 요소가 표시되지 않음)
  - config.yml을 삭제해보세요.

# 소스 코드 정보
* master를 제외한 모든 branch 는 개발 branch이며 작동을 보장하지 않습니다.
* Python 3.8 64-bit 으로 작성되었습니다. 최소 Python 3.7이 필요합니다.
* updater.py 는 cx_freeze 로 번들된 배포용 프로그램에서 작동하게 설계되었으므로 Python 인터프리터로 실행하지 마세요.
* requirements.txt로 의존성을 설치하세요.
* 소스코드 원문은 영어이며 gettext 로 한글로 번역됩니다.
