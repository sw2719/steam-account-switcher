<img align="right" src="https://user-images.githubusercontent.com/22590718/111099662-551e6080-8589-11eb-8927-e2cf055bcc06.PNG">

# Steam Account Switcher
쉽고 빠르게 다른 스팀 계정으로 로그인하세요!

[This document is also available in English.](https://github.com/sw2719/steam-account-switcher/blob/master/README.md)

[Releases에서 다운로드 하기](https://github.com/sw2719/steam-account-switcher/releases)

STEAM은 Valve Corporation 의 등록상표입니다.

이 프로그램은 Steam 및 Valve 와 아무런 연관이 없습니다.

# 특징
* 몇 번의 클릭만으로 스팀 계정간 전환할 수 있습니다.

* 계정을 전환할때마다 ID, 비밀번호, 그리고 스팀가드 코드조차 입력 할 필요 없습니다.

* 프로그램 사용시 비밀번호가 필요 없으므로 안전합니다.

* 스팀에서 계정을 자동으로 불러올 수 있습니다.

* 자동 업데이트가 내장되어 있습니다.

# 요구사항
* Windows 운영 체제 (2.7 이상 버전에서는 64비트가 요구되지 않습니다)
* Steam 이 설치되어 있어야 함
* Visual Studio 2015 또는 2017용 Visual C++ 재배포 패키지
  - 이미 설치되어 있을 가능성이 높지만, 만약 없다면 아래에서 다운로드 가능합니다.
  - [32비트 다운로드](https://aka.ms/vs/16/release/vc_redist.x32.exe)
  - [64비트 다운로드](https://aka.ms/vs/16/release/vc_redist.x64.exe)

# 사용 방법
1. 압축을 원하는 폴더에 푸세요
2. exe 파일을 실행하세요
**(이 프로그램은 레지스트리를 수정하므로 유해한 프로그램으로 진단될 수 있습니다. 또한 코드 서명이 되지 않았으므로 SmartScreen 경고가 나타날 수 있습니다.)**

3. 메뉴 > Steam에서 계정 불러오기로 스팀 계정을 가져오거나 메뉴 > 계정 추가로 수동 추가하세요
* 계정 정보는 accounts.yml 에 저장됩니다.

4. 원하는 계정 이름이 표시된 버튼을 눌러 그 계정으로 전환하세요
* 처음 프로그램을 사용하는 경우, 로그인 창이 표시될 수 있습니다. 비밀번호 저장을 체크하고 로그인하면 다음에는 로그인 창없이 로그인됩니다.
  - 이 작업은 프로그램 사용 이전에 자동로그인하던 계정을 제외한 모든 계정에 필요합니다.
  - **계정을 더 추가할 경우, 그 계정에도 작업이 필요하며 일정 시간 로그인 하지 않으면, 자동로그인이 해제되어 다시 위 과정을 진행해야 합니다.**

# FAQ
* 로그인 창이 떠요!
  - 사용 방법 4번을 보세요. 바로 위에 있네요.

* Windows SmartScreen 창이 떠요!
  - 추가 정보 누르고 실행을 누르세요. 코드 서명이 안 돼있어서 그렇습니다. 왜 코드 서명을 안 했냐면, 돈이 들거든요. 아시다시피, 이 프로그램은 무료입니다.

* 요청 사항이 있습니다! / 문제가 있습니다!
  - 요청 사항이나 문제 보고는 언제나 환영입니다. Issue를 작성해주세요.

* 설정창이 이상합니다! (일부 요소가 표시되지 않음)
  - config.yml을 삭제해보세요.

# 소스 코드 정보
* master를 제외한 모든 branch는 개발 branch이며 작동을 보장하지 않습니다.
* 소스를 실행하려면 최소 Python 3.7이 필요합니다.
* updater.py 는 cx_freeze 로 번들된 배포용 프로그램에서 작동하게 설계되었습니다.
* 소스코드 원문은 영어이며 gettext 로 한글로 번역됩니다.
