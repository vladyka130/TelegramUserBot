"""
ARP/TCP Correlator (Windows) + Live Netstat Monitor
Автор: Ukrainian Voice GPT 🇺🇦
Пояснення:
 - Сніфить ARP і TCP SYN пакети.
 - Корелює їх із відкритими з’єднаннями (psutil).
 - Відображає GUI із живим логом і live netstat монітором (оновлення кожні 10с).
"""

import threading
import time
import subprocess
from collections import deque
from datetime import datetime
import psutil
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from scapy.all import sniff, ARP, TCP, IP

TIME_WINDOW_DEFAULT = 5.0
NETSTAT_INTERVAL = 10.0  # секунд між оновленнями

recent_candidates = deque(maxlen=2000)
recent_pids = set()
sample_lock = threading.Lock()
running = False
netstat_running = False


# ---------- Логіка збору даних ----------
def sample_connections_loop():
    global running
    while running:
        try:
            conns = psutil.net_connections(kind='inet')
            now = time.time()
            with sample_lock:
                for c in conns:
                    if c.raddr:
                        pid = c.pid
                        try:
                            proc = psutil.Process(pid) if pid else None
                            pname = proc.name() if proc else None
                            pcmd = " ".join(proc.cmdline()) if proc else ""
                        except Exception:
                            pname, pcmd = None, ""
                        entry = (now, pid, pname, pcmd, c.laddr, c.raddr, c.status, c.type)
                        recent_candidates.append(entry)
        except Exception:
            pass
        time.sleep(1.0)


def correlate_ip(target_ip, arp_time, time_window):
    candidates = []
    thr = arp_time - time_window
    with sample_lock:
        for entry in list(recent_candidates):
            ts, pid, pname, pcmd, laddr, raddr, status, socktype = entry
            if ts < thr:
                continue
            try:
                r_ip = raddr[0]
            except Exception:
                continue
            if r_ip == target_ip:
                candidates.append({
                    "pid": pid,
                    "name": pname,
                    "cmd": pcmd,
                    "laddr": laddr,
                    "raddr": raddr,
                    "status": status,
                    "sock_type": "TCP" if socktype == psutil.SOCK_STREAM else "UDP"
                })
                if pid:
                    recent_pids.add(pid)
    return candidates


def arp_tcp_callback(pkt, time_window, gui_append):
    t = time.time()
    if pkt.haslayer(ARP):
        arp = pkt[ARP]
        typ = "REQUEST" if arp.op == 1 else "REPLY"
        msg = f"ARP {typ}: {arp.psrc} -> {arp.pdst}  hwsrc={arp.hwsrc}"
        gui_append(msg)
        candidates = correlate_ip(arp.pdst, t, time_window)
        if candidates:
            for c in candidates:
                gui_append(f"  PID={c['pid']} | {c['name']} | {c['cmd']}")
        gui_append("-" * 50)

    elif pkt.haslayer(TCP) and pkt.haslayer(IP):
        tcp, ip = pkt[TCP], pkt[IP]
        if tcp.flags & 0x02 and not (tcp.flags & 0x10):  # SYN без ACK
            msg = f"TCP SYN: {ip.src}:{tcp.sport} -> {ip.dst}:{tcp.dport}"
            gui_append(msg)
            candidates = correlate_ip(ip.dst, t, time_window)
            if candidates:
                for c in candidates:
                    gui_append(f"  PID={c['pid']} | {c['name']} | {c['cmd']}")
            gui_append("-" * 50)


# ---------- GUI ----------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("ARP/TCP Correlator + Netstat Live (Windows)")
        self.time_window_var = tk.DoubleVar(value=TIME_WINDOW_DEFAULT)
        self.filter_var = tk.StringVar(value="arp or tcp")

        frm = ttk.Frame(root, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)

        cfg = ttk.Frame(frm)
        cfg.pack(fill=tk.X)

        ttk.Label(cfg, text="Time window (s):").pack(side=tk.LEFT)
        ttk.Entry(cfg, width=6, textvariable=self.time_window_var).pack(side=tk.LEFT, padx=4)
        ttk.Label(cfg, text="Filter:").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Entry(cfg, width=20, textvariable=self.filter_var).pack(side=tk.LEFT, padx=4)

        self.btn_start = ttk.Button(cfg, text="Start", command=self.start)
        self.btn_start.pack(side=tk.LEFT, padx=4)
        self.btn_stop = ttk.Button(cfg, text="Stop", command=self.stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=4)
        self.btn_netstat = ttk.Button(cfg, text="Open Live Netstat", command=self.show_netstat)
        self.btn_netstat.pack(side=tk.LEFT, padx=4)

        self.log = scrolledtext.ScrolledText(frm, height=25, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True, pady=6)

    def append_log(self, text):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, f"[{ts}] {text}\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def start(self):
        global running
        if running:
            return
        running = True
        self.btn_start.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        self.append_log("🟢 Starting capture...")
        threading.Thread(target=sample_connections_loop, daemon=True).start()

        def _prn(pkt):
            self.root.after(0, arp_tcp_callback, pkt, float(self.time_window_var.get()), self.append_log)

        threading.Thread(
            target=lambda: sniff(filter=self.filter_var.get(), prn=_prn, store=False),
            daemon=True
        ).start()

    def stop(self):
        global running
        running = False
        self.btn_stop.configure(state=tk.DISABLED)
        self.btn_start.configure(state=tk.NORMAL)
        self.append_log("🛑 Capture stopped.")

    def show_netstat(self):
        """Відкриває live-вікно з netstat."""
        win = tk.Toplevel(self.root)
        win.title("Netstat Live Monitor")

        txt = scrolledtext.ScrolledText(win, height=30, width=110)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.tag_config("highlight", background="#ccffcc")

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, pady=4)
        btn_update = ttk.Button(btn_frame, text="🔁 Оновити зараз", command=lambda: self.update_netstat(txt))
        btn_update.pack(side=tk.LEFT, padx=5)
        self.live_var = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(btn_frame, text="Auto-refresh (10s)", variable=self.live_var)
        chk.pack(side=tk.LEFT, padx=5)

        def auto_update():
            if not win.winfo_exists():
                return
            if self.live_var.get():
                self.update_netstat(txt)
            win.after(int(NETSTAT_INTERVAL * 1000), auto_update)

        auto_update()

        self.update_netstat(txt)

    def update_netstat(self, widget):
        """Оновлює вміст netstat."""
        try:
            output = subprocess.check_output(["netstat", "-ano"], text=True, stderr=subprocess.STDOUT)
        except Exception as e:
            widget.insert(tk.END, f"Помилка netstat: {e}\n")
            return
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        for line in output.splitlines():
            highlight = any(f" {pid}" in line or line.endswith(str(pid)) for pid in recent_pids)
            if highlight:
                widget.insert(tk.END, line + "\n", "highlight")
            else:
                widget.insert(tk.END, line + "\n")
        widget.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
