# Hamster Shooter — Bitwa o Ziarna Słonecznika 🐹🌻

Platformowa strzelanka 2D w stylu Mario z **trybem Singleplayer (7 botów + 3 boty fabularne)** oraz **Multiplayer Online** (gotowym do darmowej publikacji na **Render.com**!).

## Funkcje gry
- **Cel gry:** Zbieraj ziarna słonecznika (cel rundy: 50 ziaren) i walcz o 1. miejsce w rankingu.
- **Sterowanie:** `A`/`D` (bieg), `W`/`Spacja` (skok i **podwójny skok**), **Myszka + LPM** (celowanie 360° i strzał), `1`–`4`/kółko (Ziarna, Karabin, Shotgun, AWP), `E` (rozmowa z NPC), `B` (Sklep), `ESC` (Menu), `M` (dźwięk).
- **50 skórek chomików:** kupione skórki zapisują się na stałe! Bronie (Karabin, Shotgun, AWP) działają na jedną rundę.
- **3 poziomy trudności** (Łatwy, Normalny, Trudny) + **własny nick gracza**.
- **Multiplayer Online (Cross-Play!):** graj z kolegami przez przeglądarkę albo w aplikacji Python Pygame-ce w tym samym pokoju!

## Jak uruchomić na komputerze (Singleplayer + klient Online)?
```bash
pip install -r requirements.txt
python main.py
```
Albo po prostu kliknij dwukrotnie `zagraj.bat`.

## Jak przetestować Multiplayer lokalnie?
1. Uruchom serwer gry:
   ```bash
   python server.py
   ```
2. Otwórz w przeglądarce `http://localhost:8000` (możesz otworzyć 2 karty naraz i grać ze sobą!) albo w grze `main.py` kliknij **MULTIPLAYER ONLINE** i połącz się z `localhost:8000`.

## Jak opublikować grę ZA DARMO na Render.com i zaprosić kolegów?
1. Wrzuć ten folder na swoje repozytorium **GitHub** (`git add .`, `git commit -m "Hamster Shooter multiplayer"`, `git push`).
2. Wejdź na [render.com](https://render.com) -> zaloguj się przez GitHub -> kliknij **New +** -> **Blueprint** (albo **Web Service**) i wybierz swoje repozytorium `hamster-shooter`.
   - Plik `render.yaml` automatycznie ustawi Pythona 3.12, instalację z `requirements-server.txt` i komendę startową `python server.py`!
3. Po ok. 1–2 minutach Render.com da Ci darmowy link, np. `https://hamster-shooter.onrender.com`.
4. **Jak zaprosić kolegów?**
   - Wejdź na swój link -> wpisz nick -> kliknij **STWÓRZ POKÓJ I ZAPROŚ**.
   - Kliknij **Kopiuj link zaproszenia** (np. `https://hamster-shooter.onrender.com/?room=K7M2`) i wyślij kolegom na Discorda / WhatsAppa!
   - Koledzy klikają link i **od razu grają w przeglądarce** (nic nie muszą instalować!), albo mogą podać 4-literowy kod pokoju w aplikacji Python (`MULTIPLAYER ONLINE`).
