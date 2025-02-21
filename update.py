#!/usr/bin/env python3
import subprocess
import time
import os
import sys
import re

SCREEN_SESSION = "nexus"
LOG_FILE = "/tmp/nexus_screen.log"

def run_command(cmd_list, shell=False):
    """
    명령어(리스트)를 실행하는 함수.
    """
    subprocess.run(cmd_list, shell=shell, check=True)

def kill_all_screens():
    """
    현재 실행중인 모든 screen 세션을 찾아서 종료한다.
    """
    print("[INFO] screen 세션 목록 확인 중...")
    result = subprocess.run(["screen", "-ls"], capture_output=True, text=True)
    output = result.stdout

    for line in output.splitlines():
        line = line.strip()
        # 세션번호.세션명 형태 찾기
        match = re.search(r"(\d+\.[^\s]+)", line)
        if match:
            full_session_name = match.group(1)
            print(f"[INFO] '{full_session_name}' 스크린 세션 종료 중...")
            try:
                run_command(["screen", "-S", full_session_name, "-X", "quit"])
            except subprocess.CalledProcessError:
                print(f"[WARNING] '{full_session_name}' 종료 실패.")

def create_screen_session():
    """
    'nexus' 이름의 screen 세션을 새로 생성하고 로그 파일 설정을 진행한다.
    """
    print(f"[INFO] '{SCREEN_SESSION}' 스크린 세션 생성 중...")
    run_command(["screen", "-S", SCREEN_SESSION, "-dm", "bash"])
    run_command(["screen", "-S", SCREEN_SESSION, "-X", "logfile", LOG_FILE])
    run_command(["screen", "-S", SCREEN_SESSION, "-X", "log", "on"])

def send_to_screen(text):
    """
    screen 세션에 명령어나 응답을 전송하는 함수.
    """
    command = text + "\n"
    run_command(["screen", "-S", SCREEN_SESSION, "-X", "stuff", command])

def run_nexus_command():
    """
    Nexus CLI 설치 명령어를 screen 세션 내에서 실행한다.
    """
    print("[INFO] Nexus CLI 명령어 실행 중...")
    send_to_screen("curl https://cli.nexus.xyz/ | sh")

def monitor_log():
    """
    로그 파일을 모니터링하면서 특정 문자열을 감지하면
    해당 문자열에 맞는 응답을 전송하거나 스크립트를 종료한다.
    """
    print(f"[INFO] 로그 파일 모니터링 시작: {LOG_FILE}")
    while not os.path.exists(LOG_FILE):
        time.sleep(0.5)

    with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.2)
                continue

            print("[로그]", line.strip())

            # "Do you want to use the existing user account? (y/n)" or "you want to use the existing"
            if ("Do you want to use the existing user account? (y/n)" in line
                or "you want to use the existing" in line):
                print("[INFO] 계정 사용 여부 질문 감지 - 'y' 전송")
                send_to_screen("y")

            # "Fetching a task to prove from Nexus Orchestrator" 감지 시 스크립트 종료
            if "Fetching a task to prove from Nexus Orchestrator" in line:
                print("[INFO] 작업 요청 문구 감지 - 스크립트 종료")
                sys.exit(0)

def main():
    kill_all_screens()
    time.sleep(3)  # 스크린 종료 후 3초 대기
    create_screen_session()
    run_nexus_command()
    monitor_log()

if __name__ == "__main__":
    main()
