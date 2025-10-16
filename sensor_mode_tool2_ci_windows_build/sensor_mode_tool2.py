import tkinter as tk
import serial
import time

# ====== 시리얼 포트 설정 ======
PORT = "/dev/tty.usbmodemLU_2022_88881"  # Mac 기준
BAUD = 115200

try:
    ser = serial.Serial(PORT, BAUD, timeout=0.2)
except Exception as e:
    print("시리얼 연결 실패:", e)
    ser = None

# ====== BW/CR 변환 맵 ======
BW_CODE_MAP = {
    7.8:0x00, 10.4:0x01, 15.6:0x02, 20.8:0x03,
    31.25:0x04, 41.7:0x05, 62.5:0x06,
    125.0:0x07, 250.0:0x08, 500.0:0x09
}

# ====== 로그 출력 함수 ======
def log(msg):
    text_log.insert(tk.END, msg + "\n")
    text_log.see(tk.END)

# ====== 명령 전송 함수 ======
def send_cmd(cmd):
    if not ser or not ser.is_open:
        log("Serial not connected")
        return "Serial not connected"
    try:
        ser.write((cmd + "\r\n").encode())
        time.sleep(0.05)
        resp = []
        while ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                resp.append(line)
        resp_text = "\n".join(resp)
        log(resp_text)
        return resp_text
    except Exception as e:
        log("TX ERR: {}".format(e))
        return "ERR"

# ====== GUI 이벤트 핸들러 ======
def set_channel():
    ch = entry_ch.get().strip()
    if ch:
        send_cmd(f"CH {ch}")

def get_channel():
    resp = send_cmd("GET_CH")
    if "OK:" in resp:
        try:
            parts = resp.split()
            if len(parts) >= 3:
                ch_val = parts[2]
                entry_ch.delete(0, tk.END)
                entry_ch.insert(0, ch_val)
        except Exception as e:
            log(f"ERR parsing CH: {e}")

def set_power():
    pw = entry_pw.get().strip()
    if pw:
        try:
            pw_val = int(pw)
            if not (-9 <= pw_val <= 22):
                log("ERR: Power must be between -9 and 22 dBm")
                return
            send_cmd(f"POW {pw_val}")
        except:
            log("ERR: Invalid Power")

def get_power():
    resp = send_cmd("GET_POW")
    if "OK:" in resp:
        try:
            parts = resp.split()
            if parts[-1].isdigit():
                pw_val = parts[-1]
                entry_pw.delete(0, tk.END)
                entry_pw.insert(0, pw_val)
        except Exception as e:
            log(f"ERR parsing POW: {e}")

def set_modulation():
    sf = entry_sf.get().strip()
    bw = entry_bw.get().strip()
    cr = entry_cr.get().strip()
    try:
        sf_val = int(sf)
        bw_val = float(bw)
        cr_val = int(cr)

        # BW 코드 변환
        bw_code = BW_CODE_MAP.get(bw_val)
        if bw_code is None:
            log(f"ERR: Unsupported BW {bw_val}. Valid: {list(BW_CODE_MAP.keys())}")
            return

        # CR 값 검증
        if cr_val not in (5, 6, 7, 8):
            log("ERR: CR must be 5, 6, 7, or 8")
            return

        send_cmd(f"MOD {sf_val} {bw_code} {cr_val}")

    except Exception as e:
        log(f"ERR: {e}")

def get_modulation():
    resp = send_cmd("GET_MOD")
    if "OK:" in resp:
        parts = resp.split()
        try:
            entry_sf.delete(0, tk.END)
            entry_sf.insert(0, parts[3])
            entry_bw.delete(0, tk.END)
            entry_bw.insert(0, parts[5])
            cr_val = parts[7].split("/")[-1] if "/" in parts[7] else parts[7]
            entry_cr.delete(0, tk.END)
            entry_cr.insert(0, cr_val)
        except:
            pass

# ====== TX 반복 처리 ======
tx_running = False

def tx_loop():
    if tx_running:
        send_cmd("TX")
        root.after(500, tx_loop)

def start_tx():
    global tx_running
    if not tx_running:
        tx_running = True
        tx_loop()

def stop_tx():
    global tx_running
    tx_running = False
    send_cmd("STOP")

# ====== 기타 모드 ======
def rx_mode():
    send_cmd("RX")

def stop_rx():
    send_cmd("STOP_RX")

def standby():
    send_cmd("STBY")

def sleep_mode():
    send_cmd("SLEEP")

def start_cw_mode():
    send_cmd("CW")

def stop_cw_mode():
    send_cmd("STOP_CW")

def get_frequency():
    send_cmd("GET_FREQ")

# ====== GUI 구성 ======
root = tk.Tk()
root.title("LoRa Test GUI")

# 채널
tk.Label(root, text="채널 (MHz)").grid(row=0,column=0)
entry_ch = tk.Entry(root)
entry_ch.grid(row=0,column=1)
tk.Button(root,text="Set CH",command=set_channel).grid(row=0,column=2)
tk.Button(root,text="Get CH",command=get_channel).grid(row=0,column=3)

# 출력 파워
tk.Label(root,text="출력 (dBm)").grid(row=1,column=0)
entry_pw = tk.Entry(root)
entry_pw.grid(row=1,column=1)
tk.Button(root,text="Set POW",command=set_power).grid(row=1,column=2)
tk.Button(root,text="Get POW",command=get_power).grid(row=1,column=3)

# 변조
tk.Label(root,text="SF").grid(row=2,column=0)
entry_sf = tk.Entry(root)
entry_sf.grid(row=2,column=1)
tk.Label(root,text="BW").grid(row=3,column=0)
entry_bw = tk.Entry(root)
entry_bw.grid(row=3,column=1)
tk.Label(root,text="CR").grid(row=4,column=0)
entry_cr = tk.Entry(root)
entry_cr.grid(row=4,column=1)
tk.Button(root,text="Set MOD",command=set_modulation).grid(row=2,column=2,rowspan=3)
tk.Button(root,text="Get MOD",command=get_modulation).grid(row=2,column=3,rowspan=3)

# TX/STOP/RX/STBY/SLEEP/CW
tk.Button(root,text="TX 시작",command=start_tx).grid(row=5,column=0)
tk.Button(root,text="TX 정지",command=stop_tx).grid(row=5,column=1)
tk.Button(root,text="RX 시작",command=rx_mode).grid(row=6,column=0)
tk.Button(root,text="RX 정지",command=stop_rx).grid(row=6,column=1)
tk.Button(root,text="STBY",command=standby).grid(row=5,column=2)
tk.Button(root,text="SLEEP",command=sleep_mode).grid(row=5,column=3)
tk.Button(root,text="CW 시작",command=start_cw_mode).grid(row=7,column=0)
tk.Button(root,text="CW 정지",command=stop_cw_mode).grid(row=7,column=1)

# 로그창
text_log = tk.Text(root,height=15,width=70)
text_log.grid(row=8,column=0,columnspan=7)

root.mainloop()
