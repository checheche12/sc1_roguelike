"""Local record manager and explicit user-invoked patch/install/game launch UI."""
from __future__ import annotations

from datetime import datetime
import importlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .store import open_campaign_store
from .lifecycle import ManagerInstance
from .preferences import (PREFERENCES_PATH, startup_database, remember_database,
                          startup_game_path, remember_game_path)
from .auto_connect import AutoConnectTarget, publish_request, read_request, request_path
from sc1.bridge.discovery import discover_games
from sc1.campaign.catalog import ORIGINAL_PROFILE, missions_for_profile
from sc1.campaign.missions import load_missions, mission_for_id
from sc1.campaign.display_text import concise_description, current_owned_descriptions


def record_summary(state: dict) -> str:
    completed = [mission.label for mission in missions_for_profile(state["profile"])
                 if state["completed_mask"] & mission.completion_mask]
    if state["profile"] == ORIGINAL_PROFILE:
        canonical = [m for m in load_missions() if m["shared_reward_mission_id"] == m["mission_id"]]
        count = sum(bool(state["completed_mask"] & (1 << m["completion_bit"])) for m in canonical)
        return f"본편·브루드워 기록   |   완료 {count}/{len(canonical)}   |   저장 번호 {state['revision']}"
    return f"시험 기록   |   골드 {state['gold']}   |   저장 번호 {state['revision']}   |   완료 {', '.join(completed) or '없음'}"


def growth_summary(state: dict) -> str:
    mode = state["state"]
    if mode == "unsupported":
        return "시험 A/B 기록은 재능·저주 선택을 사용하지 않습니다."
    if mode == "not_started":
        return "게임 안에서 재능과 저주를 선택하세요. 선택 결과는 자동으로 저장됩니다."
    if mode == "legacy_complete":
        return "완료한 임무는 당시 저장한 성장으로 다시 플레이합니다."
    if mode == "waiting_next_map":
        upcoming = state["upcoming"]
        return f"선택 대기: 재능 {upcoming['talent']}회·저주 {upcoming['curse']}회. 게임의 선택창에서 고르세요."
    if state.get("phased_growth"):
        if mode == "choosing":
            pending = state["phase_pending"]
            return f"선택 대기: 재능 {pending['talent']}회·저주 {pending['curse']}회. 게임의 선택창에서 고르세요."
        completed = state["completed_phase"]
        return "선택한 재능·저주 저장 완료." if completed < 3 else "재능·저주 선택 완료."
    if mode == "in_mission":
        return "출전 성장 확정 · 재시작과 재연결에도 같은 재능·저주를 사용합니다."
    if mode == "ready":
        return "재능 3개·저주 2개 선택 완료 · 성장 지원 테란 1 지도에 연결하면 출전 구성이 확정됩니다."
    pending = state["pending"]
    return f"게임 안에서 남은 선택: 재능 {pending['talent']}회·저주 {pending['curse']}회. 게임 화면에서 선택해 주세요. 저장된 선택지는 재연결해도 바뀌지 않습니다."


def launch(database: Path | None = None, *, new_profile: str = ORIGINAL_PROFILE,
           auto_connect_target: AutoConnectTarget | None = None,
           preferences_path: Path = PREFERENCES_PATH) -> None:
    channel = request_path()
    prior = read_request(channel)
    with ManagerInstance() as instance:
        if not instance.acquired and auto_connect_target is not None:
            publish_request(channel, auto_connect_target)
            return
        root = tk.Tk()
        if not instance.acquired:
            root.withdraw()
            messagebox.showinfo("이미 실행 중", "스타1 성장 기록 관리자가 이미 열려 있습니다.\n작업 표시줄에서 기존 관리자 창을 사용해 주세요.", parent=root)
            root.destroy()
            return
        root.title("스타1 성장 기록 관리자 · 시험판")
        root.geometry(f"900x{min(930, root.winfo_screenheight() - 80)}")
        root.minsize(730, 660)
        try:
            database = startup_database(database, preferences_path=preferences_path)
        except OSError as exc:
            root.withdraw()
            messagebox.showwarning("마지막 기록 다시 선택", str(exc), parent=root)
            selected = filedialog.askopenfilename(parent=root, title="계속할 기록 파일 선택",
                                                 filetypes=[("SQLite 기록", "*.sqlite3")])
            if not selected:
                root.destroy()
                return
            database = Path(selected)
            root.deiconify()
        try:
            app = ManagerWindow(root, database, new_profile=new_profile,
                                auto_connect_target=auto_connect_target, command_channel=channel,
                                prior_command_token=prior[0] if prior else None,
                                preferences_path=preferences_path)
        except Exception as exc:
            messagebox.showerror("기록 파일을 열 수 없음", str(exc), parent=root)
            root.destroy()
            return
        root.protocol("WM_DELETE_WINDOW", app.close)
        try:
            root.mainloop()
        finally:
            app.finish_bridge()


class ManagerWindow:
    def __init__(self, root: tk.Tk, database: Path, *, new_profile: str = ORIGINAL_PROFILE,
                 auto_connect_target: AutoConnectTarget | None = None,
                 command_channel: Path | None = None, prior_command_token=None,
                 preferences_path: Path | None = None):
        self.root = root
        self.database = database.resolve()
        self.store = open_campaign_store(self.database, new_profile=new_profile)
        self.preferences_path = preferences_path
        self.process = None
        self.last_connection_error = None
        self.events = queue.Queue()
        self.closed = False
        self.discovery_token = 0
        self.discovering = False
        self.discovery_automatic = False
        self.auto_connect_enabled = auto_connect_target is not None
        self.auto_connect_target = auto_connect_target
        self.command_channel = command_channel
        self.command_token = prior_command_token
        self.summary = tk.StringVar()
        self.profile_hint = tk.StringVar()
        self.growth_hint = tk.StringVar()
        self.connection = tk.StringVar(value="게임 미연결")
        self.installation_busy = False
        selected_game = startup_game_path(preferences_path=preferences_path or PREFERENCES_PATH)
        self.game_path = tk.StringVar(value=str(selected_game) if selected_game else "")
        self.installation_hint = tk.StringVar(value="설치 경로를 확인한 뒤 스타크래프트 시작을 누르세요. 패치가 없으면 원본 캠페인이 실행됩니다.")
        outer = ttk.Frame(root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="스타1 캠페인 성장 기록", font=("Malgun Gothic", 19, "bold")).pack(anchor="w")
        ttk.Label(outer, text="스타1 본편·브루드워 캠페인 · 게임 안에서 고른 재능·저주와 완료 기록 저장",
                  wraplength=820).pack(anchor="w", pady=(6, 2))
        ttk.Label(outer, text="재능·저주는 게임 안에서 선택합니다. 선택 결과는 자동으로 저장됩니다.",
                  wraplength=820).pack(anchor="w", pady=(0, 12))
        state = ttk.LabelFrame(outer, text="로컬 기록", padding=12)
        state.pack(fill="x")
        self.db_label = ttk.Label(state, text=str(self.database), wraplength=790)
        self.db_label.pack(anchor="w")
        ttk.Label(state, text="마지막으로 연 기록을 다음 실행에서도 자동으로 사용합니다.").pack(anchor="w", pady=(4, 0))
        ttk.Label(state, textvariable=self.profile_hint, wraplength=790).pack(anchor="w", pady=(4, 0))
        ttk.Label(state, textvariable=self.summary, font=("Malgun Gothic", 12)).pack(anchor="w", pady=8)
        row = ttk.Frame(state)
        row.pack(fill="x")
        self.new_record_button = ttk.Button(row, text="새 캠페인 기록…", command=self.new_database)
        self.new_record_button.pack(side="left")
        self.open_record_button = ttk.Button(row, text="다른 기록 열기…", command=self.open_database)
        self.open_record_button.pack(side="left", padx=6)
        ttk.Button(row, text="새로 고침", command=self.refresh).pack(side="left")
        ttk.Label(state, textvariable=self.growth_hint, wraplength=790).pack(anchor="w", pady=(10, 6))
        self.growth_button = ttk.Button(state, text="보유 재능·저주 보기", command=self.show_growth)
        self.growth_button.pack(anchor="w")
        install = ttk.LabelFrame(outer, text="캠페인 패치 · 게임 실행", padding=10)
        install.pack(fill="x", pady=(10, 0))
        path_row = ttk.Frame(install)
        path_row.pack(fill="x")
        ttk.Label(path_row, text="스타크래프트 설치 경로").pack(side="left")
        self.game_path_entry = ttk.Entry(path_row, textvariable=self.game_path)
        self.game_path_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.browse_game_button = ttk.Button(path_row, text="찾기…", command=self.browse_game_path)
        self.browse_game_button.pack(side="left")
        actions = ttk.Frame(install)
        actions.pack(fill="x", pady=(8, 5))
        self.installation_buttons = []
        for index, (label, action) in enumerate((("설치 상태 확인", "inspect"),
                ("캠페인 패치 설치 / 업데이트", "install"), ("이전 패치 복원", "restore"),
                ("원본 캠페인으로 되돌리기", "original"), ("스타크래프트 시작", "launch"))):
            button = ttk.Button(actions, text=label, command=lambda selected=action: self.installation_action(selected))
            button.grid(row=index // 3, column=index % 3, sticky="w", padx=(0, 5), pady=(0, 5))
            self.installation_buttons.append(button)
        ttk.Label(install, textvariable=self.installation_hint, wraplength=810).pack(anchor="w")
        live = ttk.LabelFrame(outer, text="스타크래프트 연결 · 32/64비트", padding=10)
        live.pack(fill="x", pady=12)
        ttk.Label(live, text="성장 모드로 실행한 게임에 현재 기록을 연결합니다. 원본 캠페인은 성장 기록 없이 실행합니다.",
                  wraplength=790).pack(anchor="w")
        ttk.Label(live, textvariable=self.connection, wraplength=790).pack(anchor="w", pady=(4, 8))
        controls = ttk.Frame(live)
        controls.pack(fill="x")
        self.connect_button = ttk.Button(controls, text="스타1 찾아 연결", command=lambda: self.start_bridge(True))
        self.connect_button.pack(side="left", padx=3)
        self.inspect_button = ttk.Button(controls, text="연결 상태 검사", command=lambda: self.start_bridge(False))
        self.inspect_button.pack(side="left", padx=3)
        ttk.Button(controls, text="연결 중지", command=self.stop_bridge).pack(side="left", padx=3)
        ttk.Label(live, text="게임으로 돌아가 지원 임무를 시작하세요. 복원 안내가 나오면 플레이할 수 있습니다.",
                  wraplength=790).pack(anchor="w", pady=(8, 0))
        tools = ttk.Frame(outer)
        tools.pack(fill="x")
        ttk.Button(tools, text="게임 없이 관리자 모의 검증", command=self.simulate).pack(side="left")
        ttk.Label(tools, text="별도 임시 기록 사용 · 현재 저장 파일에 영향 없음").pack(side="left", padx=8)
        self.log = tk.Text(outer, height=6, wrap="word", font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, pady=(12, 0))
        self.log.configure(state="disabled")
        self.refresh()
        self.remember_current_database()
        self.root.after(250, self.drain_events)
        if auto_connect_target is not None:
            self.connection.set("자동 연결 대기 · 실행기에서 스타1을 시작하는 중입니다.")
        self.root.after(500, self.auto_connect_tick)


    def browse_game_path(self):
        selected = filedialog.askdirectory(parent=self.root, title="스타크래프트 설치 폴더 선택",
                                            initialdir=self.game_path.get())
        if selected:
            self.game_path.set(selected)
            self.installation_hint.set("설치 상태 확인 또는 캠페인 패치 설치 / 업데이트를 누르세요.")

    def _installation_controls(self, busy):
        self.installation_busy = busy
        controls = [self.new_record_button, self.open_record_button, self.browse_game_button,
                    self.game_path_entry, self.connect_button, self.inspect_button, *self.installation_buttons]
        for control in controls:
            control.configure(state="disabled" if busy else "normal")

    def installation_action(self, action):
        if self.closed or self.installation_busy:
            return
        if action not in ("inspect", "install", "restore", "original", "launch"):
            raise ValueError("Unknown installation action")
        if action in ("launch", "original"):
            try:
                self.stop_bridge()
                self.finish_bridge()
                self.process = None
                self.remember_current_database()
            except (OSError, subprocess.TimeoutExpired) as exc:
                messagebox.showerror("기존 연결 정리 실패", str(exc), parent=self.root)
                return
        target = self.game_path.get().strip()
        if not target:
            messagebox.showerror("설치 경로 선택", "스타크래프트 설치 폴더 또는 StarCraft.exe 경로를 입력해 주세요.", parent=self.root)
            return
        selected_database = str(self.database)
        allow_growth = self.store.status()["profile"] == ORIGINAL_PROFILE
        self._installation_controls(True)
        labels = {"inspect": "설치 상태 확인 중…", "install": "캠페인 패치 파일 복사 및 검증 중…",
                  "restore": "이전 패치 복원 중…", "original": "패치를 보관하고 원본 캠페인으로 전환 중…",
                  "launch": "설치 상태에 맞춰 스타크래프트 시작 중…"}
        self.installation_hint.set(labels[action])

        def work():
            try:
                try:
                    installation = importlib.import_module("sc1.manager.installation")
                except ModuleNotFoundError as exc:
                    if exc.name != "sc1.manager.installation":
                        raise
                    self.events.put(("installation_done", action, {"status": "unavailable",
                        "message": "캠페인 패치 기능을 준비 중입니다. 잠시 뒤 다시 눌러 주세요."}, None, selected_database))
                    return
                callback = {"inspect": installation.inspect_installation,
                            "install": installation.install_package,
                            "restore": installation.restore_installation,
                            "original": installation.restore_original_campaign,
                            "launch": installation.launch_campaign}[action]
                result = callback(target, with_manager=False, allow_growth=allow_growth) if action == "launch" else callback(target)
                self.events.put(("installation_done", action, result, None, selected_database))
            except Exception as exc:
                self.events.put(("installation_done", action, None, str(exc), selected_database))
        threading.Thread(target=work, daemon=True).start()

    def installation_done(self, action, result, error, selected_database):
        if self.closed:
            return
        self._installation_controls(False)
        if error:
            self.installation_hint.set(error)
            self.append(f"캠페인 패치/실행: {error}")
            messagebox.showerror("캠페인 작업 실패", error, parent=self.root)
            return
        result = result or {}
        message = result.get("message", result.get("status", "완료"))
        self.installation_hint.set(message)
        self.append(message)
        if result.get("retained_installation"):
            self.append("패치 보관 위치: " + result["retained_installation"])
        if self.preferences_path is not None and result.get("status") in ("ready", "not_installed", "installed", "restored", "original", "started"):
            try:
                remember_game_path(Path(self.game_path.get()), preferences_path=self.preferences_path)
            except OSError as exc:
                self.append(f"설치 경로 설정 저장 실패: {exc}")
        if result.get("mode") == "original" and result.get("status") in ("original", "started"):
            self.auto_connect_enabled = False
            self.auto_connect_target = None
            self.connection.set("원본 캠페인 · 성장 기록을 연결하지 않습니다.")
            return
        if action == "launch" and result.get("status") == "started":
            if str(self.database) != selected_database:
                self.append("실행 중 선택 기록이 변경되어 자동 연결을 시작하지 않았습니다.")
                return
            self.auto_connect_target = AutoConnectTarget(result["executable"], int(result["started_after"]))
            self.auto_connect_enabled = True
            self.last_connection_error = None
            self.connection.set("자동 연결 대기 · 현재 기록으로 시작한 스타크래프트를 찾는 중입니다.")

    def auto_connect_tick(self):
        if self.closed:
            return
        if self.command_channel is not None:
            request = read_request(self.command_channel)
            if request and request[0] != self.command_token:
                self.command_token, target = request
                self.auto_connect_target = target
                self.auto_connect_enabled = True
                self.append("캠페인 실행기의 자동 연결 요청을 받았습니다.")
                # Preserve the currently selected record. Only stop our bridge
                # child if a different launcher-created game is requested.
                if self.process is not None or self.discovering:
                    self.stop_bridge(disable_auto=False)
        if self.auto_connect_enabled and self.process is None and not self.discovering:
            self.start_bridge(True, automatic=True)
        self.root.after(1500, self.auto_connect_tick)

    def append(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", f"[{datetime.now():%H:%M:%S}] {text}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def refresh(self):
        try:
            state = self.store.status()
            self.summary.set(record_summary(state))
            self.profile_hint.set("본편·브루드워 프로필 · 완료한 임무도 당시 성장으로 다시 플레이할 수 있습니다."
                                  if state["profile"] == ORIGINAL_PROFILE else
                                  "시험 프로필 · 기존 A/B 저장 검증 기록입니다. 본편 지도에는 새 본편 기록을 사용하세요.")
            self.growth_hint.set(growth_summary(state["growth_selection"]))
            self.growth_button.configure(state="normal" if state["profile"] == ORIGINAL_PROFILE else "disabled")
        except Exception as exc:
            self.append(f"기록 읽기 실패: {exc}")

    def show_growth(self):
        store = self.store
        try:
            current = current_owned_descriptions(store.growth_status(),store.runtime_catalog_path)
        except Exception as exc:
            messagebox.showerror("보유 성장을 읽을 수 없음", str(exc), parent=self.root)
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("보유 재능·저주 · 캠페인별 기록")
        dialog.geometry("740x740")
        dialog.minsize(660, 540)
        dialog.transient(self.root)
        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="보유 재능·저주", font=("Malgun Gothic", 17, "bold")).pack(anchor="w")
        ttk.Label(frame, text=store.path.name).pack(anchor="w", pady=(2, 6))
        ttk.Label(frame, text="재능·저주는 게임 안에서 선택합니다. 이 창은 저장된 보유 성장과 남은 선택 수를 보여 줍니다.", wraplength=650).pack(anchor="w", pady=(0, 8))
        campaign_labels={1:"본편 테란",2:"본편 저그",3:"본편 프로토스",4:"브루드워 프로토스",5:"브루드워 테란",6:"브루드워 저그",7:"어둠의 기원 · 비밀 임무"}
        selected_campaign=tk.StringVar(value=campaign_labels[mission_for_id(current['mission'])['campaign_id']])
        selector=ttk.Combobox(frame,textvariable=selected_campaign,values=list(campaign_labels.values()),state="readonly")
        selector.pack(anchor="w",fill="x",pady=(0,8))
        def selected_status():
            cid=next(key for key,label in campaign_labels.items() if label==selected_campaign.get())
            return current_owned_descriptions(store.growth_status_for_campaign(cid),store.runtime_catalog_path)
        hint = tk.StringVar()
        ttk.Label(frame, textvariable=hint, wraplength=650).pack(anchor="w", pady=(0, 10))
        scroll = ttk.Frame(frame)
        scroll.pack(fill="both", expand=True)
        canvas = tk.Canvas(scroll, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        content = ttk.Frame(canvas)
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(content_window, width=event.width))
        notice = tk.StringVar()
        ttk.Label(frame, textvariable=notice, wraplength=650, foreground="#a43b29").pack(anchor="w", pady=(10, 6))
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="닫기", command=dialog.destroy).pack(side="right")
        shown_key = None

        def render(value):
            nonlocal shown_key
            shown_key = (value["mission"], value["state"], value["revision"], value.get("phased_growth"),
                         value.get("requested_phase"), value.get("completed_phase"))
            hint.set(growth_summary(value))
            for child in content.winfo_children():
                child.destroy()
            ttk.Label(content, text="현재 보유 성장", font=("Malgun Gothic", 12, "bold")).pack(anchor="w", pady=(0, 8))
            owned = value.get("talents", []) + value.get("curses", [])
            if not owned:
                ttk.Label(content, text="아직 선택한 항목이 없습니다.").pack(anchor="w")
            for item in owned:
                suffix = f" · {item['stacks']}중첩" if "stacks" in item else ""
                ttk.Label(content, text=f"{item['name']}{suffix}", font=("Malgun Gothic", 10, "bold")).pack(anchor="w", pady=(8, 2))
                ttk.Label(content, text=concise_description(item), wraplength=620, justify="left").pack(anchor="w")
            canvas.yview_moveto(0)
            self.refresh()

        def poll():
            if not dialog.winfo_exists():
                return
            try:
                value = selected_status()
                key = (value["mission"], value["state"], value["revision"], value.get("phased_growth"),
                       value.get("requested_phase"), value.get("completed_phase"))
                if key != shown_key:
                    render(value)
            except Exception as exc:
                notice.set(f"성장 기록 확인 실패: {exc}")
            dialog.after(750, poll)

        selector.bind("<<ComboboxSelected>>", lambda event: render(selected_status()))
        render(current)
        dialog.after(750, poll)
        dialog.grab_set()
        self.root.wait_window(dialog)
        self.refresh()

    def remember_current_database(self):
        if self.preferences_path is None:
            return
        try:
            remember_database(self.database, preferences_path=self.preferences_path)
        except OSError as exc:
            self.append(f"현재 기록은 열었지만 다음 실행용 선택을 저장하지 못했습니다: {exc}")
            messagebox.showwarning("마지막 기록 설정 저장 실패", str(exc), parent=self.root)

    def switch_database(self, path):
        if getattr(self, "installation_busy", False):
            return False
        try:
            store = open_campaign_store(path)
        except Exception as exc:
            messagebox.showerror("기록 파일 오류", str(exc), parent=self.root)
            return False
        if store.path == self.database:
            self.remember_current_database()
            return True
        # Finish the old writer before exposing the new record. A live map
        # already has a growth snapshot, so it must not be rebound to a new DB.
        was_connected = self.process is not None or self.discovering or self.auto_connect_enabled
        self.stop_bridge()
        try:
            self.finish_bridge()
        except (OSError, subprocess.TimeoutExpired) as exc:
            messagebox.showerror("연결 정리 실패", str(exc), parent=self.root)
            return False
        self.process = None
        self.last_connection_error = None
        self.set_connection_busy(False)
        self.store, self.database = store, store.path
        self.remember_current_database()
        self.db_label.configure(text=str(self.database))
        self.connection.set("기록 변경 완료 · 다음 캠페인 실행부터 이 기록을 사용합니다.")
        if was_connected:
            self.append("기존 연결을 정리하고 기록을 변경했습니다. 현재 임무에 적용된 성장은 유지되며 다음 캠페인 실행부터 새 기록을 사용합니다.")
        self.refresh()
        return True

    def new_database(self):
        path = filedialog.asksaveasfilename(parent=self.root, title="새 본편 기록 파일", defaultextension=".sqlite3",
                                          initialdir=str(self.database.parent),
                                          initialfile=f"original_{datetime.now():%Y%m%d_%H%M%S}.sqlite3",
                                          filetypes=[("SQLite 기록", "*.sqlite3")])
        if path:
            if Path(path).exists():
                messagebox.showinfo("기존 파일 보호", "새 이름을 선택해 주세요. 기존 기록은 덮어쓰지 않습니다.", parent=self.root)
                return
            self.switch_database(path)

    def open_database(self):
        path = filedialog.askopenfilename(parent=self.root, title="본편 또는 기존 시험 기록 열기",
                                         initialdir=str(self.database.parent), filetypes=[("SQLite 기록", "*.sqlite3")])
        if path:
            self.switch_database(path)

    def start_bridge(self, write, *, automatic=False):
        if self.process is not None or self.discovering:
            self.append("이전 연결 작업이 끝나거나 연결을 중지한 뒤 다시 실행하세요.")
            return
        if not automatic:
            self.auto_connect_enabled = False
        self.discovery_token += 1
        token = self.discovery_token
        self.discovering = True
        self.discovery_automatic = automatic
        self.set_connection_busy(True)
        self.connection.set("실행 중인 스타1을 찾는 중…")

        def discover():
            try:
                games = discover_games()
                self.events.put(("discovered", token, write, games))
            except Exception as exc:
                self.events.put(("discovery_error", token, str(exc)))
        threading.Thread(target=discover, daemon=True).start()

    def set_connection_busy(self, busy):
        for button in (self.connect_button, self.inspect_button):
            button.configure(state="disabled" if busy else "normal")

    def discovered(self, token, write, games):
        if self.closed or token != self.discovery_token:
            return
        self.discovering = False
        self.set_connection_busy(False)
        compatible = [game for game in games if game.architecture in ("x86", "x86_64")]
        automatic = getattr(self, "discovery_automatic", False)
        if automatic and self.auto_connect_target is not None:
            compatible = [game for game in compatible if self.auto_connect_target.matches(game)]
        if not compatible:
            if automatic:
                self.connection.set("자동 연결 대기 · 실행기에서 시작한 스타1을 기다리는 중입니다.")
                return
            if games:
                message = "지원하지 않는 실행 형식의 스타1입니다. 32비트 또는 64비트 Windows 버전을 사용해 주세요."
            else:
                message = "스타1을 찾지 못했습니다. 배틀넷에서 스타크래프트를 실행한 뒤 다시 연결해 주세요."
            self.connection.set(message)
            self.append(message)
            return
        game = compatible[0] if len(compatible) == 1 else self.choose_game(compatible)
        if game is None:
            self.auto_connect_enabled = False
            self.connection.set("연결을 취소했습니다.")
            return
        self.launch_bridge(game, write)

    def choose_game(self, games):
        dialog = tk.Toplevel(self.root)
        dialog.title("연결할 스타1 선택")
        dialog.transient(self.root)
        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="스타1이 여러 개 실행 중입니다. 캠페인 지도를 연 게임을 선택하세요.").pack(anchor="w", pady=(0, 12))
        selection = tk.IntVar(value=-1)
        result = []
        for index, game in enumerate(games):
            ttk.Radiobutton(frame, text=f"게임 {index + 1} · {game.label}", variable=selection,
                            value=index).pack(anchor="w", pady=6)

        def accept():
            if 0 <= selection.get() < len(games):
                result.append(games[selection.get()])
                dialog.destroy()

        row = ttk.Frame(frame)
        row.pack(anchor="e", pady=(12, 0))
        ttk.Button(row, text="취소", command=dialog.destroy).pack(side="left", padx=6)
        ttk.Button(row, text="선택한 게임에 연결", command=accept).pack(side="left")
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return result[0] if result else None

    def launch_bridge(self, game, write):
        command = [sys.executable, "-u", "-m", "sc1.bridge", "run" if write else "scan",
                   "--pid", str(game.pid), "--expected-start-time", str(game.started_at)]
        if write:
            command += ["--database", str(self.database), "--attach-write", "--exit-with-manager"]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            process = subprocess.Popen(command, cwd=Path(__file__).resolve().parents[2], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", creationflags=flags,
                                       close_fds=True,
                                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        except OSError as exc:
            self.auto_connect_enabled = False
            self.append(f"연결 프로그램 실행 실패: {exc}")
            self.connection.set("연결을 시작하지 못했습니다. 아래 상세 기록을 확인하세요.")
            return
        self.process = process
        self.last_connection_error = None
        self.set_connection_busy(True)
        self.connection.set("게임 확인 중 · 현재 기록에 맞는 지원 지도를 시작해 주세요" if write else "연결 상태를 읽기 전용 검사 중")
        def read_output():
            try:
                for line in process.stdout:
                    self.events.put(("output", process, line.rstrip()))
            finally:
                process.stdout.close()
                code = process.wait()
                process.stdin.close()
                self.events.put(("exit", process, code))
        threading.Thread(target=read_output, daemon=True).start()

    def stop_bridge(self, *, disable_auto=True):
        if disable_auto:
            self.auto_connect_enabled = False
        self.discovery_token += 1
        if self.discovering:
            self.discovering = False
            self.connection.set("게임 찾기를 취소했습니다.")
            self.set_connection_busy(False)
        if self.process and self.process.poll() is None:
            process = self.process
            process.stdin.close()
            self.root.after(2000, lambda: self.terminate_bridge(process))
            self.connection.set("연결을 정리하는 중…")
            self.append("연결 프로그램 중지를 요청했습니다. 게임 프로세스는 유지됩니다.")

    @staticmethod
    def terminate_bridge(process):
        if process.poll() is None:
            process.terminate()  # Only the child created by this manager.

    def finish_bridge(self):
        """Release the writer before allowing another manager to start."""
        process = self.process
        if process is None:
            return
        process.stdin.close()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.terminate_bridge(process)
            process.wait(timeout=3)

    def simulate(self):
        from .__main__ import run_demo
        try:
            with tempfile.TemporaryDirectory(prefix="sc1-ui-demo-") as tmp:
                result = run_demo(Path(tmp) / "probe.sqlite3")
            self.append(f"관리자 모의 검증 통과: 저장 123 / 중복 지급 없음 / B 복원 {result['restored_in_probe_b']['gold']}. 실제 게임 테스트는 아닙니다.")
        except Exception as exc:
            self.append(f"관리자 모의 검증 실패: {exc}")

    def drain_events(self):
        if self.closed:
            return
        while not self.events.empty():
            item = self.events.get_nowait()
            if isinstance(item, tuple):
                if item[0] == "installation_done":
                    self.installation_done(*item[1:])
                elif item[0] == "discovered":
                    self.discovered(*item[1:])
                elif item[0] == "discovery_error":
                    _, token, error = item
                    if token == self.discovery_token:
                        self.discovering = False
                        self.auto_connect_enabled = False
                        self.set_connection_busy(False)
                        self.connection.set("게임을 찾지 못했습니다. 아래 상세 기록을 확인하세요.")
                        self.append(f"스타1 찾기 실패: {error}")
                elif item[0] == "exit":
                    _, process, code = item
                    if self.process is process:
                        self.process = None
                        self.set_connection_busy(False)
                        if self.last_connection_error:
                            self.connection.set(self.last_connection_error)
                        elif code == 0:
                            self.connection.set("검사 또는 연결이 끝났습니다. 다시 연결할 수 있습니다.")
                        else:
                            self.auto_connect_enabled = False
                            self.connection.set("연결이 끝났습니다. 아래 상세 기록을 확인한 뒤 다시 연결해 주세요.")
                    self.append(f"연결 프로그램 종료: {code}")
                elif item[0] == "output":
                    _, process, line = item
                    self.append(line)
                    if self.process is process:
                        self.update_connection_status(line)
            else:
                self.append(item)
                self.update_connection_status(item)
        self.refresh()
        self.root.after(500, self.drain_events)

    def update_connection_status(self, line):
        try:
            event = json.loads(line)
        except (ValueError, TypeError):
            return
        if not isinstance(event, dict):
            return
        statuses = {
            "choice_offered": "게임 안에 재능·저주 선택지가 준비되었습니다. 게임의 선택창에서 고르세요.",
            "waiting_for_ingame_choice": "게임 안에서 재능·저주 선택을 기다리는 중입니다. 선택 결과는 자동으로 저장됩니다.",
            "waiting_for_choices": "게임 안에서 재능·저주 선택을 마쳐 주세요. 선택 결과는 자동으로 저장됩니다.",
            "waiting_for_growth": "게임 안에서 재능·저주 선택을 마쳐 주세요. 선택 결과는 자동으로 저장됩니다.",
            "waiting_for_map": "스타1 연결 대기 · 현재 기록에 맞는 지원 지도를 시작해 주세요.",
            "rebinding_map": "임무 전환 감지 · 현재 기록을 유지하며 새 지도의 연결을 기다리는 중입니다.",
            "map_rebound": "새 지도에 다시 연결했습니다. 현재 기록을 복원하는 중입니다.",
            "waiting_for_unpause": "게임으로 돌아가 일시 정지를 해제해 주세요.",
            "waiting_for_heartbeat": "게임의 응답을 기다리는 중…",
            "restored": "연결 완료 · 성장 기록을 복원했습니다.",
            "running": "연결 중 · 임무를 진행해 주세요.",
            "committed": "저장 완료 · 성장 기록을 보관했습니다.",
            "saved": "성장 기록 저장 완료.",
            "map_error": "지도에서 오류가 발생했습니다. 아래 상세 기록을 확인하세요.",
        }
        if event.get("status") in statuses:
            text = statuses[event["status"]]
            self.connection.set(text)
        elif event.get("event") == "scan" and not event.get("candidates"):
            self.connection.set("지원 지도가 아직 감지되지 않았습니다. 현재 기록에 맞는 지도를 시작해 주세요.")
        elif event.get("event") == "error":
            if event.get("type") == "WriterBusyError":
                self.last_connection_error = "다른 관리자에서 이미 연결 중입니다. 기존 창을 사용하거나 그 창에서 연결을 중지한 뒤 다시 연결하세요."
            elif "profile_mismatch" in str(event.get("message", "")):
                self.last_connection_error = "지도와 기록의 프로필이 다릅니다. 본편 지도에는 본편 기록, 시험 A/B에는 기존 시험 기록을 열어 주세요."
            else:
                self.last_connection_error = "연결에 실패했습니다. 아래 상세 기록을 확인하세요."
            # A disappearing/restarted map and a closed game can reconnect. A
            # storage/profile/ownership failure needs attention, not a retry loop.
            message = str(event.get("message", ""))
            transient = event.get("type") == "BridgeError" and any(
                marker in message for marker in ("스타1이 종료", "heartbeat stopped", "signature or protocol version changed"))
            if not transient:
                self.auto_connect_enabled = False
            self.connection.set(self.last_connection_error)

    def close(self):
        self.closed = True
        self.stop_bridge()
        self.root.destroy()
