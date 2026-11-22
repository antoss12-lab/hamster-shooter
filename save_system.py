"""
save_system.py — System zapisywania i wczytywania postępu gry do pliku JSON (savegame.json).
Świetny przykład nauki Pythona: zapisujemy słownik (dict) do czytelnego pliku tekstowego JSON!
"""

import json
import os
from settings import WEAPONS, SKINS, DIFFICULTIES

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savegame.json")


def default_save_data() -> dict:
    """Zwraca domyślny, czysty stan nowego gracza."""
    return {
        "player_name": "Chomik",
        "difficulty_id": "normalny",
        "seeds": 0,
        "total_seeds": 0,
        "kills": 0,
        "owned_weapons": ["ziarna"],
        "weapon_id": "ziarna",
        "owned_skins": ["klasyczny"],
        "skin_id": "klasyczny",
        "upgrade_levels": {"max_hp": 0, "speed": 0},
        "quest_index": 0,
        "victory_shown": False,
        "sound_enabled": True,
    }


def load_progress() -> tuple[dict, bool]:
    """
    Wczytuje zapisany postęp z pliku savegame.json.
    Skórki, nick, poziom trudności i ziarna zapisują się na stałe,
    natomiast bronie NIE zapisują się między rundami / po restarcie (zawsze startujesz z Ziarnami).
    """
    data = default_save_data()
    if not os.path.exists(SAVE_FILE):
        return data, False

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            return data, False

        # Bezpieczne odczytanie i walidacja każdego pola
        if isinstance(raw.get("player_name"), str) and raw["player_name"].strip():
            data["player_name"] = raw["player_name"].strip()[:14]

        if raw.get("difficulty_id") in DIFFICULTIES:
            data["difficulty_id"] = raw["difficulty_id"]

        for int_key in ("seeds", "total_seeds", "kills", "quest_index"):
            val = raw.get(int_key)
            if isinstance(val, int) and val >= 0:
                data[int_key] = val

        # Bronie zawsze startują od podstawowego Miotacza Ziaren (nie zapisują się!)
        data["owned_weapons"] = ["ziarna"]
        data["weapon_id"] = "ziarna"

        # Skórki zapisują się na stałe!
        owned_s = [s for s in raw.get("owned_skins", []) if s in SKINS]
        if "klasyczny" not in owned_s:
            owned_s.insert(0, "klasyczny")
        data["owned_skins"] = owned_s

        if raw.get("skin_id") in owned_s:
            data["skin_id"] = raw["skin_id"]

        raw_up = raw.get("upgrade_levels")
        if isinstance(raw_up, dict):
            data["upgrade_levels"] = {
                "max_hp": max(0, min(3, int(raw_up.get("max_hp", 0)))),
                "speed": max(0, min(2, int(raw_up.get("speed", 0)))),
            }

        data["victory_shown"] = bool(raw.get("victory_shown", False))
        data["sound_enabled"] = bool(raw.get("sound_enabled", True))
        return data, True
    except Exception:
        return data, False


def save_progress(game) -> bool:
    """Zapisuje trwały postęp gracza (skórki, nick, ziarna, zadania — bez broni) do savegame.json."""
    payload = {
        "player_name": (game.player_name_input.strip() or game.player.name or "Chomik")[:14],
        "difficulty_id": game.difficulty_id,
        "seeds": int(game.player.seeds),
        "total_seeds": int(game.player.total_seeds),
        "kills": int(game.player.kills),
        "owned_skins": sorted(game.player.owned_skins),
        "skin_id": game.player.skin_id,
        "upgrade_levels": dict(game.player.upgrade_levels),
        "quest_index": int(game.quest_index),
        "victory_shown": bool(game.victory_shown),
        "sound_enabled": bool(game.sounds.enabled),
    }
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def delete_save() -> bool:
    """Usuwa plik zapisu (gdy gracz wybierze 'Resetuj zapis' w menu)."""
    try:
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
        return True
    except Exception:
        return False
