from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import json
import os
import random
import sys
import time
import tkinter as tk
from tkinter import messagebox
import urllib.request
import customtkinter as ctk
import keyboard
import pyautogui

# --- 미니멀 화이트모드 디자인 팔레트 (#8dbff0 포인트) ---
LIGHT_BG = "#F5F6F8"  # 아주 약간의 회색빛이 도는 배경
LIGHT_LAYER = "#FFFFFF"  # 패널 / 카드 배경 (순백색)
LIGHT_BORDER = "#E2E8F0"  # 부드러운 테두리선
ACCENT_BLUE = "#8dbff0"  # 사용자 지정 포인트 블루 (버튼 강조 색상)
ACCENT_HOVER = "#75afe9"  # 버튼 호버 색상
TEXT_MAIN = "#1E293B"  # 메인 텍스트 (진한 회색/네이비)
TEXT_SUB = "#64748B"  # 서브 레이블 텍스트
NEUTRAL_BTN = "#E2E8F0"  # 중립 버튼 배경
NEUTRAL_HOVER = "#CBD5E1"

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# 화면 구석으로 마우스를 치우면 비상 정지되는 안전장치
pyautogui.FAILSAFE = True

# 전역 서버 시간 오프셋 변수
server_offset = timedelta(0)

# --- 설정 파일(JSON) 관리 로직 ---
SETTINGS_FILE = "ticketing_settings.json"

DEFAULT_TICKETING_SITES = {
    "티켓링크": {
        "url": "https://www.ticketlink.co.kr",
        "next_month": [1270, 1180],
        "date_start": [1006, 1255],
        "gap_x": 44,
        "gap_y": 35,
        "day_btn": [1500, 1210],
        "night_btn": [1500, 1300],
        "book_btn_1": [1850, 1500],  # 공연 1개일 때 예매하기 진입
        "book_btn_2": [1850, 1580],  # 공연 2개일 때 예매하기 진입
        "final_book_btn": [925, 890],
        "seat_rgb": [220, 230, 240],
        "bg_rgb": [255, 255, 255],
        "presets": {
            "예스24아트원 1관": {
                "seat_base_pos": [300, 465],
                "seat_gap_x": 16,
                "seat_gap_y": 16,
                "max_row": 9,
                "max_col": 6,
                "target_center_x": 372,
            },
            "SH아트홀": {
                "seat_base_pos": [330, 507],
                "seat_gap_x": 14,
                "seat_gap_y": 14,
                "max_row": 7,
                "max_col": 3,
                "target_center_x": 372,
            },
        },
    },
    "예스24티켓": {
        "url": "https://ticket.yes24.com",
        "next_month": [1250, 1150],
        "date_start": [1000, 1200],
        "gap_x": 42,
        "gap_y": 32,
        "day_btn": [1480, 1180],
        "night_btn": [1480, 1260],
        "book_btn_1": [1800, 1450],
        "book_btn_2": [1800, 1520],
        "final_book_btn": [900, 850],
        "seat_rgb": [220, 230, 240],
        "bg_rgb": [255, 255, 255],
        "presets": {
            "예스24아트원 1관 (예스24용)": {
                "seat_base_pos": [310, 470],
                "seat_gap_x": 16,
                "seat_gap_y": 16,
                "max_row": 9,
                "max_col": 6,
                "target_center_x": 372,
            }
        },
    },
}

TICKETING_SITES = {}


def load_settings():
  global TICKETING_SITES
  if os.path.exists(SETTINGS_FILE):
    try:
      with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        TICKETING_SITES = json.load(f)
        print(f"[*] 외부 설정 파일({SETTINGS_FILE}) 로드 성공!")
        return
    except Exception as e:
      print(f"⚠️ 설정 파일 로드 실패 (기본값으로 대체): {e}")

  TICKETING_SITES = DEFAULT_TICKETING_SITES
  save_settings_to_json()


def save_settings_to_json():
  try:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
      json.dump(TICKETING_SITES, f, ensure_ascii=False, indent=4)
      print(f"[*] 설정 파일({SETTINGS_FILE}) 저장 완료!")
  except Exception as e:
    print(f"⚠️ 설정 파일 저장 실패: {e}")


load_settings()


def sync_server_time_for_site(site_name):
  global server_offset
  site_data = TICKETING_SITES.get(site_name)
  if not site_data or "url" not in site_data:
    server_offset = timedelta(0)
    return

  target_url = site_data["url"]
  try:
    print(f"[*] [{site_name}] 서버 ({target_url}) 시간 동기화 중...")
    req = urllib.request.Request(
        target_url, headers={"User-Agent": "Mozilla/5.0"}
    )
    start_t = time.time()
    with urllib.request.urlopen(req, timeout=5) as response:
      end_t = time.time()
      latency = (end_t - start_t) / 2.0
      gmt_date_str = response.headers.get("Date")
      if gmt_date_str:
        gmt_dt = parsedate_to_datetime(gmt_date_str)
        kst_dt = gmt_dt + timedelta(hours=9)
        server_dt = kst_dt.replace(tzinfo=None)
        local_now = datetime.now()
        server_offset = (server_dt - local_now) + timedelta(seconds=latency)
        print(
            f"[*] [{site_name}] 서버 시간 동기화 완료! (지연 시간 보정:"
            f" {latency:.3f}초)"
        )
        return
  except Exception as e:
    print(
        f"[{site_name}] 서버 시간 동기화 지연/실패 (로컬 시간으로 대체 작동):"
        f" {e}"
    )
  server_offset = timedelta(0)


sync_server_time_for_site(
    list(TICKETING_SITES.keys())[0] if TICKETING_SITES else "티켓링크"
)

app = ctk.CTk()
app.title("하이브리드 티켓팅 오토메이션")
app.geometry("880x440")
app.attributes("-topmost", True)

screen_width = app.winfo_screenwidth()
x_pos = screen_width - 900
y_pos = 40
app.geometry(f"880x440+{x_pos}+{y_pos}")

steps = []
current_index = 0

site_var = ctk.StringVar(
    value=list(TICKETING_SITES.keys())[0] if TICKETING_SITES else ""
)
venue_var = ctk.StringVar(value="")
month_var = ctk.StringVar(value="current")
row_var = ctk.StringVar(value="3")
col_var = ctk.StringVar(value="6")
time_var_choice = ctk.StringVar(value="skip")
show_count_var = ctk.StringVar(value="1")  # 공연 개수 (1 또는 2)

time_display_var = ctk.StringVar(value="서버 시간 계산 중...")
status_var = ctk.StringVar(value="메인 화면에서 원하는 기능을 선택하세요.")

live_x_var = ctk.StringVar(value="0")
live_y_var = ctk.StringVar(value="0")
live_rgb_var = ctk.StringVar(value="R: 0, G: 0, B: 0")


def quit_program():
  print("\n프로그램을 안전하게 종료합니다.")
  try:
    keyboard.unhook_all()
  except:
    pass
  app.destroy()
  sys.exit(0)


app.protocol("WM_DELETE_WINDOW", quit_program)

container = ctk.CTkFrame(app, fg_color=LIGHT_BG)
container.pack(fill="both", expand=True)
container.rowconfigure(0, weight=1)
container.columnconfigure(0, weight=1)

frames = {}


def show_frame(frame_name):
  frame = frames[frame_name]
  frame.tkraise()
  if frame_name == "Ticketing":
    update_venue_combobox()
  elif frame_name == "Settings":
    refresh_settings_ui()
  print(f"[*] 화면 전환: {frame_name}")


def is_available_seat(pos):
  try:
    px, py = int(pos[0]), int(pos[1])
    r, g, b = pyautogui.pixel(px, py)
    is_gray = (
        220 <= r <= 250
        and 220 <= g <= 250
        and 220 <= b <= 250
        and abs(r - g) <= 8
        and abs(g - b) <= 8
    )
    is_white = r >= 248 and g >= 248 and b >= 248
    if not is_gray and not is_white:
      return True
  except Exception:
    pass
  return False


def human_move(x, y):
  duration = random.uniform(0.18, 0.32)
  pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutCubic)


def natural_click(x, y):
  human_move(x, y)
  time.sleep(random.uniform(0.04, 0.09))
  pyautogui.mouseDown()
  time.sleep(random.uniform(0.03, 0.07))
  pyautogui.mouseUp()


def on_site_changed(choice):
  selected_site = site_var.get()
  update_venue_combobox()
  sync_server_time_for_site(selected_site)


def update_venue_combobox():
  selected_site = site_var.get()
  if selected_site in TICKETING_SITES:
    presets = sorted(list(TICKETING_SITES[selected_site]["presets"].keys()))
    venue_combo.configure(values=presets)
    if presets:
      venue_var.set(presets[0])
    else:
      venue_var.set("")


def apply_ticketing_settings():
  global steps, current_index
  try:
    selected_site = site_var.get()
    selected_venue = venue_var.get()
    m_choice = month_var.get()
    r = int(row_var.get())
    c = int(col_var.get())
    t_choice = time_var_choice.get()
    s_count = show_count_var.get()
  except ValueError:
    messagebox.showerror("입력 오류", "행과 열은 숫자여야 합니다!")
    return

  site_data = TICKETING_SITES.get(selected_site)
  if not site_data:
    messagebox.showerror("오류", "선택한 티켓 사이트 정보를 찾을 수 없습니다.")
    return

  next_month_btn_pos = site_data["next_month"]
  date_start_pos = site_data["date_start"]
  gap_x = site_data["gap_x"]
  gap_y = site_data["gap_y"]

  target_date_x = date_start_pos[0] + (c - 1) * gap_x
  target_date_y = date_start_pos[1] + (r - 1) * gap_y
  target_date_pos = (target_date_x, target_date_y)

  time_buttons = {
      "day": site_data["day_btn"],
      "night": site_data["night_btn"],
  }

  # 공연 개수(1개 또는 2개)에 따른 예매하기 진입 좌표 선택
  if s_count == "2":
    book_button_pos = site_data.get("book_btn_2", site_data["book_btn_1"])
  else:
    book_button_pos = site_data["book_btn_1"]

  new_steps = []
  if m_choice == "next":
    new_steps.append({"desc": "다음달 넘기기 버튼", "pos": next_month_btn_pos})
  elif m_choice == "next_next":
    new_steps.append(
        {"desc": "다다음달 넘기기 버튼 (1차)", "pos": next_month_btn_pos}
    )
    new_steps.append(
        {"desc": "다다음달 넘기기 버튼 (2차)", "pos": next_month_btn_pos}
    )

  new_steps.append({"desc": f"날짜 선택 ({r}행 {c}열)", "pos": target_date_pos})

  # 시간 선택 분기 (낮공연, 밤공연, 바로넘김)
  if t_choice == "day":
    new_steps.append({"desc": "공연 시간 선택 (낮공연)", "pos": time_buttons["day"]})
  elif t_choice == "night":
    new_steps.append({"desc": "공연 시간 선택 (밤공연)", "pos": time_buttons["night"]})

  new_steps.append(
      {
          "desc": (
              f"[{selected_site}] 예매하기 진입 (공연 {s_count}개용)"
          ),
          "pos": book_button_pos,
      }
  )

  steps = new_steps
  current_index = 0
  update_status_text()
  messagebox.showinfo(
      "설정 완료",
      f"사이트: {selected_site}\n공연장: {selected_venue}\n공연 수: {s_count}개\n설정이"
      " 성공적으로 반영되었습니다!",
  )


def bulk_scan_available_seats():
  global steps, current_index
  selected_site = site_var.get()
  selected_venue = venue_var.get()

  site_data = TICKETING_SITES.get(selected_site)
  if not site_data or selected_venue not in site_data["presets"]:
    print("⚠️ 선택된 사이트 또는 공연장 프리셋 정보가 올바르지 않습니다.")
    return

  seat_preset = site_data["presets"][selected_venue]
  base_x, base_y = seat_preset["seat_base_pos"]
  gx = seat_preset["seat_gap_x"]
  gy = seat_preset["seat_gap_y"]
  target_cx = seat_preset["target_center_x"]

  print(
      f"\n[*] [{selected_site} - {selected_venue}] 좌석 페이지 로딩 완료 ->"
      " 포도알 색상 스캔 시작..."
  )

  all_seats = []
  skipped_count = 0

  for row in range(1, seat_preset["max_row"] + 1):
    for col in range(1, seat_preset["max_col"] + 1):
      sx = base_x + (col - 1) * gx
      sy = base_y + (row - 1) * gy

      if not is_available_seat((sx, sy)):
        skipped_count += 1
        continue

      dist_x = abs(sx - target_cx)
      all_seats.append({
          "row": row,
          "col": col,
          "pos": [sx, sy],
          "sort_weight": row * dist_x,
      })

  available_seats = sorted(
      all_seats, key=lambda s: (s["row"], s["sort_weight"])
  )
  print(
      f"    - [스캔 결과] 예매 가능 포도알 {len(available_seats)}개 발견! (제외:"
      f" {skipped_count}개)"
  )

  if not available_seats:
    print("⚠️ 잔여석 없음. 1초 후 재스캔...")
    status_var.set("⚠️ 포도알 없음! 재스캔 중...")
    app.after(1000, bulk_scan_available_seats)
    return

  base_steps = [s for s in steps if "포도알 후보" not in s]
  new_steps = list(base_steps)
  for idx, seat in enumerate(available_seats):
    new_steps.append({
        "desc": f"포도알 후보 #{idx+1} ({seat['row']}행 {seat['col']}열)",
        "pos": seat["pos"],
    })

  steps = new_steps
  current_index = len(base_steps)
  update_status_text()
  print("✨ 첫 번째 예매 가능 포도알 조준 완료! [F8] 이동, [F9] 클릭")


# --- [프레임 1] 메인 화면 (Main Screen) ---
frame_main = ctk.CTkFrame(container, fg_color=LIGHT_BG)
frames["Main"] = frame_main

top_main_frame = ctk.CTkFrame(
    frame_main, fg_color=LIGHT_LAYER, height=50, corner_radius=0
)
top_main_frame.pack(fill="x", padx=0, pady=0)

ctk.CTkLabel(
    top_main_frame,
    text="⚡ 하이브리드 티켓팅 오토메이션",
    font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold"),
    text_color=TEXT_MAIN,
).pack(side="left", padx=16, pady=12)

ctk.CTkButton(
    top_main_frame,
    text="✕ 종료",
    fg_color=ACCENT_BLUE,
    hover_color=ACCENT_HOVER,
    text_color=TEXT_MAIN,
    width=70,
    height=28,
    font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
    command=quit_program,
).pack(side="right", padx=16)

center_main_frame = ctk.CTkFrame(frame_main, fg_color=LIGHT_BG)
center_main_frame.pack(expand=True)

ctk.CTkButton(
    center_main_frame,
    text="🎫  티켓팅 시작하기",
    fg_color=ACCENT_BLUE,
    hover_color=ACCENT_HOVER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold"),
    width=280,
    height=48,
    corner_radius=6,
    command=lambda: show_frame("Ticketing"),
).pack(pady=10)

ctk.CTkButton(
    center_main_frame,
    text="⚙️  환경 설정 및 프리셋 관리",
    fg_color=LIGHT_LAYER,
    hover_color=NEUTRAL_HOVER,
    border_width=1,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold"),
    width=280,
    height=48,
    corner_radius=6,
    command=lambda: show_frame("Settings"),
).pack(pady=10)

ctk.CTkButton(
    center_main_frame,
    text="🔍  좌표 및 RGB 찾기",
    fg_color=LIGHT_LAYER,
    hover_color=NEUTRAL_HOVER,
    border_width=1,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold"),
    width=280,
    height=48,
    corner_radius=6,
    command=lambda: show_frame("CoordFinder"),
).pack(pady=10)


# --- [프레임 2] 티켓팅 화면 (Ticketing Screen) ---
frame_ticketing = ctk.CTkFrame(container, fg_color=LIGHT_BG)
frames["Ticketing"] = frame_ticketing

top_tick_frame = ctk.CTkFrame(
    frame_ticketing, fg_color=LIGHT_LAYER, height=50, corner_radius=0
)
top_tick_frame.pack(fill="x", padx=0, pady=0)

ctk.CTkButton(
    top_tick_frame,
    text="◀ 메인",
    fg_color=NEUTRAL_BTN,
    hover_color=NEUTRAL_HOVER,
    text_color=TEXT_MAIN,
    width=70,
    height=28,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    command=lambda: show_frame("Main"),
).pack(side="left", padx=16, pady=11)
ctk.CTkLabel(
    top_tick_frame,
    text="🎫 티켓팅 제어 패널",
    font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"),
    text_color=TEXT_MAIN,
).pack(side="left", padx=8)

ctk.CTkButton(
    top_tick_frame,
    text="✕ 종료",
    fg_color=ACCENT_BLUE,
    hover_color=ACCENT_HOVER,
    text_color=TEXT_MAIN,
    width=70,
    height=28,
    font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
    command=quit_program,
).pack(side="right", padx=16)

main_tick_frame = ctk.CTkFrame(frame_ticketing, fg_color=LIGHT_BG)
main_tick_frame.pack(fill="both", expand=True, padx=16, pady=12)

left_tick_frame = ctk.CTkFrame(
    main_tick_frame,
    fg_color=LIGHT_LAYER,
    corner_radius=6,
    border_width=1,
    border_color=LIGHT_BORDER,
)
left_tick_frame.pack(side="left", fill="both", expand=True, padx=6, pady=4)
left_tick_frame.columnconfigure(1, weight=1)

ctk.CTkLabel(
    left_tick_frame,
    text="⚙️ 티켓팅 조건 설정",
    font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"),
    text_color=TEXT_MAIN,
).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 6))

ctk.CTkLabel(
    left_tick_frame,
    text="티켓 사이트",
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    text_color=TEXT_SUB,
).grid(row=1, column=0, sticky="w", padx=12, pady=4)
site_combo = ctk.CTkComboBox(
    left_tick_frame,
    variable=site_var,
    values=sorted(list(TICKETING_SITES.keys())),
    state="readonly",
    width=180,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    dropdown_font=ctk.CTkFont(family="Malgun Gothic", size=11),
    command=on_site_changed,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    button_color=ACCENT_BLUE,
    button_hover_color=ACCENT_HOVER,
    dropdown_fg_color=LIGHT_LAYER,
)
site_combo.grid(row=1, column=1, sticky="e", padx=12, pady=4)

ctk.CTkLabel(
    left_tick_frame,
    text="공연장 프리셋",
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    text_color=TEXT_SUB,
).grid(row=2, column=0, sticky="w", padx=12, pady=4)
venue_combo = ctk.CTkComboBox(
    left_tick_frame,
    variable=venue_var,
    state="readonly",
    width=180,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    dropdown_font=ctk.CTkFont(family="Malgun Gothic", size=11),
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    button_color=ACCENT_BLUE,
    button_hover_color=ACCENT_HOVER,
    dropdown_fg_color=LIGHT_LAYER,
)
venue_combo.grid(row=2, column=1, sticky="e", padx=12, pady=4)

ctk.CTkLabel(
    left_tick_frame,
    text="관람 월",
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    text_color=TEXT_SUB,
).grid(row=3, column=0, sticky="w", padx=12, pady=4)
month_combo = ctk.CTkComboBox(
    left_tick_frame,
    variable=month_var,
    values=["current", "next", "next_next"],
    state="readonly",
    width=180,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    dropdown_font=ctk.CTkFont(family="Malgun Gothic", size=11),
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    button_color=ACCENT_BLUE,
    button_hover_color=ACCENT_HOVER,
    dropdown_fg_color=LIGHT_LAYER,
)
month_combo.grid(row=3, column=1, sticky="e", padx=12, pady=4)

ctk.CTkLabel(
    left_tick_frame,
    text="날짜 (행, 열)",
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    text_color=TEXT_SUB,
).grid(row=4, column=0, sticky="w", padx=12, pady=4)

date_sub_f = ctk.CTkFrame(left_tick_frame, fg_color="transparent")
date_sub_f.grid(row=4, column=1, sticky="e", padx=12, pady=4)
row_entry = ctk.CTkEntry(
    date_sub_f,
    textvariable=row_var,
    width=82,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
row_entry.pack(side="left", padx=2)
col_entry = ctk.CTkEntry(
    date_sub_f,
    textvariable=col_var,
    width=82,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
col_entry.pack(side="right", padx=2)

ctk.CTkLabel(
    left_tick_frame,
    text="공연 시간",
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    text_color=TEXT_SUB,
).grid(row=5, column=0, sticky="w", padx=12, pady=4)
time_frame = ctk.CTkFrame(left_tick_frame, fg_color="transparent")
time_frame.grid(row=5, column=1, sticky="e", padx=12, pady=4)
ctk.CTkRadioButton(
    time_frame,
    text="낮공연",
    variable=time_var_choice,
    value="day",
    font=ctk.CTkFont(family="Malgun Gothic", size=10),
    text_color=TEXT_MAIN,
).pack(side="left", padx=2)
ctk.CTkRadioButton(
    time_frame,
    text="밤공연",
    variable=time_var_choice,
    value="night",
    font=ctk.CTkFont(family="Malgun Gothic", size=10),
    text_color=TEXT_MAIN,
).pack(side="left", padx=2)
ctk.CTkRadioButton(
    time_frame,
    text="바로넘김",
    variable=time_var_choice,
    value="skip",
    font=ctk.CTkFont(family="Malgun Gothic", size=10),
    text_color=TEXT_MAIN,
).pack(side="left", padx=2)

ctk.CTkLabel(
    left_tick_frame,
    text="당일 공연 수",
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    text_color=TEXT_SUB,
).grid(row=6, column=0, sticky="w", padx=12, pady=4)
show_count_frame = ctk.CTkFrame(left_tick_frame, fg_color="transparent")
show_count_frame.grid(row=6, column=1, sticky="e", padx=12, pady=4)
ctk.CTkRadioButton(
    show_count_frame,
    text="1개 (기본)",
    variable=show_count_var,
    value="1",
    font=ctk.CTkFont(family="Malgun Gothic", size=10),
    text_color=TEXT_MAIN,
).pack(side="left", padx=10)
ctk.CTkRadioButton(
    show_count_frame,
    text="2개 (회차있음)",
    variable=show_count_var,
    value="2",
    font=ctk.CTkFont(family="Malgun Gothic", size=10),
    text_color=TEXT_MAIN,
).pack(side="left", padx=10)

apply_btn = ctk.CTkButton(
    left_tick_frame,
    text="설정 적용",
    fg_color=ACCENT_BLUE,
    hover_color=ACCENT_HOVER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"),
    height=34,
    corner_radius=6,
    command=apply_ticketing_settings,
)
apply_btn.grid(row=7, column=0, columnspan=2, sticky="ew", padx=12, pady=12)

right_tick_frame = ctk.CTkFrame(
    main_tick_frame,
    fg_color=LIGHT_LAYER,
    corner_radius=6,
    border_width=1,
    border_color=LIGHT_BORDER,
)
right_tick_frame.pack(side="right", fill="both", expand=True, padx=6, pady=4)

ctk.CTkLabel(
    right_tick_frame,
    text="선택 사이트 공식 서버 시간",
    font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
    text_color=TEXT_SUB,
).pack(pady=(16, 2))
time_label = ctk.CTkLabel(
    right_tick_frame,
    textvariable=time_display_var,
    font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
    text_color=ACCENT_BLUE,
)
time_label.pack(pady=4)

status_label = ctk.CTkLabel(
    right_tick_frame,
    textvariable=status_var,
    font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
    text_color=TEXT_MAIN,
    wraplength=340,
    justify="center",
)
status_label.pack(pady=12)

hint_label = ctk.CTkLabel(
    right_tick_frame,
    text="[F8] 이동 | [F9] 포도알 클릭(연석) | [F10] 최종 예매",
    font=ctk.CTkFont(family="Malgun Gothic", size=10, weight="bold"),
    text_color=TEXT_SUB,
)
hint_label.pack(pady=(4, 16))


# --- [프레임 3] 설정 화면 (Settings Screen) ---
frame_settings = ctk.CTkFrame(container, fg_color=LIGHT_BG)
frames["Settings"] = frame_settings

top_set_frame = ctk.CTkFrame(
    frame_settings, fg_color=LIGHT_LAYER, height=50, corner_radius=0
)
top_set_frame.pack(fill="x", padx=0, pady=0)

ctk.CTkButton(
    top_set_frame,
    text="◀ 메인",
    fg_color=NEUTRAL_BTN,
    hover_color=NEUTRAL_HOVER,
    text_color=TEXT_MAIN,
    width=70,
    height=28,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    command=lambda: show_frame("Main"),
).pack(side="left", padx=16, pady=11)
ctk.CTkLabel(
    top_set_frame,
    text="⚙️ 티켓사이트 및 공연장 프리셋 상세 설정",
    font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"),
    text_color=TEXT_MAIN,
).pack(side="left", padx=8)

ctk.CTkButton(
    top_set_frame,
    text="✕ 종료",
    fg_color=ACCENT_BLUE,
    hover_color=ACCENT_HOVER,
    text_color=TEXT_MAIN,
    width=70,
    height=28,
    font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
    command=quit_program,
).pack(side="right", padx=16)

main_set_frame = ctk.CTkFrame(frame_settings, fg_color=LIGHT_BG)
main_set_frame.pack(fill="both", expand=True, padx=16, pady=12)

left_set_pane = ctk.CTkFrame(
    main_set_frame,
    fg_color=LIGHT_LAYER,
    corner_radius=6,
    border_width=1,
    border_color=LIGHT_BORDER,
)
left_set_pane.pack(side="left", fill="both", expand=True, padx=6, pady=4)

set_site_sel_var = ctk.StringVar()
s_name_var = ctk.StringVar()
s_url_var = ctk.StringVar()
s_next_x, s_next_y = ctk.StringVar(), ctk.StringVar()
s_date_x, s_date_y = ctk.StringVar(), ctk.StringVar()
s_gx, s_gy = ctk.StringVar(), ctk.StringVar()
s_day_x, s_day_y = ctk.StringVar(), ctk.StringVar()
s_night_x, s_night_y = ctk.StringVar(), ctk.StringVar()
s_b1_x, s_b1_y = ctk.StringVar(), ctk.StringVar()
s_b2_x, s_b2_y = ctk.StringVar(), ctk.StringVar()
s_final_x, s_final_y = ctk.StringVar(), ctk.StringVar()
seat_r, seat_g, seat_b = ctk.StringVar(), ctk.StringVar(), ctk.StringVar()
bg_r, bg_g, bg_b = ctk.StringVar(), ctk.StringVar(), ctk.StringVar()


def on_settings_site_selected(choice):
  sel = set_site_sel_var.get()
  if sel == "+ 새 사이트 추가":
    s_name_var.set("")
    s_url_var.set("https://")
    s_next_x.set("1270")
    s_next_y.set("1180")
    s_date_x.set("1006")
    s_date_y.set("1255")
    s_gx.set("44")
    s_gy.set("35")
    s_day_x.set("1500")
    s_day_y.set("1210")
    s_night_x.set("1500")
    s_night_y.set("1300")
    s_b1_x.set("1850")
    s_b1_y.set("1500")
    s_b2_x.set("1850")
    s_b2_y.set("1580")
    s_final_x.set("925")
    s_final_y.set("890")
    seat_r.set("220")
    seat_g.set("230")
    seat_b.set("240")
    bg_r.set("255")
    bg_g.set("255")
    bg_b.set("255")
  elif sel in TICKETING_SITES:
    data = TICKETING_SITES[sel]
    s_name_var.set(sel)
    s_url_var.set(data.get("url", ""))
    s_next_x.set(str(data["next_month"][0]))
    s_next_y.set(str(data["next_month"][1]))
    s_date_x.set(str(data["date_start"][0]))
    s_date_y.set(str(data["date_start"][1]))
    s_gx.set(str(data["gap_x"]))
    s_gy.set(str(data["gap_y"]))
    s_day_x.set(str(data["day_btn"][0]))
    s_day_y.set(str(data["day_btn"][1]))
    s_night_x.set(str(data["night_btn"][0]))
    s_night_y.set(str(data["night_btn"][1]))
    s_b1_x.set(str(data["book_btn_1"][0]))
    s_b1_y.set(str(data["book_btn_1"][1]))
    s_b2_x.set(str(data["book_btn_2"][0]))
    s_b2_y.set(str(data["book_btn_2"][1]))
    s_final_x.set(str(data["final_book_btn"][0]))
    s_final_y.set(str(data["final_book_btn"][1]))
    seat_col = data.get("seat_rgb", [220, 230, 240])
    bg_col = data.get("bg_rgb", [255, 255, 255])
    seat_r.set(str(seat_col[0]))
    seat_g.set(str(seat_col[1]))
    seat_b.set(str(seat_col[2]))
    bg_r.set(str(bg_col[0]))
    bg_g.set(str(bg_col[1]))
    bg_b.set(str(bg_col[2]))


st_sel_f = ctk.CTkFrame(left_set_pane, fg_color="transparent")
st_sel_f.pack(fill="x", padx=10, pady=4)
ctk.CTkLabel(
    st_sel_f,
    text="사이트 선택",
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    text_color=TEXT_SUB,
).pack(side="left")

st_combo = ctk.CTkComboBox(
    st_sel_f,
    variable=set_site_sel_var,
    state="readonly",
    width=160,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    dropdown_font=ctk.CTkFont(family="Malgun Gothic", size=11),
    command=on_settings_site_selected,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    button_color=ACCENT_BLUE,
    button_hover_color=ACCENT_HOVER,
    dropdown_fg_color=LIGHT_LAYER,
)
st_combo.pack(side="right")


def add_coord_row(parent, title, var_x, var_y):
  f = ctk.CTkFrame(parent, fg_color="transparent")
  f.pack(fill="x", padx=10, pady=2)
  ctk.CTkLabel(
      f,
      text=title,
      font=ctk.CTkFont(family="Malgun Gothic", size=10),
      text_color=TEXT_SUB,
  ).pack(side="left")
  e2 = ctk.CTkEntry(
      f,
      textvariable=var_y,
      width=45,
      fg_color=LIGHT_LAYER,
      border_color=LIGHT_BORDER,
      text_color=TEXT_MAIN,
      font=ctk.CTkFont(family="Malgun Gothic", size=11),
  )
  e2.pack(side="right", padx=2)
  ctk.CTkLabel(f, text=",", text_color="gray").pack(side="right")
  e1 = ctk.CTkEntry(
      f,
      textvariable=var_x,
      width=45,
      fg_color=LIGHT_LAYER,
      border_color=LIGHT_BORDER,
      text_color=TEXT_MAIN,
      font=ctk.CTkFont(family="Malgun Gothic", size=11),
  )
  e1.pack(side="right", padx=2)


form_s1 = ctk.CTkFrame(left_set_pane, fg_color="transparent")
form_s1.pack(fill="x", padx=10, pady=2)
ctk.CTkLabel(
    form_s1,
    text="사이트명 / URL",
    font=ctk.CTkFont(family="Malgun Gothic", size=10),
    text_color=TEXT_SUB,
).pack(side="left")
url_entry = ctk.CTkEntry(
    form_s1,
    textvariable=s_url_var,
    width=95,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
url_entry.pack(side="right", padx=2)
ctk.CTkLabel(form_s1, text="/", text_color="gray").pack(side="right")
name_entry = ctk.CTkEntry(
    form_s1,
    textvariable=s_name_var,
    width=75,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
name_entry.pack(side="right", padx=2)

add_coord_row(left_set_pane, "달력넘기기(X,Y)", s_next_x, s_next_y)
add_coord_row(left_set_pane, "날짜좌표(X,Y)", s_date_x, s_date_y)
add_coord_row(left_set_pane, "날짜간격(가로,세로)", s_gx, s_gy)
add_coord_row(left_set_pane, "낮공연버튼(X,Y)", s_day_x, s_day_y)
add_coord_row(left_set_pane, "밤공연버튼(X,Y)", s_night_x, s_night_y)
add_coord_row(left_set_pane, "예매하기(공연1개)", s_b1_x, s_b1_y)
add_coord_row(left_set_pane, "예매하기(공연2개)", s_b2_x, s_b2_y)

f_mov = ctk.CTkFrame(left_set_pane, fg_color="transparent")
f_mov.pack(fill="x", padx=10, pady=2)
ctk.CTkLabel(
    f_mov,
    text="최종예매버튼(X,Y)",
    font=ctk.CTkFont(family="Malgun Gothic", size=10),
    text_color=TEXT_SUB,
).pack(side="left")
e_fb_y = ctk.CTkEntry(
    f_mov,
    textvariable=s_final_y,
    width=48,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
e_fb_y.pack(side="right", padx=1)
e_fb_x = ctk.CTkEntry(
    f_mov,
    textvariable=s_final_x,
    width=48,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
e_fb_x.pack(side="right", padx=1)

f_rgb = ctk.CTkFrame(left_set_pane, fg_color="transparent")
f_rgb.pack(fill="x", padx=10, pady=2)
ctk.CTkLabel(
    f_rgb,
    text="좌석/배경 RGB",
    font=ctk.CTkFont(family="Malgun Gothic", size=10),
    text_color=TEXT_SUB,
).pack(side="left")
eb_b = ctk.CTkEntry(
    f_rgb,
    textvariable=bg_b,
    width=36,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
eb_b.pack(side="right", padx=1)
eb_g = ctk.CTkEntry(
    f_rgb,
    textvariable=bg_g,
    width=36,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
eb_g.pack(side="right", padx=1)
eb_r = ctk.CTkEntry(
    f_rgb,
    textvariable=bg_r,
    width=36,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
eb_r.pack(side="right", padx=1)
ctk.CTkLabel(f_rgb, text="/", text_color="gray").pack(side="right", padx=2)
es_b = ctk.CTkEntry(
    f_rgb,
    textvariable=seat_b,
    width=36,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
es_b.pack(side="right", padx=1)
es_g = ctk.CTkEntry(
    f_rgb,
    textvariable=seat_g,
    width=36,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
es_g.pack(side="right", padx=1)
es_r = ctk.CTkEntry(
    f_rgb,
    textvariable=seat_r,
    width=36,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
)
es_r.pack(side="right", padx=1)


def save_site_setting():
  name = s_name_var.get().strip()
  if not name:
    messagebox.showerror("오류", "사이트명을 입력해주세요.")
    return
  try:
    TICKETING_SITES[name] = {
        "url": s_url_var.get().strip(),
        "next_month": [int(s_next_x.get()), int(s_next_y.get())],
        "date_start": [int(s_date_x.get()), int(s_date_y.get())],
        "gap_x": int(s_gx.get()),
        "gap_y": int(s_gy.get()),
        "day_btn": [int(s_day_x.get()), int(s_day_y.get())],
        "night_btn": [int(s_night_x.get()), int(s_night_y.get())],
        "book_btn_1": [int(s_b1_x.get()), int(s_b1_y.get())],
        "book_btn_2": [int(s_b2_x.get()), int(s_b2_y.get())],
        "final_book_btn": [int(s_final_x.get()), int(s_final_y.get())],
        "seat_rgb": [int(seat_r.get()), int(seat_g.get()), int(seat_b.get())],
        "bg_rgb": [int(bg_r.get()), int(bg_g.get()), int(bg_b.get())],
        "presets": (
            TICKETING_SITES[name]["presets"]
            if name in TICKETING_SITES
            else {}
        ),
    }
    save_settings_to_json()
    refresh_settings_ui()
    messagebox.showinfo("저장 완료", f"[{name}] 사이트 설정이 저장되었습니다!")
  except ValueError:
    messagebox.showerror("오류", "모든 좌표 및 RGB 값은 숫자여야 합니다.")


def delete_site_setting():
  sel = set_site_sel_var.get()
  if sel in TICKETING_SITES:
    if len(TICKETING_SITES) <= 1:
      messagebox.showerror(
          "삭제 불가", "최소 1개의 티켓 사이트는 남아있어야 합니다."
      )
      return
    if messagebox.askyesno(
        "사이트 삭제 확인", f"[{sel}] 사이트를 정말 삭제하시겠습니까?"
    ):
      del TICKETING_SITES[sel]
      save_settings_to_json()
      refresh_settings_ui()
      messagebox.showinfo("삭제 완료", f"[{sel}] 사이트가 삭제되었습니다.")
  else:
    messagebox.showerror("오류", "삭제할 유효한 사이트를 선택해주세요.")


btn_site_f = ctk.CTkFrame(left_set_pane, fg_color="transparent")
btn_site_f.pack(pady=6)

ctk.CTkButton(
    btn_site_f,
    text="사이트 저장",
    fg_color=ACCENT_BLUE,
    hover_color=ACCENT_HOVER,
    text_color=TEXT_MAIN,
    width=100,
    height=28,
    corner_radius=6,
    font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
    command=save_site_setting,
).pack(side="left", padx=4)

ctk.CTkButton(
    btn_site_f,
    text="사이트 삭제",
    fg_color=NEUTRAL_BTN,
    hover_color=NEUTRAL_HOVER,
    text_color=TEXT_MAIN,
    width=100,
    height=28,
    corner_radius=6,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    command=delete_site_setting,
).pack(side="left", padx=4)


# --- [우측 파트 2] 사이트별 공연장 프리셋 관리 ---
right_set_pane = ctk.CTkFrame(
    main_set_frame,
    fg_color=LIGHT_LAYER,
    corner_radius=6,
    border_width=1,
    border_color=LIGHT_BORDER,
)
right_set_pane.pack(side="right", fill="both", expand=True, padx=6, pady=4)

p_target_site_var = ctk.StringVar()
p_preset_sel_var = ctk.StringVar()
p_venue_name_var = ctk.StringVar()
p_bx, p_by = ctk.StringVar(), ctk.StringVar()
p_gx, p_gy = ctk.StringVar(), ctk.StringVar()
p_cx = ctk.StringVar()


def on_settings_preset_site_changed(choice):
  site = p_target_site_var.get()
  if site in TICKETING_SITES:
    sorted_presets = sorted(list(TICKETING_SITES[site]["presets"].keys()))
    presets = sorted_presets + ["+ 새 프리셋 추가"]
    p_combo.configure(values=presets)
    if presets:
      p_combo.set(presets[0])
      on_settings_preset_selected(presets[0])


def on_settings_preset_selected(choice):
  site = p_target_site_var.get()
  p_sel = p_preset_sel_var.get()
  if site in TICKETING_SITES and p_sel in TICKETING_SITES[site]["presets"]:
    p_venue_name_var.set(p_sel)
    data = TICKETING_SITES[site]["presets"][p_sel]
    p_bx.set(str(data["seat_base_pos"][0]))
    p_by.set(str(data["seat_base_pos"][1]))
    p_gx.set(str(data["seat_gap_x"]))
    p_gy.set(str(data["seat_gap_y"]))
    p_cx.set(str(data["target_center_x"]))
  elif p_sel == "+ 새 프리셋 추가":
    p_venue_name_var.set("")
    p_bx.set("330")
    p_by.set("500")
    p_gx.set("14")
    p_gy.set("14")
    p_cx.set("372")


p_site_f = ctk.CTkFrame(right_set_pane, fg_color="transparent")
p_site_f.pack(fill="x", padx=10, pady=4)
ctk.CTkLabel(
    p_site_f,
    text="적용할 사이트",
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    text_color=TEXT_SUB,
).pack(side="left")

p_site_combo = ctk.CTkComboBox(
    p_site_f,
    variable=p_target_site_var,
    state="readonly",
    width=160,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    dropdown_font=ctk.CTkFont(family="Malgun Gothic", size=11),
    command=on_settings_preset_site_changed,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    button_color=ACCENT_BLUE,
    button_hover_color=ACCENT_HOVER,
    dropdown_fg_color=LIGHT_LAYER,
)
p_site_combo.pack(side="right")

p_sel_f = ctk.CTkFrame(right_set_pane, fg_color="transparent")
p_sel_f.pack(fill="x", padx=10, pady=4)
ctk.CTkLabel(
    p_sel_f,
    text="공연장(프리셋)",
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    text_color=TEXT_SUB,
).pack(side="left")

p_combo = ctk.CTkComboBox(
    p_sel_f,
    variable=p_preset_sel_var,
    state="readonly",
    width=160,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    dropdown_font=ctk.CTkFont(family="Malgun Gothic", size=11),
    command=on_settings_preset_selected,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    button_color=ACCENT_BLUE,
    button_hover_color=ACCENT_HOVER,
    dropdown_fg_color=LIGHT_LAYER,
)
p_combo.pack(side="right")

form_p1 = ctk.CTkFrame(right_set_pane, fg_color="transparent")
form_p1.pack(fill="x", padx=10, pady=2)
ctk.CTkLabel(
    form_p1,
    text="공연장명",
    font=ctk.CTkFont(family="Malgun Gothic", size=10),
    text_color=TEXT_SUB,
).pack(side="left")
ctk.CTkEntry(
    form_p1,
    textvariable=p_venue_name_var,
    width=160,
    fg_color=LIGHT_LAYER,
    border_color=LIGHT_BORDER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
).pack(side="right")

add_coord_row(right_set_pane, "(1,1)좌표 X,Y", p_bx, p_by)
add_coord_row(right_set_pane, "포도알간격(가로,세로)", p_gx, p_gy)


def add_single_row(parent, title, var):
  f = ctk.CTkFrame(parent, fg_color="transparent")
  f.pack(fill="x", padx=10, pady=2)
  ctk.CTkLabel(
      f,
      text=title,
      font=ctk.CTkFont(family="Malgun Gothic", size=10),
      text_color=TEXT_SUB,
  ).pack(side="left")
  ctk.CTkEntry(
      f,
      textvariable=var,
      width=98,
      fg_color=LIGHT_LAYER,
      border_color=LIGHT_BORDER,
      text_color=TEXT_MAIN,
      font=ctk.CTkFont(family="Malgun Gothic", size=11),
  ).pack(side="right")


add_single_row(right_set_pane, "정중앙 x좌표", p_cx)


def save_preset_setting():
  site = p_target_site_var.get()
  v_name = p_venue_name_var.get().strip()
  if not site or not v_name:
    messagebox.showerror("오류", "사이트와 공연장 이름을 확인해주세요.")
    return
  try:
    TICKETING_SITES[site]["presets"][v_name] = {
        "seat_base_pos": [int(p_bx.get()), int(p_by.get())],
        "seat_gap_x": int(p_gx.get()),
        "seat_gap_y": int(p_gy.get()),
        "max_row": 9,
        "max_col": 6,
        "target_center_x": int(p_cx.get()),
    }
    save_settings_to_json()
    refresh_settings_ui()
    messagebox.showinfo(
        "저장 완료", f"[{site}] - [{v_name}] 프리셋이 저장되었습니다!"
    )
  except ValueError:
    messagebox.showerror("오류", "좌표 및 간격 값은 모두 숫자여야 합니다.")


def delete_preset_setting():
  site = p_target_site_var.get()
  p_sel = p_preset_sel_var.get()
  if site in TICKETING_SITES and p_sel in TICKETING_SITES[site]["presets"]:
    if len(TICKETING_SITES[site]["presets"]) <= 1:
      messagebox.showerror(
          "삭제 불가",
          "해당 사이트에 최소 1개의 공연장 프리셋은 남아있어야 합니다.",
      )
      return
    if messagebox.askyesno(
        "프리셋 삭제 확인",
        f"[{site}] 사이트의 [{p_sel}] 프리셋을 정말 삭제하시겠습니까?",
    ):
      del TICKETING_SITES[site]["presets"][p_sel]
      save_settings_to_json()
      refresh_settings_ui()
      messagebox.showinfo("삭제 완료", f"[{p_sel}] 프리셋이 삭제되었습니다.")
  else:
    messagebox.showerror("오류", "삭제할 유효한 프리셋을 선택해주세요.")


btn_preset_f = ctk.CTkFrame(right_set_pane, fg_color="transparent")
btn_preset_f.pack(pady=6)

ctk.CTkButton(
    btn_preset_f,
    text="프리셋 저장",
    fg_color=ACCENT_BLUE,
    hover_color=ACCENT_HOVER,
    text_color=TEXT_MAIN,
    width=100,
    height=28,
    corner_radius=6,
    font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
    command=save_preset_setting,
).pack(side="left", padx=4)

ctk.CTkButton(
    btn_preset_f,
    text="프리셋 삭제",
    fg_color=NEUTRAL_BTN,
    hover_color=NEUTRAL_HOVER,
    text_color=TEXT_MAIN,
    width=100,
    height=28,
    corner_radius=6,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    command=delete_preset_setting,
).pack(side="left", padx=4)


# --- [프레임 4] 좌표 및 RGB 찾기 화면 (CoordFinder Screen) ---
frame_coord_finder = ctk.CTkFrame(container, fg_color=LIGHT_BG)
frames["CoordFinder"] = frame_coord_finder

top_coord_frame = ctk.CTkFrame(
    frame_coord_finder, fg_color=LIGHT_LAYER, height=50, corner_radius=0
)
top_coord_frame.pack(fill="x", padx=0, pady=0)

ctk.CTkButton(
    top_coord_frame,
    text="◀ 메인",
    fg_color=NEUTRAL_BTN,
    hover_color=NEUTRAL_HOVER,
    text_color=TEXT_MAIN,
    width=70,
    height=28,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    command=lambda: show_frame("Main"),
).pack(side="left", padx=16, pady=11)
ctk.CTkLabel(
    top_coord_frame,
    text="🔍 실시간 마우스 좌표 및 RGB 찾기",
    font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"),
    text_color=TEXT_MAIN,
).pack(side="left", padx=8)

ctk.CTkButton(
    top_coord_frame,
    text="✕ 종료",
    fg_color=ACCENT_BLUE,
    hover_color=ACCENT_HOVER,
    text_color=TEXT_MAIN,
    width=70,
    height=28,
    font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
    command=quit_program,
).pack(side="right", padx=16)

main_coord_frame = ctk.CTkFrame(frame_coord_finder, fg_color=LIGHT_BG)
main_coord_frame.pack(fill="both", expand=True, padx=16, pady=12)

left_coord_pane = ctk.CTkFrame(
    main_coord_frame,
    fg_color=LIGHT_LAYER,
    corner_radius=6,
    border_width=1,
    border_color=LIGHT_BORDER,
)
left_coord_pane.pack(side="left", fill="both", expand=True, padx=6, pady=4)


def create_fixed_value_display(parent, label_text, var, val_color):
  ctk.CTkLabel(
      parent,
      text=label_text,
      font=ctk.CTkFont(family="Malgun Gothic", size=11),
      text_color=TEXT_SUB,
  ).pack(anchor="w", padx=16, pady=(12, 2))

  f = ctk.CTkFrame(parent, fg_color="transparent", width=220, height=30)
  f.pack(anchor="w", padx=16)
  f.pack_propagate(False)

  lbl = ctk.CTkLabel(
      f,
      textvariable=var,
      font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
      text_color=val_color,
      anchor="w",
  )
  lbl.pack(fill="both", expand=True)


create_fixed_value_display(left_coord_pane, "마우스 X 좌표", live_x_var, ACCENT_BLUE)
create_fixed_value_display(left_coord_pane, "마우스 Y 좌표", live_y_var, ACCENT_BLUE)
create_fixed_value_display(
    left_coord_pane, "픽셀 RGB 색상", live_rgb_var, TEXT_MAIN
)


def record_current_position():
  try:
    x, y = pyautogui.position()
    r, g, b = pyautogui.pixel(x, y)
    record_text = f"X: {x}, Y: {y} | RGB: ({r}, {g}, {b})\n"
    coord_log_box.insert("end", record_text)
    coord_log_box.see("end")
  except Exception as e:
    print(f"좌표 기록 실패: {e}")


def clear_coord_log():
  coord_log_box.delete("0.0", "end")


btn_coord_action_f = ctk.CTkFrame(left_coord_pane, fg_color="transparent")
btn_coord_action_f.pack(fill="x", padx=16, pady=16)

ctk.CTkButton(
    btn_coord_action_f,
    text="📌 현재 위치 기록 ([Space])",
    fg_color=ACCENT_BLUE,
    hover_color=ACCENT_HOVER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
    height=34,
    corner_radius=6,
    command=record_current_position,
).pack(side="left", fill="x", expand=True, padx=(0, 4))

ctk.CTkButton(
    btn_coord_action_f,
    text="🗑️ 기록 삭제",
    fg_color=NEUTRAL_BTN,
    hover_color=NEUTRAL_HOVER,
    text_color=TEXT_MAIN,
    font=ctk.CTkFont(family="Malgun Gothic", size=11),
    width=90,
    height=34,
    corner_radius=6,
    command=clear_coord_log,
).pack(side="right", padx=(4, 0))

right_coord_pane = ctk.CTkFrame(
    main_coord_frame,
    fg_color=LIGHT_LAYER,
    corner_radius=6,
    border_width=1,
    border_color=LIGHT_BORDER,
)
right_coord_pane.pack(side="right", fill="both", expand=True, padx=6, pady=4)

ctk.CTkLabel(
    right_coord_pane,
    text="기록된 좌표 & RGB 로그",
    font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
    text_color=TEXT_SUB,
).pack(anchor="w", padx=16, pady=(16, 4))

coord_log_box = ctk.CTkTextbox(
    right_coord_pane,
    width=380,
    height=200,
    fg_color=LIGHT_BG,
    text_color=TEXT_MAIN,
    border_color=LIGHT_BORDER,
    border_width=1,
    font=ctk.CTkFont(family="Consolas", size=11),
)
coord_log_box.pack(padx=16, pady=(0, 16), fill="both", expand=True)

for f_name, f_obj in [
    ("Main", frame_main),
    ("Ticketing", frame_ticketing),
    ("Settings", frame_settings),
    ("CoordFinder", frame_coord_finder),
]:
  f_obj.grid(row=0, column=0, sticky="nsew")


def on_f8_press(e):
  global current_index
  if steps and current_index < len(steps):
    s = steps[current_index]
    x, y = s["pos"]
    human_move(x, y)
    print(f"✨ [휴먼라이크 이동 완료] {s['desc']} -> 좌표 ({x}, {y})")


def on_f9_press(e):
  global current_index
  if steps and current_index < len(steps):
    s = steps[current_index]
    x, y = s["pos"]

    if "예매하기 진입" in s["desc"]:
      print("⏳ 보안 우회를 위해 인공 딜레이와 함께 예매하기 클릭 시도...")
      time.sleep(random.uniform(0.3, 0.5))
      natural_click(x, y)
      print(f"🖱️ [클릭 완료] {s['desc']} -> 좌표 ({x}, {y}) 클릭됨!")

      current_index += 1
      update_status_text()

      print("⏳ 좌석 선택 페이지 완전 렌더링 대기 중 (1.2초 후 포도알 스캔)...")
      app.after(1200, bulk_scan_available_seats)
      return

    natural_click(x, y)
    print(f"🖱️ [클릭 완료] {s['desc']} -> 좌표 ({x}, {y}) 클릭됨!")

    current_index += 1
    update_status_text()
  else:
    print("\n⚠️ 설정이 적용되지 않았거나 모든 단계가 이미 끝났습니다.")


def on_f10_press(e):
  selected_site = site_var.get()
  site_data = TICKETING_SITES.get(selected_site)
  if site_data:
    fx, fy = site_data["final_book_btn"]
    print(
        f"🚀 [F10 단축키 입력] [{selected_site}] 최종 예매하기 실행 -> 좌표 ({fx},"
        f" {fy})"
    )
    natural_click(fx, fy)
    status_var.set(f"🚀 [{selected_site}] 최종 예매하기 클릭 완료!")


keyboard.on_press_key("f8", on_f8_press)
keyboard.on_press_key("f9", on_f9_press)
keyboard.on_press_key("f10", on_f10_press)
keyboard.on_press_key("space", lambda e: record_current_position())


def update_live_cursor_info():
  try:
    x, y = pyautogui.position()
    r, g, b = pyautogui.pixel(x, y)
    live_x_var.set(str(x))
    live_y_var.set(str(y))
    live_rgb_var.set(f"R: {r}, G: {g}, B: {b}")
  except Exception:
    pass
  app.after(100, update_live_cursor_info)


def refresh_settings_ui():
  sorted_sites = sorted(
      [s for s in TICKETING_SITES.keys() if s != "+ 새 사이트 추가"]
  )
  sites = sorted_sites + ["+ 새 사이트 추가"]
  st_combo.configure(values=sites)
  if sites:
    st_combo.set(sites[0])
    on_settings_site_selected(sites[0])

  sorted_p_sites = sorted(list(TICKETING_SITES.keys()))
  p_site_combo.configure(values=sorted_p_sites)
  if sorted_p_sites:
    p_site_combo.set(sorted_p_sites[0])
    on_settings_preset_site_changed(sorted_p_sites[0])

  sorted_main_sites = sorted(list(TICKETING_SITES.keys()))
  site_combo.configure(values=sorted_main_sites)
  if sorted_main_sites:
    site_combo.set(sorted_main_sites[0])
    update_venue_combobox()


def update_clock():
  current_server_time = datetime.now() + server_offset
  time_str = current_server_time.strftime("%H:%M:%S.%f")[:-3]
  time_display_var.set(f"{time_str}")
  app.after(50, update_clock)


def update_status_text():
  if not steps:
    status_var.set("티켓팅 화면에서 [설정 적용]을 눌러주세요.")
  elif current_index < len(steps):
    s = steps[current_index]
    status_var.set(f"▶ 다음 목표: {s['desc']}")
  else:
    status_var.set("🎉 모든 단계 완료! 예매 성공 기원!")


app.after(50, update_clock)
app.after(100, update_live_cursor_info)
refresh_settings_ui()
show_frame("Main")

app.mainloop()