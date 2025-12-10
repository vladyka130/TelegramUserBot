#!/usr/bin/env python3
"""
arp_mitigator_fixed.py

Scapy mitigation for ARP Who-Has:
- слухає Who-Has (ARP op=1) на інтерфейсі,
- знаходить MAC для target IP (system arp cache або короткий ARP lookup),
- відсилає правильну ARP is-at відповідь, де:
    Ethernet.src == ARP.hwsrc == target_mac
- відсилає reply кілька разів + опційно відправляє broadcast gratuitous,
- лог і live лічильник.

Примітка: це ARP-reply mitigation — не kernel-level drop.
Запускати як Адмін.
"""
import argparse
import time
import threading
import sys
from scapy.all import (
    sniff, sendp, Ether, ARP, srp1, conf, get_if_hwaddr
)
import subprocess
import psutil
import os

LOG_FILE = "../../venv/Pycharm2025/c_helper_flet/arp_mitigator_fixed.log"
SNAP_TIMEOUT = 1  # секунд для короткого ARP lookup
RETRIES = 3       # скільки разів шлемо reply
STATUS_INTERVAL = 2.0

running = True
observed = 0
replied = 0

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def get_system_arp(ip):
    try:
        out = subprocess.check_output(["arp", "-a"], text=True, encoding="utf-8", errors="ignore")
        for line in out.splitlines():
            if ip in line:
                parts = line.split()
                for p in parts:
                    if "-" in p and len(p) >= 15:
                        return p.replace("-", ":")
    except Exception:
        return None
    return None

def quick_arp_lookup(target_ip, iface):
    try:
        # надсилаємо Who-Has та чекаємо на відповідь
        pkt = srp1(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=target_ip), iface=iface, timeout=SNAP_TIMEOUT, verbose=0)
        if pkt and pkt.haslayer(ARP):
            return pkt[ARP].hwsrc
    except Exception as e:
        log(f"quick_arp_lookup error: {e}")
    return None

def craft_and_send_reply(target_ip, target_mac, requester_mac, requester_ip, iface, send_broadcast=False):
    """
    Відправляємо ARP is-at так, щоб Ethernet.src == target_mac і ARP.hwsrc == target_mac
    Надсилаємо кілька копій і опціонально broadcast gratuitous.
    """
    global replied
    try:
        for i in range(RETRIES):
            # Ethernet.src має бути target_mac (імітація того, що цю IP має target_mac)
            ether = Ether(dst=requester_mac, src=target_mac)
            arp = ARP(op=2, hwsrc=target_mac, psrc=target_ip, hwdst=requester_mac, pdst=requester_ip)
            pkt = ether/arp
            sendp(pkt, iface=iface, verbose=0)
            replied += 1
            time.sleep(0.12)  # невелика пауза між копіями

        if send_broadcast:
            # gratuitous ARP broadcast: Ethernet dst = ff:ff..., ARP hwdst = ff:... pdst = target_ip
            ether_b = Ether(dst="ff:ff:ff:ff:ff:ff", src=target_mac)
            arp_b = ARP(op=2, hwsrc=target_mac, psrc=target_ip, hwdst="ff:ff:ff:ff:ff:ff", pdst=target_ip)
            sendp(ether_b/arp_b, iface=iface, verbose=0)
            log(f"Sent gratuitous broadcast for {target_ip} as {target_mac} on {iface}")

        log(f"Sent {RETRIES} ARP reply(s): {target_ip} is-at {target_mac} -> to {requester_ip} ({requester_mac}) on {iface}")
    except Exception as e:
        log(f"Error sending reply: {e}")

def handle_arp(pkt, iface, only_local=True, send_broadcast=False):
    """
    Обробка ARP пакета. Реагуємо на Who-Has (op==1).
    Параметр only_local: якщо True — реагуємо тільки на Who-Has, що походять від нашої машини.
    """
    global observed
    try:
        if not pkt.haslayer(ARP):
            return
        arp = pkt[ARP]
        if arp.op != 1:
            return

        requester_mac = arp.hwsrc.lower()
        requester_ip = arp.psrc if arp.psrc != "0.0.0.0" else None
        target_ip = arp.pdst

        observed += 1
        log(f"Observed Who-Has: {requester_ip} ({requester_mac}) asks who-has {target_ip}")

        # якщо тільки локальні запити — перевіряємо
        if only_local:
            local_ips = set()
            for ifname, addrs in psutil.net_if_addrs().items():
                for a in addrs:
                    if hasattr(a, 'address') and a.address:
                        local_ips.add(a.address)
            our_mac = get_if_hwaddr(iface).lower()
            if (requester_ip not in local_ips) and (requester_mac != our_mac):
                log(" -> Ignored (not local requester)")
                return

        # 1) попытка з ARP cache
        mac = get_system_arp(target_ip)
        if not mac:
            # 2) короткий ARP lookup
            mac = quick_arp_lookup(target_ip, iface)

        if mac:
            # якщо MAC знайшли — відправляємо reply, встановлюючи Ethernet.src=target_mac
            craft_and_send_reply(target_ip, mac, requester_mac, requester_ip or "0.0.0.0", iface, send_broadcast=send_broadcast)
        else:
            log(f" -> No MAC found for {target_ip} (skipping)")

    except Exception as e:
        log(f"handle_arp exception: {e}")

def start_sniff(iface, only_local=True, send_broadcast=False):
    log(f"Starting sniff on iface: {iface}, filter: arp")
    sniff(iface=iface, filter="arp", prn=lambda p: handle_arp(p, iface, only_local, send_broadcast), store=0)

def status_printer():
    global observed, replied
    start = time.time()
    while running:
        elapsed = int(time.time() - start)
        print(f"\r⏱ {elapsed:4d}s | Observed Who-Has: {observed:6d} | Sent replies: {replied:6d}", end="", flush=True)
        time.sleep(STATUS_INTERVAL)

def choose_interface(name_hint=None):
    ifaces = conf.ifaces.data
    names = [iface.name for iface in ifaces.values()]
    if name_hint:
        for n in names:
            if name_hint.lower() in n.lower():
                return n
    print("Available interfaces:")
    for i, n in enumerate(names):
        print(f"  [{i}] {n}")
    idx = input("Choose interface (number): ").strip()
    try:
        idx = int(idx)
        return names[idx]
    except Exception:
        return names[0]

def main():
    global running
    import argparse
    parser = argparse.ArgumentParser(description="ARP Mitigator Fixed (Scapy + Npcap)")
    parser.add_argument("--iface", "-i", help="Interface name", default=None)
    parser.add_argument("--all", action="store_true", help="React to all Who-Has (not only local sources)")
    parser.add_argument("--broadcast", action="store_true", help="Send gratuitous broadcast after replies")
    args = parser.parse_args()

    iface = args.iface or choose_interface()
    only_local = not args.all
    send_broadcast = args.broadcast

    log(f"Using interface: {iface} (only_local={only_local}, broadcast={send_broadcast})")
    t_status = threading.Thread(target=status_printer, daemon=True)
    t_status.start()

    try:
        start_sniff(iface, only_local=only_local, send_broadcast=send_broadcast)
    except KeyboardInterrupt:
        log("KeyboardInterrupt — stopping")
    finally:
        running = False
        time.sleep(0.2)
        log("Stopped.")

if __name__ == "__main__":
    main()
