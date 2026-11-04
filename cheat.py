# language: python, file: cheat.py — память CS2, ESP, radar, trigger через SendInput
import time
import threading
import math
import json
import os
import ctypes
from ctypes import wintypes

import pymem
import pymem.process
import win32api
import win32con

from offsets import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

try:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        CFG = json.load(f)
except Exception:
    CFG = {}

def save_config():
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(CFG, f, indent=2)
    except Exception:
        pass

# экранное разрешение — не хардкод
SCREEN_W = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_H = ctypes.windll.user32.GetSystemMetrics(1)


class Memory:
    def __init__(self):
        self.pm = None
        self.client = 0
        self.pid = 0
        self.ready = False

    def attach(self):
        try:
            self.pm = pymem.Pymem("cs2.exe")
            self.pid = self.pm.process_id
            mod = pymem.process.module_from_name(self.pm.process_handle, "client.dll")
            if not mod:
                self.ready = False
                return False
            self.client = mod.lpBaseOfDll
            self.ready = True
            return True
        except Exception:
            self.pm = None
            self.ready = False
            return False

    def read_int(self, addr):
        try:
            return self.pm.read_int(addr)
        except Exception:
            return 0

    def read_bool(self, addr):
        try:
            return self.pm.read_bool(addr)
        except Exception:
            return False

    def read_ptr(self, addr):
        try:
            return self.pm.read_longlong(addr)
        except Exception:
            return 0

    def read_vec3(self, addr):
        try:
            return (self.pm.read_float(addr),
                    self.pm.read_float(addr + 4),
                    self.pm.read_float(addr + 8))
        except Exception:
            return (0.0, 0.0, 0.0)

    def read_matrix(self, addr):
        try:
            return [self.pm.read_float(addr + i * 4) for i in range(16)]
        except Exception:
            return [0.0] * 16


mem = Memory()

overlay_data = {
    "boxes": [],
    "texts": [],
    "radar": [],
    "ready": False,
    "pid": 0,
}
overlay_lock = threading.Lock()


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def vec_len(a):
    return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)

def dist(a, b):
    return vec_len(vec_sub(a, b))

def world_to_screen(pos, mat, w, h):
    cw = mat[12] * pos[0] + mat[13] * pos[1] + mat[14] * pos[2] + mat[15]
    if cw < 0.001:
        return None
    cx = mat[0] * pos[0] + mat[1] * pos[1] + mat[2] * pos[2] + mat[3]
    cy = mat[4] * pos[0] + mat[5] * pos[1] + mat[6] * pos[2] + mat[7]
    nx = cx / cw
    ny = cy / cw
    return ((w / 2.0) * (nx + 1.0), (h / 2.0) * (1.0 - ny))

def calc_angle(src, dst):
    d = vec_sub(dst, src)
    hyp = math.sqrt(d[0] ** 2 + d[1] ** 2)
    ax = -math.degrees(math.atan2(d[2], hyp)) if hyp != 0 else 0.0
    ay = math.degrees(math.atan2(d[1], d[0]))
    return (ax, ay, 0.0)

def angle_dist(a, b):
    dx = math.remainder(a[0] - b[0], 360.0)
    dy = math.remainder(a[1] - b[1], 360.0)
    return math.sqrt(dx * dx + dy * dy)

# --- SendInput вместо mouse_event/keybd_event (CS2 raw input) ---
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

def send_mouse(flags):
    inp = INPUT(type=0)
    inp.mi = MOUSEINPUT(0, 0, 0, flags, 0, None)
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def send_key(vk, up=False):
    inp = INPUT(type=1)
    flags = 0x0002 if up else 0
    inp.ki = KEYBDINPUT(vk, 0, flags, 0, None)
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def read_entity(pawn):
    if not pawn:
        return {"pawn": 0, "origin": (0, 0, 0), "head": (0, 0, 0),
                "hp": 0, "team": 0, "life": 0, "dormant": False}
    hp = mem.read_int(pawn + M_I_HEALTH)
    team = mem.read_int(pawn + M_I_TEAM_NUM)
    life = mem.read_int(pawn + M_LIFE_STATE)
    dormant = mem.read_bool(pawn + M_B_DORMANT)
    origin = mem.read_vec3(pawn + M_VEC_ORIGIN)
    view_off = mem.read_vec3(pawn + M_VEC_VIEW_OFFSET)
    head = (origin[0], origin[1], origin[2] + view_off[2])
    return {"pawn": pawn, "origin": origin, "head": head,
            "hp": hp, "team": team, "life": life, "dormant": dormant}


def get_entities():
    if not mem.ready:
        return None, []
    entity_list = mem.read_ptr(mem.client + DW_ENTITY_LIST)
    if not entity_list:
        return None, []
    local_pawn = mem.read_ptr(mem.client + DW_LOCAL_PLAYER_PAWN)
    if not local_pawn:
        return None, []
    me = read_entity(local_pawn)
    ents = []
    for i in range(1, 65):
        try:
            list_entry = mem.read_ptr(entity_list + 0x10 + 8 * (i >> 9))
            if not list_entry:
                continue
            pawn = mem.read_ptr(list_entry + 0x78 * (i & 0x1FF))
            if not pawn or pawn == local_pawn:
                continue
            e = read_entity(pawn)
            if e["hp"] <= 0 or e["life"] != 0 or e["dormant"]:
                continue
            ents.append(e)
        except Exception:
            continue
    return me, ents


def compute_overlay():
    me, ents = get_entities()
    if me is None or not mem.ready:
        with overlay_lock:
            overlay_data["ready"] = mem.ready
            overlay_data["pid"] = mem.pid
        return
    view = mem.read_matrix(mem.client + DW_VIEW_MATRIX)

    boxes, texts, radar = [], [], []
    for e in ents:
        if not CFG.get("esp_team", False) and e["team"] == me["team"]:
            continue
        d = dist(me["origin"], e["origin"])
        if d > CFG.get("esp_max_dist", 2000):
            continue

        hs = world_to_screen(e["head"], view, SCREEN_W, SCREEN_H)
        fs = world_to_screen(e["origin"], view, SCREEN_W, SCREEN_H)
        if hs and fs:
            boxes.append((hs[0], hs[1], fs[0], fs[1], e["hp"]))
            if CFG.get("esp_name", True):
                texts.append((hs[0], hs[1] - 16, "enemy"))
            if CFG.get("esp_distance", True):
                texts.append((hs[0], fs[1] + 2, f"{d / 100:.0f}m"))

        rx = (e["origin"][0] - me["origin"][0]) * 0.05
        ry = (e["origin"][1] - me["origin"][1]) * 0.05
        radar.append((rx, ry, e["team"] == me["team"]))

    with overlay_lock:
        overlay_data["boxes"] = boxes
        overlay_data["texts"] = texts
        overlay_data["radar"] = radar
        overlay_data["ready"] = mem.ready
        overlay_data["pid"] = mem.pid


def trigger_tick():
    if not CFG.get("trigger_enabled", False):
        return
    me, ents = get_entities()
    if me is None or not mem.ready:
        return
    view_angles = mem.read_vec3(mem.client + DW_VIEW_ANGLES)
    for e in ents:
        if e["team"] == me["team"]:
            continue
        target = calc_angle(me["head"], e["head"])
        if angle_dist(view_angles, target) <= CFG.get("trigger_fov", 2.0):
            send_mouse(0x0002)  # LEFTDOWN
            time.sleep(0.01)
            send_mouse(0x0004)  # LEFTUP
            time.sleep(CFG.get("trigger_delay", 30) / 1000.0)
            break


def movement_tick():
    if not mem.ready:
        return
    me, _ = get_entities()
    if me is None or not me["pawn"]:
        return

    if CFG.get("no_recoil", False):
        punch = mem.read_vec3(me["pawn"] + M_AIM_PUNCH_ANGLE)
        if punch[0] != 0 or punch[1] != 0:
            va = mem.read_vec3(mem.client + DW_VIEW_ANGLES)
            corrected = (va[0] - punch[0] * 2.0, va[1] - punch[1] * 2.0, 0.0)
            try:
                mem.pm.write_float(mem.client + DW_VIEW_ANGLES, corrected[0])
                mem.pm.write_float(mem.client + DW_VIEW_ANGLES + 4, corrected[1])
            except Exception:
                pass

    if CFG.get("bhop_enabled", False) and (win32api.GetAsyncKeyState(win32con.VK_SPACE) & 0x8000):
        flags = mem.read_int(me["pawn"] + M_F_FLAGS)
        if flags & 1:
            send_key(win32con.VK_SPACE, up=False)
            send_key(win32con.VK_SPACE, up=True)


def cheat_loop():
    while True:
        if not mem.ready:
            if not mem.attach():
                with overlay_lock:
                    overlay_data["ready"] = False
                time.sleep(2.0)
                continue
        try:
            if not mem.pm or not mem.pm.process_handle:
                mem.ready = False
                continue
            compute_overlay()
            trigger_tick()
            movement_tick()
        except Exception:
            mem.ready = False
        time.sleep(0.05)


def start_cheat():
    t = threading.Thread(target=cheat_loop, daemon=True)
    t.start()
    return t
