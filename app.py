import tkinter as tk
from tkinter import messagebox
import json
import os
import math

# --- 定数 ---
# 色やフォント、ファイル名などをここで一元管理します
PINK = "#e2979c"
RED = "#e7305b"
GREEN = "#9bdeac"
YELLOW = "#f7f5dd"
FONT_NAME = "Courier"
CONFIG_FILE = "pomodoro_config.json"

# --- グローバル変数 ---
# アプリケーション全体で共有する変数を定義します
reps = 0
timer = None
is_paused = False
paused_time = 0

# --- 設定の保存と読み込み ---

def load_config():
    """設定ファイルからデータを読み込む"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # デフォルト設定
        return {
            "work_min": 25,
            "short_break_min": 5,
            "long_break_min": 30,
            "pomodoros": 0
        }

def save_config(config):
    """現在の設定をファイルに保存する"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# --- タイマーリセット ---

def reset_timer():
    """タイマーを停止し、初期状態に戻す"""
    global reps, is_paused
    if timer:
        window.after_cancel(timer)
    
    reps = 0
    is_paused = False
    paused_time = 0

    # UIの更新
    title_label.config(text="タイマー", fg=GREEN)
    canvas.itemconfig(timer_text, text="00:00")
    start_button.config(text="スタート")
    
    # ポモドーロカウンターのUIを現在の設定値に更新
    pomodoro_count_entry.delete(0, tk.END)
    pomodoro_count_entry.insert(0, str(config["pomodoros"]))
    
    update_pomodoro_display()


# --- ポモドーロカウンターの操作 ---

def update_pomodoro_display():
    """現在のポモドーロ回数を画面のチェックマークで表示する"""
    pomodoros_done = int(pomodoro_count_entry.get())
    check_marks = "✔" * pomodoros_done
    checkmark_label.config(text=check_marks)

def reset_pomodoro_count():
    """ポモドーロカウンターを0にリセットし、保存する"""
    if messagebox.askokcancel("確認", "本当にポモドーロカウンターをリセットしますか？"):
        pomodoro_count_entry.delete(0, tk.END)
        pomodoro_count_entry.insert(0, "0")
        update_settings() # 変更を保存

# --- タイマーのメカニズム ---

def start_timer():
    """タイマーを開始または再開する"""
    global reps, is_paused, paused_time
    
    try:
        # 現在の入力値を取得して設定を更新
        update_settings()
    except ValueError:
        messagebox.showerror("入力エラー", "タイマーとカウンターには半角数字を入力してください。")
        return

    if is_paused:
        # 一時停止からの再開
        is_paused = False
        start_button.config(text="一時停止")
        countdown(paused_time)
        return

    # 通常のスタート
    start_button.config(text="一時停止")
    reps += 1
    
    work_sec = config["work_min"] * 60
    short_break_sec = config["short_break_min"] * 60
    long_break_sec = config["long_break_min"] * 60
    
    # 4ポモドーロ（8サイクル目）で長い休憩
    if reps % 8 == 0:
        title_label.config(text="長い休憩", fg=RED)
        countdown(long_break_sec)
    # 2, 4, 6サイクル目で短い休憩
    elif reps % 2 == 0:
        title_label.config(text="短い休憩", fg=PINK)
        countdown(short_break_sec)
    # 1, 3, 5, 7サイクル目で集中作業
    else:
        title_label.config(text="集中時間", fg=GREEN)
        countdown(work_sec)
        
def pause_timer():
    """タイマーを一時停止する"""
    global is_paused, paused_time
    is_paused = True
    paused_time = int(canvas.itemcget(timer_text, 'text').split(':')[0]) * 60 + int(canvas.itemcget(timer_text, 'text').split(':')[1])
    window.after_cancel(timer)
    start_button.config(text="再開")


def toggle_timer():
    """スタート/一時停止ボタンの処理を切り替える"""
    if start_button.cget('text') in ["スタート", "再開"]:
        start_timer()
    else:
        pause_timer()


# --- カウントダウンのメカニズム ---

def countdown(count):
    """指定された秒数からカウントダウンする"""
    global timer
    
    count_min = math.floor(count / 60)
    count_sec = count % 60
    if count_sec < 10:
        count_sec = f"0{count_sec}"
        
    canvas.itemconfig(timer_text, text=f"{count_min}:{count_sec}")
    
    if count > 0:
        timer = window.after(1000, countdown, count - 1)
    else:
        # タイマーが0になったときの処理
        play_sound()
        
        # 集中時間が終わったらポモドーロカウンターを増やす
        if reps % 2 != 0:
            current_pomos = int(pomodoro_count_entry.get())
            pomodoro_count_entry.delete(0, tk.END)
            pomodoro_count_entry.insert(0, str(current_pomos + 1))
            update_settings() # 保存

        # 次のタイマーを自動で開始
        start_timer()

# --- 設定の更新と保存 ---

def update_settings():
    """入力欄の値を読み込み、設定を更新・保存する"""
    global config
    try:
        config["work_min"] = int(work_entry.get())
        config["short_break_min"] = int(short_break_entry.get())
        config["long_break_min"] = int(long_break_entry.get())
        config["pomodoros"] = int(pomodoro_count_entry.get())
        
        save_config(config)
        update_pomodoro_display()
        # messagebox.showinfo("成功", "設定を保存しました。")
    except ValueError:
        raise ValueError("Invalid input")

# --- 音声再生 ---

def play_sound():
    """タイマー完了時に音を鳴らす"""
    # playsound ライブラリがない場合は、標準のビープ音を鳴らす
    try:
        from playsound import playsound
        # 'bell.mp3'のような音声ファイルを同じフォルダに置いてください
        if os.path.exists("bell.mp3"):
            playsound("bell.mp3", block=False)
        else:
            window.bell() # ファイルがない場合はビープ音
    except ImportError:
        window.bell() # ライブラリがない場合もビープ音

# --- UIセットアップ ---

# 設定を読み込む
config = load_config()

# ウィンドウの作成
window = tk.Tk()
window.title("ポモドーロタイマー")
window.config(padx=50, pady=25, bg=YELLOW)

# タイトルラベル
title_label = tk.Label(text="タイマー", font=(FONT_NAME, 40, "bold"), fg=GREEN, bg=YELLOW)
title_label.grid(row=0, column=1)

# タイマー表示 (Canvasを使用)
canvas = tk.Canvas(width=200, height=224, bg=YELLOW, highlightthickness=0)
tomato_img = tk.PhotoImage(file="tomato.png") # トマトの画像
canvas.create_image(100, 112, image=tomato_img)
timer_text = canvas.create_text(100, 130, text="00:00", fill="white", font=(FONT_NAME, 35, "bold"))
canvas.grid(row=1, column=1)

# ボタン
start_button = tk.Button(text="スタート", command=toggle_timer, font=(FONT_NAME, 12), highlightthickness=0)
start_button.grid(row=2, column=0)

reset_button = tk.Button(text="リセット", command=reset_timer, font=(FONT_NAME, 12), highlightthickness=0)
reset_button.grid(row=2, column=2)

# ポモドーロカウンターとチェックマーク
checkmark_label = tk.Label(bg=YELLOW, fg=GREEN, font=(FONT_NAME, 15, "bold"))
checkmark_label.grid(row=3, column=1)

pomodoro_count_label = tk.Label(text="完了ポモドーロ数:", bg=YELLOW, font=(FONT_NAME, 10))
pomodoro_count_label.grid(row=4, column=0, sticky="e")
pomodoro_count_entry = tk.Entry(width=5)
pomodoro_count_entry.insert(0, str(config["pomodoros"]))
pomodoro_count_entry.grid(row=4, column=1, sticky="w")

reset_pomo_button = tk.Button(text="カウンターを0に", command=reset_pomodoro_count)
reset_pomo_button.grid(row=4, column=2)

# --- 設定入力欄 ---
settings_frame = tk.Frame(window, bg=YELLOW, padx=10, pady=10)
settings_frame.grid(row=5, column=0, columnspan=3, pady=20)

tk.Label(settings_frame, text="設定 (分)", bg=YELLOW, font=(FONT_NAME, 12, "bold")).grid(row=0, column=0, columnspan=3)

tk.Label(settings_frame, text="集中:", bg=YELLOW).grid(row=1, column=0)
work_entry = tk.Entry(settings_frame, width=5)
work_entry.insert(0, str(config["work_min"]))
work_entry.grid(row=1, column=1)

tk.Label(settings_frame, text="短い休憩:", bg=YELLOW).grid(row=2, column=0)
short_break_entry = tk.Entry(settings_frame, width=5)
short_break_entry.insert(0, str(config["short_break_min"]))
short_break_entry.grid(row=2, column=1)

tk.Label(settings_frame, text="長い休憩:", bg=YELLOW).grid(row=3, column=0)
long_break_entry = tk.Entry(settings_frame, width=5)
long_break_entry.insert(0, str(config["long_break_min"]))
long_break_entry.grid(row=3, column=1)

save_button = tk.Button(settings_frame, text="設定を保存", command=update_settings)
save_button.grid(row=4, column=0, columnspan=3, pady=10)


# 起動時にカウンター表示を更新
update_pomodoro_display()

# ウィンドウを閉じたときの処理
def on_closing():
    if messagebox.askokcancel("終了", "タイマーを終了しますか？"):
        # 閉じる直前に最新のカウンター情報を保存
        try:
            update_settings()
        except ValueError:
            pass # 入力が不正な場合は保存せずに閉じる
        window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()