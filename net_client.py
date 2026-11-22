"""
net_client.py — Klient WebSocket dla wersji komputerowej Pygame-ce (cross-play z przeglądarką na Render.com!).
Pozwala połączyć grę w Pythonie z serwerem server.py (lokalnie lub na Render.com) i grać w tym samym pokoju z kolegami!
"""

import asyncio
import json
import aiohttp


def normalize_ws_url(raw_host: str) -> str:
    """Zamienia adres serwera (np. 'twoja-gra.onrender.com' lub 'localhost:8000') na poprawny adres WebSocket."""
    addr = raw_host.strip().rstrip("/")
    if not addr:
        addr = "localhost:8000"
    if addr.startswith("https://"):
        addr = "wss://" + addr[len("https://"):]
    elif addr.startswith("http://"):
        addr = "ws://" + addr[len("http://"):]
    elif not addr.startswith("ws://") and not addr.startswith("wss://"):
        if addr.startswith("localhost") or addr.startswith("127.0.0.1"):
            addr = "ws://" + addr
        else:
            addr = "wss://" + addr
    if not addr.endswith("/ws"):
        addr += "/ws"
    return addr


class MultiplayerClient:
    """Asynchroniczny klient WebSocket działający wewnątrz głównej pętli asyncio gry Pygame."""

    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.ws: aiohttp.ClientWebSocketResponse | None = None
        self.recv_task: asyncio.Task | None = None
        self.connected = False
        self.status = "Rozłączony"
        self.player_id: str | None = None
        self.room_code: str = ""
        self.inbox: list[dict] = []

    async def connect(self, server_addr: str, room_code: str, player_name: str, skin_id: str, with_bots: bool = True) -> tuple[bool, str]:
        await self.disconnect()
        url = normalize_ws_url(server_addr)
        self.status = f"Łączenie z {url}..."
        try:
            self.session = aiohttp.ClientSession()
            self.ws = await self.session.ws_connect(url, heartbeat=25.0, timeout=10.0)
            self.connected = True
            await self.send(
                {
                    "type": "join",
                    "room": room_code.strip().upper(),
                    "name": player_name,
                    "skin_id": skin_id,
                    "with_bots": with_bots,
                }
            )
            self.recv_task = asyncio.create_task(self._recv_loop())
            self.status = "Połączono!"
            return True, "Połączono z serwerem!"
        except Exception as exc:
            await self.disconnect()
            msg = f"Błąd połączenia: {exc}"
            self.status = msg
            return False, msg

    async def _recv_loop(self):
        if self.ws is None:
            return
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if data.get("type") == "welcome":
                            self.player_id = data.get("player_id")
                            self.room_code = data.get("room", "")
                        self.inbox.append(data)
                    except Exception:
                        pass
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            self.connected = False

    def pop_messages(self) -> list[dict]:
        msgs = self.inbox
        self.inbox = []
        return msgs

    async def send(self, payload: dict):
        if self.ws is not None and not self.ws.closed:
            try:
                await self.ws.send_str(json.dumps(payload))
            except Exception:
                self.connected = False

    def send_nowait(self, payload: dict):
        """Planuje wysłanie pakietu bez blokowania pętli klatek Pygame."""
        if self.connected and self.ws is not None and not self.ws.closed:
            asyncio.create_task(self.send(payload))

    async def disconnect(self):
        self.connected = False
        if self.recv_task is not None:
            self.recv_task.cancel()
            try:
                await self.recv_task
            except Exception:
                pass
            self.recv_task = None
        if self.ws is not None:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None
        if self.session is not None:
            try:
                await self.session.close()
            except Exception:
                pass
            self.session = None
        self.player_id = None
        self.room_code = ""
