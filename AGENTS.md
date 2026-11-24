# AGENTS.md — Zasady projektu Hamster Shooter

## 1. Git i branche (OBOWIĄZKOWE)
- **Nie tworzymy nowych funkcjonalności bezpośrednio na branchu `main`.**
- Przed rozpoczęciem pracy nad nową funkcją lub poprawką zawsze utwórz osobny branch z `main`, np.:
  - `feature/<nazwa-funkcji>` (np. `feature/nowa-bron`, `feature/nowe-skiny`)
  - `fix/<nazwa-poprawki>` (np. `fix/kolizje-platform`)
- Zmiany łączymy z `main` dopiero po przetestowaniu i zatwierdzeniu (merge / Pull Request).
- Nigdy nie commituj prywatnego pliku zapisu `savegame.json` ani folderów `__pycache__/`.

## 2. Technologie i architektura
- **Gra lokalna (Desktop):** Python 3.12 + `pygame-ce` (główna pętla oparta na `asyncio` w `main.py`, z zachowaniem kompatybilności z `Pygbag`).
- **Multiplayer Online i publikacja (Render.com):**
  - Serwer: `server.py` (`aiohttp`, HTTP + WebSockets na porcie z `PORT`).
  - Klient przeglądarkowy: `web/index.html` (cross-play z klientem Pygame przez `net_client.py`).
  - Konfiguracja wdrożenia: `render.yaml` i `requirements-server.txt` (lekka lista bez `pygame-ce`, żeby serwer na Render budował się szybko).

## 3. Kluczowe zasady rozgrywki
- **Styl:** zamknięta mapa 2D w stylu Mario (mury dookoła, platformy, złote bloki `?` uderzane od dołu, rury, trampoliny).
- **Sterowanie:** podwójny skok (`W`/`Spacja`), celowanie myszą 360° i strzelanie (LPM).
- **Zapis postępu (`save_system.py` / `localStorage`):**
  - **Skórki chomików** (aktualnie 50), nick, poziom trudności i portfel ziaren **zapisują się na stałe**.
  - **Bronie** (Karabin, Shotgun, AWP) **działają tylko w bieżącej rundzie** i resetują się do Miotacza Ziaren w nowej rundzie / po restarcie.

## 4. Styl kodu i nauka Pythona
- Projekt służy też do nauki Pythona — pisz kod czysto, dziel go na logiczne pliki (`settings.py`, `entities.py`, `weapons.py`, `map_level.py`, `ui.py`, `sounds.py`, `save_system.py`, `net_client.py`, `server.py`, `main.py`).
- Dodawaj zwięzłe, pomocne komentarze po polsku w ważnych miejscach logiki.
- Po każdej zmianie kodu zweryfikuj kompilację i działanie testem automatycznym.
