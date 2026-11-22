"""
server.py — Serwer Multiplayer (HTTP + WebSockets) dla Hamster Shooter!
Gotowy do darmowej publikacji na Render.com:
- Serwuje wersję gry w przeglądarce pod adresem '/' (koledzy wchodzą z linku bez instalacji!)
- Obsługuje pokoje multiplayer na żywo pod '/ws' (działa zarówno z przeglądarką, jak i z wersją Python Pygame-ce!)
- Tworzy 4-znakowe kody pokojów (np. K7M2) i linki zaproszeń (?room=K7M2).

Lokalne uruchomienie testowe:
    python server.py
Następnie otwórz w przeglądarce: http://localhost:8000
"""

import asyncio
import json
import math
import os
import random
import time
from aiohttp import web, WSMsgType

# --- Mapa (identyczna jak w map_level.py — zamknięta arena w stylu Mario) ---
TILE_SIZE = 40
MAP_COLS = 40
MAP_ROWS = 22
WORLD_W = MAP_COLS * TILE_SIZE
WORLD_H = MAP_ROWS * TILE_SIZE

LEVEL_LAYOUT = [
    "########################################",
    "#                                      #",
    "#                                      #",
    "#      B?B            B?B        B?B   #",
    "#                                      #",
    "#  BBBB      BBBBB           BBBBB     #",
    "#                  E             E     #",
    "#        E               BBBB          #",
    "#   BBBBBB     B?B              BBBBBB #",
    "#                                      #",
    "#             BBBBBBB                  #",
    "#   E                         E        #",
    "# BBBB   ?              ?        BBBB  #",
    "#           PP      PP                 #",
    "#     BBBB  PP  B?B PP  BBBB           #",
    "#           PP      PP         E       #",
    "#  1             2            BBBBBB   #",
    "# BBBBBB   ^    BBB    ^               #",
    "#        BBBB        BBBB   PP   3   E #",
    "#    S                      PP  BBBBBB #",
    "########################################",
    "########################################",
]

# Wyznaczamy punkty na mapie raz na starcie serwera
SEED_SPOTS: list[tuple[int, int]] = []
BOT_SPAWNS: list[tuple[int, int]] = []
QUESTION_COORDS: list[tuple[int, int]] = []

for _r in range(MAP_ROWS):
    for _c in range(MAP_COLS):
        _ch = LEVEL_LAYOUT[_r][_c]
        if _ch == "?":
            QUESTION_COORDS.append((_c, _r))
        elif _ch == "E":
            BOT_SPAWNS.append((_c * TILE_SIZE + 20, _r * TILE_SIZE + 20))
        if 2 <= _r < MAP_ROWS - 2 and 2 <= _c < MAP_COLS - 2:
            if _ch == " " and LEVEL_LAYOUT[_r + 1][_c] in ("#", "B", "?"):
                SEED_SPOTS.append((_c * TILE_SIZE + 20, _r * TILE_SIZE + 12))

POWERUP_KINDS = ["speed", "shield", "heal", "damage"]
ROOM_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class GameRoom:
    """Pojedynczy pokój multiplayer z własnym 4-znakowym kodem zaproszenia (tylko gracze, bez botów)."""

    def __init__(self, code: str):
        self.code = code
        self.created_at = time.time()
        self.players: dict[str, dict] = {}
        self.sockets: dict[str, web.WebSocketResponse] = {}
        self.next_entity_id = 1

        # Wspólne ziarna, power-upy i bloki '?' w pokoju
        self.seeds: dict[int, dict] = {}
        self.powerups: dict[int, dict] = {}
        self.block_cooldowns: dict[str, float] = {f"{c},{r}": 0.0 for c, r in QUESTION_COORDS}
        self.seed_timer = 1.5

        for _ in range(12):
            self.spawn_random_seed()

    def spawn_random_seed(self):
        if len(self.seeds) >= 18 or not SEED_SPOTS:
            return
        sx, sy = random.choice(SEED_SPOTS)
        sid = self.next_entity_id
        self.next_entity_id += 1
        self.seeds[sid] = {"id": sid, "x": sx, "y": sy, "value": 1}

    def spawn_seed_at(self, x: float, y: float):
        if len(self.seeds) >= 28:
            return
        sid = self.next_entity_id
        self.next_entity_id += 1
        # Upewniamy się, że ziarno jest wewnątrz zamkniętej areny
        cx = max(TILE_SIZE + 14, min(WORLD_W - TILE_SIZE - 14, x))
        cy = max(TILE_SIZE + 14, min(WORLD_H - TILE_SIZE * 2 - 14, y))
        self.seeds[sid] = {"id": sid, "x": round(cx, 1), "y": round(cy, 1), "value": 1}

    def spawn_powerup_at(self, x: float, y: float):
        if len(self.powerups) >= 6:
            return
        pid = self.next_entity_id
        self.next_entity_id += 1
        kind = random.choice(POWERUP_KINDS)
        self.powerups[pid] = {"id": pid, "x": round(x, 1), "y": round(y, 1), "kind": kind, "ttl": 20.0}

    def build_snapshot(self) -> dict:
        # W trybie multiplayer w pokoju są wyłącznie prawdziwi gracze (bez botów!)
        active_blocks = {k: round(v, 2) for k, v in self.block_cooldowns.items() if v > 0}
        return {
            "type": "snapshot",
            "room": self.code,
            "players": list(self.players.values()),
            "seeds": list(self.seeds.values()),
            "powerups": list(self.powerups.values()),
            "blocks": active_blocks,
        }

    async def broadcast(self, message: dict, exclude_id: str | None = None):
        raw = json.dumps(message)
        dead = []
        for pid, ws in list(self.sockets.items()):
            if pid == exclude_id:
                continue
            try:
                await ws.send_str(raw)
            except Exception:
                dead.append(pid)
        for pid in dead:
            self.remove_player(pid)

    def remove_player(self, pid: str):
        self.players.pop(pid, None)
        self.sockets.pop(pid, None)

    async def step(self, dt: float):
        # Odświeżanie bloków '?', pojawianie się ziaren i czas trwania power-upów
        for k in list(self.block_cooldowns.keys()):
            if self.block_cooldowns[k] > 0:
                self.block_cooldowns[k] = max(0.0, self.block_cooldowns[k] - dt)

        self.seed_timer -= dt
        if self.seed_timer <= 0:
            self.seed_timer = 2.2
            self.spawn_random_seed()

        for pid in list(self.powerups.keys()):
            self.powerups[pid]["ttl"] -= dt
            if self.powerups[pid]["ttl"] <= 0:
                self.powerups.pop(pid, None)


class MultiplayerServer:
    """Zarządza wszystkimi pokojami i połączeniami WebSocket."""

    def __init__(self):
        self.rooms: dict[str, GameRoom] = {}
        self.player_counter = 1

    def generate_code(self) -> str:
        for _ in range(100):
            code = "".join(random.choice(ROOM_CHARS) for _ in range(4))
            if code not in self.rooms:
                return code
        return str(random.randint(1000, 9999))

    def get_or_create_room(self, code: str) -> GameRoom:
        clean = "".join(ch for ch in code.upper() if ch.isalnum())[:6]
        if not clean:
            clean = self.generate_code()
        if clean not in self.rooms:
            self.rooms[clean] = GameRoom(clean)
        return self.rooms[clean]

    async def tick_loop(self):
        """Główna pętla serwera: 20 razy na sekundę aktualizuje pokoje i wysyła stan do graczy."""
        last = time.monotonic()
        while True:
            await asyncio.sleep(0.05)  # 20 Hz
            now = time.monotonic()
            dt = min(now - last, 0.1)
            last = now

            empty_codes = []
            for code, room in list(self.rooms.items()):
                if not room.sockets:
                    if now - room.created_at > 20.0:
                        empty_codes.append(code)
                    continue
                await room.step(dt)
                await room.broadcast(room.build_snapshot())

            for code in empty_codes:
                self.rooms.pop(code, None)

    async def ws_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=25.0)
        await ws.prepare(request)

        pid = f"p{self.player_counter}"
        self.player_counter += 1
        room: GameRoom | None = None

        try:
            async for msg in ws:
                if msg.type != WSMsgType.TEXT:
                    continue
                try:
                    data = json.loads(msg.data)
                except Exception:
                    continue

                mtype = data.get("type")

                if mtype == "join":
                    req_room = str(data.get("room", "")).strip()
                    name = str(data.get("name", "Chomik")).strip()[:14] or "Chomik"
                    skin_id = str(data.get("skin_id", "klasyczny"))

                    room = self.get_or_create_room(req_room)
                    room.sockets[pid] = ws
                    room.players[pid] = {
                        "id": pid,
                        "name": name,
                        "is_bot": False,
                        "x": 220.0,
                        "y": float(WORLD_H - 120),
                        "vx": 0.0,
                        "vy": 0.0,
                        "aim": 0.0,
                        "facing_right": True,
                        "skin_id": skin_id,
                        "weapon_id": "ziarna",
                        "hp": 100,
                        "max_hp": 100,
                        "alive": True,
                        "seeds": 0,
                        "total_seeds": 0,
                        "kills": 0,
                        "shield": 0.0,
                        "damage_boost": 0.0,
                    }

                    snap = room.build_snapshot()
                    await ws.send_str(
                        json.dumps(
                            {
                                "type": "welcome",
                                "player_id": pid,
                                "room": room.code,
                                "players": snap["players"],
                                "seeds": snap["seeds"],
                                "powerups": snap["powerups"],
                                "blocks": snap["blocks"],
                            }
                        )
                    )
                    await room.broadcast({"type": "notice", "text": f"{name} dołączył do pokoju {room.code}!"}, exclude_id=pid)

                elif room is None:
                    continue

                elif mtype == "update":
                    p = room.players.get(pid)
                    if p is not None:
                        for key in ("x", "y", "vx", "vy", "aim", "facing_right", "skin_id", "weapon_id", "hp", "max_hp", "alive", "seeds", "total_seeds", "kills", "shield", "damage_boost"):
                            if key in data:
                                p[key] = data[key]
                        if "name" in data and str(data["name"]).strip():
                            p["name"] = str(data["name"]).strip()[:14]

                elif mtype == "shoot":
                    p = room.players.get(pid)
                    await room.broadcast(
                        {
                            "type": "shoot",
                            "owner_id": pid,
                            "owner_name": p["name"] if p else "Chomik",
                            "x": data.get("x", 0),
                            "y": data.get("y", 0),
                            "angle": data.get("angle", 0),
                            "weapon_id": data.get("weapon_id", "ziarna"),
                            "damage_mult": data.get("damage_mult", 1.0),
                        },
                        exclude_id=pid,
                    )

                elif mtype == "hit":
                    target_id = str(data.get("target_id", ""))
                    dmg = max(1, min(200, int(data.get("damage", 15))))
                    attacker = room.players.get(pid)
                    attacker_name = attacker["name"] if attacker else "Chomik"

                    # Trafienie innego gracza (kolegi w pokoju!)
                    if target_id in room.players and target_id != pid:
                        target_ws = room.sockets.get(target_id)
                        if target_ws is not None:
                            try:
                                await target_ws.send_str(
                                    json.dumps(
                                        {
                                            "type": "damaged",
                                            "target_id": target_id,
                                            "attacker_id": pid,
                                            "attacker_name": attacker_name,
                                            "damage": dmg,
                                            "killed": False,
                                        }
                                    )
                                )
                            except Exception:
                                pass

                elif mtype == "player_died":
                    # Gracz zginął — rozsypujemy ziarna na mapie dla wszystkich!
                    x = float(data.get("x", 300))
                    y = float(data.get("y", 400))
                    killer_name = str(data.get("killer_name", ""))
                    killer_id = str(data.get("killer_id", ""))
                    victim = room.players.get(pid)
                    vname = victim["name"] if victim else "Chomik"
                    for _ in range(3):
                        room.spawn_seed_at(x + random.uniform(-50, 50), y - 16)
                    if killer_name:
                        await room.broadcast({"type": "notice", "text": f"{killer_name} pokonał {vname}!"})
                    if killer_id in room.sockets:
                        try:
                            await room.sockets[killer_id].send_str(json.dumps({"type": "kill_credit", "victim_name": vname}))
                        except Exception:
                            pass

                elif mtype == "collect_seed":
                    sid = int(data.get("seed_id", -1))
                    seed = room.seeds.pop(sid, None)
                    if seed is not None:
                        await ws.send_str(json.dumps({"type": "seed_awarded", "value": seed["value"], "x": seed["x"], "y": seed["y"]}))

                elif mtype == "collect_powerup":
                    pup_id = int(data.get("powerup_id", -1))
                    pup = room.powerups.pop(pup_id, None)
                    if pup is not None:
                        await ws.send_str(json.dumps({"type": "powerup_awarded", "kind": pup["kind"]}))

                elif mtype == "bump_block":
                    c = int(data.get("col", -1))
                    r = int(data.get("row", -1))
                    key = f"{c},{r}"
                    if key in room.block_cooldowns and room.block_cooldowns[key] <= 0:
                        room.block_cooldowns[key] = 12.0
                        bx = c * TILE_SIZE + 20
                        by = r * TILE_SIZE - 14
                        if random.random() < 0.35:
                            room.spawn_powerup_at(bx, by)
                        else:
                            for _ in range(random.randint(2, 3)):
                                room.spawn_seed_at(bx + random.uniform(-35, 35), by)
                        await room.broadcast({"type": "block_bumped", "col": c, "row": r})

        finally:
            if room is not None:
                p = room.players.get(pid)
                pname = p["name"] if p else "Gracz"
                room.remove_player(pid)
                await room.broadcast({"type": "notice", "text": f"{pname} opuścił pokój."})

        return ws


def create_app() -> web.Application:
    mp = MultiplayerServer()
    app = web.Application()

    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
    index_path = os.path.join(web_dir, "index.html")

    async def index_handler(_request):
        return web.FileResponse(index_path)

    async def health_handler(_request):
        return web.json_response({"status": "ok", "rooms": len(mp.rooms)})

    async def on_startup(application):
        application["tick_task"] = asyncio.create_task(mp.tick_loop())

    async def on_cleanup(application):
        task = application.get("tick_task")
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    app.router.add_get("/", index_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/ws", mp.ws_handler)
    if os.path.isdir(web_dir):
        app.router.add_static("/static", web_dir)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Hamster Shooter Multiplayer Server startuje na http://0.0.0.0:{port}")
    web.run_app(create_app(), host="0.0.0.0", port=port)
