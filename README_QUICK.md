````markdown
# 빠른 시작 — 최소 명령

이 문서는 프로젝트 루트에서 파이썬 가상환경(venv)을 생성하고, 필요한 패키지를 설치한 뒤 프로그램을 실행하는 최소 명령을 안내합니다. macOS + zsh 환경에서 동작합니다.

옵션 A — 제공된 스크립트 사용(권장):

```bash
# 스크립트가 가상환경을 만들고 실행하도록 bash로 실행합니다
bash quick_use.sh
```

옵션 B — zsh에서 수동으로 실행하기:

```bash
# 1. 가상환경 생성
python3 -m venv .venv

# 2. 활성화 (zsh)
source .venv/bin/activate

# 3. pip 업그레이드 및 의존성 설치
pip install --upgrade pip
pip install -r app/requirements.txt

# 4. 실행
python3 main.py
```

주의사항:
- `app/requirements.txt` 파일이 없으면 스크립트는 프로젝트 루트의 `requirements.txt`를 대신 사용하려 시도합니다.
- 스크립트 내부에서 venv를 활성화하면 그 프로세스 안에서만 활성화됩니다. 인터랙티브 셸에서 계속 사용하려면 직접 `source .venv/bin/activate`를 실행하세요.

````
# Quick start — minimal steps

This file provides the minimal commands to set up a Python virtual environment, install the project's dependencies, and run the program from the project root (works on macOS with zsh).

Option A — run the provided script (recommended):

```bash
# Run with bash so the script can create and run inside the venv
bash quick_use.sh
```

Option B — run the steps manually in zsh:

```bash
# 1. create virtual environment
python3 -m venv .venv

# 2. activate (zsh)
source .venv/bin/activate

# 3. upgrade pip and install requirements
pip install --upgrade pip
pip install -r app/requirements.txt

# 4. run
python3 main.py
```

Notes:
- If `app/requirements.txt` is missing, the script will try `requirements.txt` in the project root.
- Activating the venv inside the script only affects the script process; if you want the venv active in your interactive shell, run the `source .venv/bin/activate` command yourself.
