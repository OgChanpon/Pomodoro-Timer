import tkinter as tk
from tkinter import messagebox
import json
import os
import math
import sys # EXE化のためにsysをインポート

# --- 音声再生ライブラリのインポート ---
try:
    from playsound import playsound
    HAS_PLAYSOUND = True
except ImportError:
    HAS_PLAYSOUND = False
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# --- 定数 ---
PINK = "#e2979c"
RED = "#e7305b"
GREEN = "#9bdeac"
YELLOW = "#f7f5dd"
FONT_NAME = "Courier"
CONFIG_FILE = "pomodoro_config.json"

# --- グローバル変数 ---
reps = 0
timer = None
is_paused = False
paused_time = 0

# --- EXE化のためのリソースパス解決関数 ---
def resource_path(relative_path):
    """ EXE化した後でもリソースファイル（画像や音声）を見つけられるようにする関数 """
    try:
        # PyInstallerが作成した一時フォルダのパスを取得
        base_path = sys._MEIPASS
    except Exception:
        # 通常のPython環境で実行している場合
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- EXE化対応: ファイルパスをresource_path経由で取得 ---
AUDIO_MP3_FILE = resource_path("bell.mp3")
AUDIO_WAV_FILE = resource_path("bell.wav")

# --- 設定の保存と読み込み ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"work_min": 25, "short_break_min": 5, "long_break_min": 30, "pomodoros": 0}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# --- タイマーリセット ---
def reset_timer():
    global reps, is_paused
    if timer:
        window.after_cancel(timer)
    reps = 0
    is_paused = False
    title_label.config(text="タイマー", fg=GREEN)
    timer_label.config(text="00:00")
    start_button.config(text="スタート")
    pomodoro_count_entry.delete(0, tk.END)
    pomodoro_count_entry.insert(0, str(config["pomodoros"]))
    update_pomodoro_display()

# --- ポモドーロカウンター ---
def update_pomodoro_display():
    try:
        pomodoros_done = int(pomodoro_count_entry.get())
        check_marks = "✔" * (pomodoros_done % 4)
        checkmark_label.config(text=check_marks)
    except ValueError:
        checkmark_label.config(text="")

def reset_pomodoro_count():
    if messagebox.askokcancel("確認", "本当にカウンターをリセットしますか？"):
        pomodoro_count_entry.delete(0, tk.END)
        pomodoro_count_entry.insert(0, "0")
        update_settings()

# --- タイマーメカニズム ---
def start_timer():
    global reps, is_paused
    try:
        update_settings()
    except ValueError:
        messagebox.showerror("入力エラー", "タイマーとカウンターには半角数字を入力してください。")
        return

    if is_paused:
        is_paused = False
        start_button.config(text="一時停止")
        countdown(paused_time)
        return

    start_button.config(text="一時停止")
    reps += 1
    
    if reps % 8 == 0:
        start_specific_timer("long", auto=True)
    elif reps % 2 == 0:
        start_specific_timer("short", auto=True)
    else:
        start_specific_timer("work", auto=True)

def pause_timer():
    global is_paused, paused_time
    if timer:
        is_paused = True
        current_time_str = timer_label.cget("text")
        try:
            minutes, seconds = map(int, current_time_str.split(':'))
            paused_time = minutes * 60 + seconds
        except ValueError:
            paused_time = 0
        window.after_cancel(timer)
        start_button.config(text="再開")

def toggle_timer():
    if start_button.cget('text') in ["スタート", "再開"]:
        start_timer()
    else:
        pause_timer()

def start_specific_timer(timer_type, auto=False):
    global reps, is_paused, timer
    if timer:
        window.after_cancel(timer)
    is_paused = False
    start_button.config(text="一時停止")
    
    try:
        update_settings()
    except ValueError:
        messagebox.showerror("入力エラー", "タイマーには半角数字を入力してください。")
        return

    if not auto:
        if timer_type == "work": reps = 0
        elif timer_type == "short": reps = 1
        elif timer_type == "long": reps = 7
        
    if timer_type == "work":
        title_label.config(text="集中時間", fg=GREEN)
        countdown(config["work_min"] * 60)
    elif timer_type == "short":
        title_label.config(text="短い休憩", fg=PINK)
        countdown(config["short_break_min"] * 60)
    elif timer_type == "long":
        title_label.config(text="長い休憩", fg=RED)
        countdown(config["long_break_min"] * 60)

# --- カウントダウン ---
def countdown(count):
    global timer
    count_min, count_sec = divmod(count, 60)
    timer_label.config(text=f"{count_min:02d}:{count_sec:02d}")
    if count > 0:
        timer = window.after(1000, countdown, count - 1)
    else:
        play_sound()
        if reps % 2 != 0:
            current_pomos = int(pomodoro_count_entry.get())
            pomodoro_count_entry.delete(0, tk.END)
            pomodoro_count_entry.insert(0, str(current_pomos + 1))
            update_settings()
        start_timer()

# --- 設定更新 ---
def update_settings():
    global config
    try:
        config = {
            "work_min": int(work_entry.get()),
            "short_break_min": int(short_break_entry.get()),
            "long_break_min": int(long_break_entry.get()),
            "pomodoros": int(pomodoro_count_entry.get())
        }
        save_config(config)
        update_pomodoro_display()
    except ValueError:
        raise ValueError("Invalid input")

# --- 音声再生ロジック (WAV -> MP3 -> 標準ビープ音) ---
def play_sound():
    """音声ファイルを再生する。wav -> mp3 -> beep の順で試行"""
    if HAS_WINSOUND and os.path.exists(AUDIO_WAV_FILE):
        try:
            winsound.PlaySound(AUDIO_WAV_FILE, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return
        except Exception as e:
            print(f"winsoundエラー: {e}")
    
    if HAS_PLAYSOUND and os.path.exists(AUDIO_MP3_FILE):
        try:
            playsound(AUDIO_MP3_FILE, block=False)
            return
        except Exception as e:
            print(f"playsoundエラー: {e}")
    
    window.bell()

# --- UIセットアップ ---
config = load_config()
window = tk.Tk()
window.title("ポモドーロタイマー")
window.config(padx=40, pady=20, bg=YELLOW)
window.resizable(False, False)

# row 0: タイトル
title_label = tk.Label(text="タイマー", font=(FONT_NAME, 40, "bold"), fg=GREEN, bg=YELLOW)
title_label.grid(row=0, column=0, pady=(0, 5))

# row 1: タイマー表示専用のラベル
timer_label = tk.Label(text="00:00", font=(FONT_NAME, 50, "bold"), fg=RED, bg=YELLOW)
timer_label.grid(row=1, column=0, pady=5)

# row 2: Canvas (トマト画像のみ)
canvas = tk.Canvas(width=220, height=220, bg=YELLOW, highlightthickness=0) 
try:
    # EXE化対応: 画像パスをresource_path経由で取得
    tomato_img_path = resource_path("tomato.png")
    tomato_img = tk.PhotoImage(file=tomato_img_path)
    canvas.create_image(110, 110, image=tomato_img)
except tk.TclError:
    canvas.create_rectangle(0, 0, 220, 220, fill="red", outline="red")
canvas.grid(row=2, column=0)

# row 3: メイン操作ボタン
button_frame = tk.Frame(window, bg=YELLOW)
button_frame.grid(row=3, column=0, pady=10)
start_button = tk.Button(button_frame, text="スタート", command=toggle_timer, font=(FONT_NAME, 12), width=8)
start_button.pack(side="left", padx=10)
reset_button = tk.Button(button_frame, text="リセット", command=reset_timer, font=(FONT_NAME, 12), width=8)
reset_button.pack(side="left", padx=10)

# row 4: 手動スタートボタン
manual_start_frame = tk.Frame(window, bg=YELLOW)
manual_start_frame.grid(row=4, column=0, pady=5)
tk.Label(manual_start_frame, text="手動スタート:", bg=YELLOW, font=(FONT_NAME, 9)).pack(side="left", padx=5)
tk.Button(manual_start_frame, text="集中", width=5, command=lambda: start_specific_timer("work")).pack(side="left")
tk.Button(manual_start_frame, text="短休憩", width=5, command=lambda: start_specific_timer("short")).pack(side="left")
tk.Button(manual_start_frame, text="長休憩", width=5, command=lambda: start_specific_timer("long")).pack(side="left")

# row 5, 6: ポモドーロカウンター
checkmark_label = tk.Label(bg=YELLOW, fg=GREEN, font=(FONT_NAME, 15, "bold"))
checkmark_label.grid(row=5, column=0)
pomo_count_frame = tk.Frame(window, bg=YELLOW)
pomo_count_frame.grid(row=6, column=0, pady=5)
tk.Label(pomo_count_frame, text="完了ポモドーロ数:", bg=YELLOW, font=(FONT_NAME, 10)).pack(side="left")
pomodoro_count_entry = tk.Entry(pomo_count_frame, width=5)
pomodoro_count_entry.insert(0, str(config["pomodoros"]))
pomodoro_count_entry.pack(side="left")
tk.Button(pomo_count_frame, text="0に", command=reset_pomodoro_count, font=("", 8)).pack(side="left", padx=5)

# row 7: 設定
settings_frame = tk.Frame(window, bg=YELLOW, padx=10, pady=10, bd=1, relief="solid")
settings_frame.grid(row=7, column=0, pady=15)
tk.Label(settings_frame, text="設定 (分)", bg=YELLOW, font=(FONT_NAME, 12, "bold")).grid(row=0, column=0, columnspan=2)
tk.Label(settings_frame, text="集中:", bg=YELLOW).grid(row=1, column=0, sticky="e", pady=2)
work_entry = tk.Entry(settings_frame, width=5)
work_entry.insert(0, str(config["work_min"]))
work_entry.grid(row=1, column=1)
tk.Label(settings_frame, text="短い休憩:", bg=YELLOW).grid(row=2, column=0, sticky="e", pady=2)
short_break_entry = tk.Entry(settings_frame, width=5)
short_break_entry.insert(0, str(config["short_break_min"]))
short_break_entry.grid(row=2, column=1)
tk.Label(settings_frame, text="長い休憩:", bg=YELLOW).grid(row=3, column=0, sticky="e", pady=2)
long_break_entry = tk.Entry(settings_frame, width=5)
long_break_entry.insert(0, str(config["long_break_min"]))
long_break_entry.grid(row=3, column=1)
tk.Button(settings_frame, text="設定を保存", command=update_settings).grid(row=4, column=0, columnspan=2, pady=10)

update_pomodoro_display()

def on_closing():
    try:
        update_settings()
    except ValueError:
        pass
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()