"""
main.py — Główny plik gry Hamster Shooter (Pygame-ce + gotowy pod przeglądarkę z Pygbag).
Aby uruchomić grę na komputerze, wpisz w terminalu:
    python main.py
"""

import asyncio
import math
import random
import pygame

from settings import (
    SCREEN_W,
    SCREEN_H,
    WORLD_W,
    WORLD_H,
    TILE_SIZE,
    FPS,
    WIN_SEEDS_GOAL,
    DIFFICULTIES,
    MAX_MAP_SEEDS,
    SEED_SPAWN_INTERVAL,
    COMBAT_BOT_PRESETS,
    WEAPON_ORDER,
    SKIN_ORDER,
    POWERUP_TYPES,
    QUESTS,
    GOLD,
    WHITE,
    GREEN,
    RED,
    SUNFLOWER_DARK,
    SUNFLOWER_LIGHT,
    get_font,
)
from sounds import SoundManager
from save_system import load_progress, save_progress, delete_save, default_save_data
from map_level import MarioArena
from entities import Hamster, StoryBot, SunflowerSeed, PowerUp, draw_hamster_avatar
from weapons import Bullet, Particle, FloatingText, spawn_burst, draw_weapon_on_hamster
from ui import (
    ShopOverlay,
    draw_hud,
    draw_crosshair,
    draw_dialogue_box,
    draw_start_screen,
    draw_multiplayer_lobby,
    draw_victory_overlay,
)
from net_client import MultiplayerClient


class HamsterGame:
    """Cała logika jednej rozgrywki — łatwo ją zrestartować przyciskiem 'Nowa runda'."""

    def __init__(self, sounds: SoundManager, save_data: dict | None = None, has_save: bool = False):
        self.sounds = sounds
        self.level = MarioArena()
        self.shop = ShopOverlay()

        if save_data is None:
            save_data = default_save_data()

        # Ustawienia z menu i zapisu (nick gracza + poziom trudności)
        self.player_name_input = save_data["player_name"]
        self.name_input_active = not has_save
        self.difficulty_id = save_data["difficulty_id"]
        self.has_save = has_save
        self.confirm_reset = False
        self.autosave_timer = 5.0
        self.save_toast_timer = 0.0
        self.sounds.enabled = save_data.get("sound_enabled", True)

        # Stany gry: "menu", "playing", "shop", "dialogue", "victory"
        self.state = "menu"
        self.victory_shown = bool(save_data.get("victory_shown", False))
        self.elapsed = 0.0
        self.seed_spawn_timer = 1.0
        self.shake_timer = 0.0
        self.shake_strength = 0.0

        # Kamera (płynnie śledzi chomika po zamkniętej arenie)
        self.cam_x = 0.0
        self.cam_y = 0.0

        # Tworzenie gracza i odtworzenie zapisanego postępu
        px, py = self.level.player_spawn
        clean_name = self.player_name_input.strip() or "Chomik"
        self.player = Hamster(
            clean_name,
            px,
            py,
            is_player=True,
            skin_id=save_data["skin_id"],
            weapon_id=save_data["weapon_id"],
            difficulty_id=self.difficulty_id,
        )
        self.player.seeds = int(save_data["seeds"])
        self.player.total_seeds = int(save_data["total_seeds"])
        self.player.kills = int(save_data["kills"])
        self.player.owned_weapons = set(save_data["owned_weapons"])
        self.player.owned_skins = set(save_data["owned_skins"])
        self.player.upgrade_levels = dict(save_data["upgrade_levels"])
        self.player.max_hp = 100 + 25 * self.player.upgrade_levels.get("max_hp", 0)
        self.player.hp = self.player.max_hp

        # Tworzenie 7 atakujących botów
        self.bots: list[Hamster] = []
        for i, preset in enumerate(COMBAT_BOT_PRESETS):
            sx, sy = self.level.bot_spawns[i % len(self.level.bot_spawns)]
            bot = Hamster(
                preset["name"],
                sx,
                sy,
                is_player=False,
                skin_id=preset["skin"],
                weapon_id=preset["weapon"],
                body_override=preset["body_override"],
                difficulty_id=self.difficulty_id,
            )
            self.bots.append(bot)

        self.all_fighters: list[Hamster] = [self.player] + self.bots

        # Tworzenie 3 botów fabularnych (NPC)
        self.npcs: list[StoryBot] = []
        self._create_story_bots()

        # Zadania fabularne
        self.quest_index = int(save_data["quest_index"])
        self.active_npc: StoryBot | None = None
        self.dialogue_lines: list[str] = []
        self.dialogue_idx = 0
        self.open_shop_after_dialogue = False

        # Obiekty na arenie
        self.bullets: list[Bullet] = []
        self.particles: list[Particle] = []
        self.texts: list[FloatingText] = []
        self.seeds: list[SunflowerSeed] = []
        self.powerups: list[PowerUp] = []

        # Na start rozsypujemy kilka ziaren słonecznika po mapie
        for _ in range(10):
            self._spawn_random_seed()

        self.shop_btn_rect = pygame.Rect(0, 0, 0, 0)
        self.start_btn_rect = pygame.Rect(0, 0, 0, 0)
        self.mp_btn_rect = pygame.Rect(0, 0, 0, 0)
        self.name_input_rect = pygame.Rect(0, 0, 0, 0)
        self.reset_btn_rect: pygame.Rect | None = None
        self.diff_btn_rects: list[tuple[pygame.Rect, str]] = []
        self.victory_btns = (pygame.Rect(0, 0, 0, 0), pygame.Rect(0, 0, 0, 0), pygame.Rect(0, 0, 0, 0))

        # --- Tryb Multiplayer Online (Cross-Play z przeglądarką na Render.com) ---
        self.net = MultiplayerClient()
        self.online_mode = False
        self.mp_server_url = "localhost:8000"
        self.mp_room_input = ""
        self.mp_active_field = "url"  # "url" lub "room"
        self.mp_status = ""
        self.pending_connect = False
        self.remote_players: dict[str, dict] = {}
        self.net_seeds: list[dict] = []
        self.net_powerups: list[dict] = []
        self.net_send_timer = 0.0
        self.mp_lobby_rects = (
            pygame.Rect(0, 0, 0, 0),
            pygame.Rect(0, 0, 0, 0),
            pygame.Rect(0, 0, 0, 0),
            pygame.Rect(0, 0, 0, 0),
        )

    async def connect_online(self):
        """Łączy klienta Pygame z serwerem Multiplayer (lokalnie lub Render.com)."""
        self._apply_menu_settings()
        self.mp_status = "Łączenie z serwerem..."
        ok, msg = await self.net.connect(
            self.mp_server_url,
            self.mp_room_input,
            self.player.name,
            self.player.skin_id,
        )
        if ok:
            self.online_mode = True
            self.remote_players.clear()
            self.bullets.clear()
            self.net_seeds.clear()
            self.net_powerups.clear()
            self.player.owned_weapons = {"ziarna"}
            self.player.weapon_id = "ziarna"
            self.player.hp = self.player.max_hp
            self.player.alive = True
            self.state = "playing"
            self.mp_status = ""
            self.sounds.play("buy")
        else:
            self.mp_status = msg
            self.sounds.play("error")

    def save(self, show_toast: bool = False):
        """Zapisuje aktualny postęp gracza do savegame.json."""
        if save_progress(self):
            self.has_save = True
            if show_toast:
                self.save_toast_timer = 1.6

    def _save_summary_text(self) -> str:
        if not self.has_save and self.player.total_seeds == 0 and len(self.player.owned_skins) <= 1:
            return ""
        return (
            f"Zapisany postęp: {self.player.seeds} ziaren  |  "
            f"Skórki: {len(self.player.owned_skins)}/{len(SKIN_ORDER)}  (bronie są na 1 rundę)"
        )

    def _apply_menu_settings(self):
        """Zapisuje wpisany nick gracza i wybrany poziom trudności przed wejściem na arenę."""
        clean = self.player_name_input.strip() or "Chomik"
        self.player_name_input = clean
        self.player.name = clean
        self.confirm_reset = False
        for bot in self.bots:
            bot.apply_difficulty(self.difficulty_id)
        self.save(show_toast=True)

    def _create_story_bots(self):
        p1 = self.level.npc_spawns.get("1", (160, WORLD_H - 180))
        p2 = self.level.npc_spawns.get("2", (980, WORLD_H - 180))
        p3 = self.level.npc_spawns.get("3", (1420, WORLD_H - 120))

        self.npcs = [
            StoryBot(
                "mistrz",
                "Mistrz Ziarno",
                "Mędrzec Słonecznika",
                p1[0],
                p1[1],
                hat="wizard",
                skin_id="krol",
                lines=[],
            ),
            StoryBot(
                "kupiec",
                "Kupiec Pysio",
                "Handlarz Bronią i Skórkami",
                p2[0],
                p2[1],
                hat="merchant",
                skin_id="klasyczny",
                lines=[
                    "Hej, mały wojowniku! Mam najlepsze zabawki na całej arenie: Karabin, Shotgun i zabójcze AWP!",
                    "A jeśli chcesz wyglądać jak prawdziwy kozak, sprawdź skórki Chomika Ninja, Kosmity albo Króla! Otwieram Ci sklep!",
                ],
            ),
            StoryBot(
                "zwiadowca",
                "Zwiadowca Kłapouch",
                "Przewodnik po Arenie",
                p3[0],
                p3[1],
                hat="scout",
                skin_id="rycerz",
                lines=[
                    "Pssst! Znasz sekret tej mapy? Wskocz głową od dołu w złote bloki '?' jak w Mario — wysypią się ziarna albo power-upy!",
                    "Uważaj na 7 atakujących botów, zwłaszcza na Snajpera z AWP. Używaj podwójnego skoku i czerwonych grzybków-trampolin!",
                ],
            ),
        ]

    def current_quest(self) -> dict | None:
        if 0 <= self.quest_index < len(QUESTS):
            return QUESTS[self.quest_index]
        return None

    def current_quest_progress(self) -> int:
        q = self.current_quest()
        if q is None:
            return 0
        qtype = q["type"]
        if qtype == "seeds_collected":
            return self.player.total_seeds
        if qtype == "kills":
            return self.player.kills
        if qtype == "weapons_owned":
            return len(self.player.owned_weapons)
        return 0

    def is_quest_ready(self) -> bool:
        q = self.current_quest()
        return q is not None and self.current_quest_progress() >= q["target"]

    def _spawn_random_seed(self):
        if len(self.seeds) >= MAX_MAP_SEEDS or not self.level.seed_spots:
            return
        sx, sy = random.choice(self.level.seed_spots)
        self.seeds.append(SunflowerSeed(sx, sy - 8, vx=0.0, vy=-60.0))

    def start_dialogue(self, npc: StoryBot):
        self.active_npc = npc
        self.dialogue_idx = 0
        self.open_shop_after_dialogue = False
        self.sounds.play("talk")

        if npc.npc_id == "mistrz":
            q = self.current_quest()
            if q is None:
                self.dialogue_lines = [
                    "Ukończyłeś wszystkie moje zadania! Cała arena śpiewa pieśni o Tobie, Mistrzu Słonecznika!",
                ]
            elif self.is_quest_ready():
                # Odbiór nagrody za ukończone zadanie!
                reward = q["reward"]
                self.player.seeds += reward
                self.player.total_seeds += reward
                self.sounds.play("buy")
                self.texts.append(FloatingText(self.player.rect.centerx, self.player.rect.top - 20, f"+{reward} ZIAREN (NAGRODA!)", GOLD, 1.4))
                lines = [q["done"]]
                self.quest_index += 1
                self.save(show_toast=True)
                next_q = self.current_quest()
                if next_q is not None:
                    lines.append(f"Kolejne zadanie: {next_q['intro']}")
                self.dialogue_lines = lines
            else:
                prog = self.current_quest_progress()
                intro = q["intro"].replace("młody chomiku", self.player.name)
                self.dialogue_lines = [
                    intro,
                    f"Twój obecny postęp: {prog} / {q['target']}. Wróć do mnie, gdy skończysz, a dam Ci +{q['reward']} ziaren!",
                ]
        elif npc.npc_id == "kupiec":
            self.dialogue_lines = list(npc.lines)
            self.open_shop_after_dialogue = True
        else:
            self.dialogue_lines = list(npc.lines)

        self.state = "dialogue"

    def advance_dialogue(self):
        self.dialogue_idx += 1
        if self.dialogue_idx >= len(self.dialogue_lines):
            if self.open_shop_after_dialogue:
                self.state = "shop"
                self.open_shop_after_dialogue = False
            else:
                self.state = "playing"
            self.active_npc = None
        else:
            self.sounds.play("talk")

    def cycle_weapon(self, step: int):
        owned = [w for w in WEAPON_ORDER if w in self.player.owned_weapons]
        if len(owned) <= 1:
            return
        idx = owned.index(self.player.weapon_id)
        self.player.weapon_id = owned[(idx + step) % len(owned)]
        self.sounds.play("talk")

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Obsługuje klawiaturę i myszkę. Może zwrócić 'restart'."""
        if event.type == pygame.KEYDOWN:
            if self.state == "mp_lobby":
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    self.sounds.play("talk")
                elif event.key == pygame.K_TAB:
                    self.mp_active_field = "room" if self.mp_active_field == "url" else "url"
                elif event.key == pygame.K_RETURN:
                    self.pending_connect = True
                elif event.key == pygame.K_BACKSPACE:
                    if self.mp_active_field == "url":
                        self.mp_server_url = self.mp_server_url[:-1]
                    else:
                        self.mp_room_input = self.mp_room_input[:-1]
                elif event.unicode and event.unicode.isprintable():
                    if self.mp_active_field == "url" and len(self.mp_server_url) < 48:
                        self.mp_server_url += event.unicode
                    elif self.mp_active_field == "room" and len(self.mp_room_input) < 6 and event.unicode.isalnum():
                        self.mp_room_input += event.unicode.upper()
                return None

            if self.state == "menu":
                if event.key == pygame.K_RETURN:
                    self.online_mode = False
                    self._apply_menu_settings()
                    self.state = "playing"
                    self.sounds.play("buy")
                elif self.name_input_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.player_name_input = self.player_name_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.name_input_active = False
                    elif event.unicode and event.unicode.isprintable() and len(self.player_name_input) < 14:
                        self.player_name_input += event.unicode
                elif event.key == pygame.K_SPACE:
                    self.online_mode = False
                    self._apply_menu_settings()
                    self.state = "playing"
                    self.sounds.play("buy")
                return None

            if event.key == pygame.K_m:
                self.sounds.toggle()
                self.save()
                return None

            if self.state == "victory":
                if event.key == pygame.K_RETURN:
                    self.state = "playing"
                return None

            if self.state == "shop":
                if event.key in (pygame.K_b, pygame.K_ESCAPE, pygame.K_TAB):
                    self.state = "playing"
                    self.save()
                return None

            if self.state == "dialogue":
                if event.key in (pygame.K_SPACE, pygame.K_e, pygame.K_RETURN):
                    self.advance_dialogue()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "playing"
                    self.active_npc = None
                return None

            # --- Sterowanie w trybie gry ("playing") ---
            if event.key == pygame.K_ESCAPE:
                self.save(show_toast=True)
                self.state = "menu"
                self.name_input_active = False
                self.confirm_reset = False
                self.sounds.play("talk")
            elif event.key in (pygame.K_w, pygame.K_SPACE, pygame.K_UP):
                self.player.try_jump(self.particles, self.sounds)
            elif event.key in (pygame.K_b, pygame.K_TAB):
                self.state = "shop"
                self.sounds.play("talk")
            elif event.key == pygame.K_e:
                for npc in self.npcs:
                    if npc.is_near(self.player):
                        self.start_dialogue(npc)
                        break
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                idx = event.key - pygame.K_1
                wid = WEAPON_ORDER[idx]
                if wid in self.player.owned_weapons:
                    self.player.weapon_id = wid
                    self.sounds.play("talk")
                else:
                    self.texts.append(FloatingText(self.player.rect.centerx, self.player.rect.top - 18, "Kup tę broń w Sklepie [B]!", GOLD, 1.0))
                    self.sounds.play("error")

        elif event.type == pygame.MOUSEWHEEL:
            if self.state == "playing":
                self.cycle_weapon(-1 if event.y > 0 else 1)
            elif self.state == "shop" and self.shop.tab == "skins":
                self.shop.change_skin_page(-1 if event.y > 0 else 1)
                self.sounds.play("talk")

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.state == "mp_lobby":
                connect_btn, back_btn, url_rect, room_rect = self.mp_lobby_rects
                if url_rect.collidepoint(pos):
                    self.mp_active_field = "url"
                elif room_rect.collidepoint(pos):
                    self.mp_active_field = "room"
                elif connect_btn.collidepoint(pos):
                    self.pending_connect = True
                elif back_btn.collidepoint(pos):
                    self.state = "menu"
                    self.sounds.play("talk")
            elif self.state == "menu":
                if self.reset_btn_rect is not None and self.reset_btn_rect.collidepoint(pos):
                    if self.confirm_reset:
                        delete_save()
                        self.sounds.play("error")
                        return "reset_all"
                    else:
                        self.confirm_reset = True
                        self.sounds.play("talk")
                elif self.mp_btn_rect.collidepoint(pos):
                    self._apply_menu_settings()
                    self.state = "mp_lobby"
                    self.mp_status = ""
                    self.sounds.play("talk")
                elif self.name_input_rect.collidepoint(pos):
                    self.name_input_active = True
                    self.confirm_reset = False
                    self.sounds.play("talk")
                elif self.start_btn_rect.collidepoint(pos):
                    self.online_mode = False
                    self._apply_menu_settings()
                    self.state = "playing"
                    self.sounds.play("buy")
                else:
                    self.name_input_active = False
                    self.confirm_reset = False
                    for rect, did in self.diff_btn_rects:
                        if rect.collidepoint(pos):
                            self.difficulty_id = did
                            self.sounds.play("talk")
                            break
            elif self.state == "shop":
                res = self.shop.handle_click(pos, self.player, self.sounds)
                self.save(show_toast=True)
                if res == "close":
                    self.state = "playing"
            elif self.state == "dialogue":
                self.advance_dialogue()
            elif self.state == "victory":
                cont_btn, restart_btn, menu_btn = self.victory_btns
                if cont_btn.collidepoint(pos):
                    self.state = "playing"
                elif restart_btn.collidepoint(pos):
                    return "restart"
                elif menu_btn.collidepoint(pos):
                    self.state = "menu"
                    self.sounds.play("talk")
            elif self.state == "playing":
                if self.shop_btn_rect.collidepoint(pos):
                    self.state = "shop"
                    self.sounds.play("talk")

        return None

    def update(self, dt: float):
        self.elapsed += dt
        if self.save_toast_timer > 0:
            self.save_toast_timer = max(0.0, self.save_toast_timer - dt)
        if self.state != "playing":
            # Nawet w menu delikatnie animujemy bloki i chomiki w tle
            self.level.update(dt)
            for npc in self.npcs:
                npc.update(dt)
            self._update_camera(dt)
            return

        # 1. Aktualizacja mapy i botów fabularnych
        self.level.update(dt)
        if not self.online_mode:
            for npc in self.npcs:
                npc.update(dt)

        # --- Tryb MULTIPLAYER ONLINE (Cross-Play z przeglądarką / Render.com) ---
        if self.online_mode:
            self._update_online(dt)
            return

        # 2. Sterowanie gracza (klawiatura + celowanie myszką)
        self.player.update_timers(dt)
        if not self.player.alive:
            self.player.respawn_timer -= dt
            if self.player.respawn_timer <= 0:
                self.player.respawn(self.level.bot_spawns)
        else:
            keys = pygame.key.get_pressed()
            move = 0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                move -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                move += 1

            target_vx = move * self.player.get_move_speed()
            accel = 16.0 if self.player.on_ground else 9.0
            self.player.vx += (target_vx - self.player.vx) * min(1.0, accel * dt)

            self.player.move_and_collide(
                dt, self.level, self.seeds, self.powerups, self.particles, self.texts, self.sounds
            )

            # Celowanie myszką (przeliczamy pozycję kursora na współrzędne świata)
            mx, my = pygame.mouse.get_pos()
            world_mx = mx + self.cam_x
            world_my = my + self.cam_y
            dx = world_mx - self.player.rect.centerx
            dy = world_my - self.player.rect.centery
            self.player.aim_angle = math.atan2(dy, dx)
            self.player.facing_right = dx >= 0

            # Strzelanie przy trzymaniu lewego przycisku myszy
            if pygame.mouse.get_pressed()[0] and not self.shop_btn_rect.collidepoint((mx, my)):
                shake = self.player.try_shoot(self.bullets, self.particles, self.sounds)
                if shake > 0:
                    self.shake_timer = 0.12
                    self.shake_strength = max(self.shake_strength, shake)

        # 3. Aktualizacja 7 atakujących botów
        for bot in self.bots:
            bot.update_ai(
                dt,
                self.level,
                self.all_fighters,
                self.seeds,
                self.powerups,
                self.bullets,
                self.particles,
                self.texts,
                self.sounds,
            )

        # 4. Pociski i trafienia
        for b in self.bullets:
            b.update(dt, self.level)
            if not b.alive:
                spawn_burst(self.particles, b.x, b.y, b.color, count=4, speed=110)
                continue
            for fighter in self.all_fighters:
                if fighter is b.owner or not fighter.alive:
                    continue
                if fighter.rect.collidepoint(int(b.x), int(b.y)):
                    b.alive = False
                    fighter.take_damage(b.damage, b.owner, self.particles, self.texts, self.sounds, self.seeds)
                    if fighter.is_player:
                        self.shake_timer = 0.14
                        self.shake_strength = 6.0
                    break
        self.bullets = [b for b in self.bullets if b.alive]

        # 5. Ziarna słonecznika (pojawianie się i zbieranie)
        self.seed_spawn_timer -= dt
        if self.seed_spawn_timer <= 0:
            self.seed_spawn_timer = SEED_SPAWN_INTERVAL
            self._spawn_random_seed()

        for s in self.seeds:
            s.update(dt, self.level)
            for fighter in self.all_fighters:
                if fighter.alive and fighter.rect.colliderect(s.rect):
                    s.alive = False
                    fighter.seeds += s.value
                    fighter.total_seeds += s.value
                    spawn_burst(self.particles, s.x, s.y, GOLD, count=5, speed=100)
                    if fighter.is_player:
                        self.sounds.play("seed")
                        self.texts.append(FloatingText(s.x, s.y - 12, f"+{s.value} Ziarno", GOLD, 0.7))
                    break
        self.seeds = [s for s in self.seeds if s.alive]

        # 6. Power-upy
        for p in self.powerups:
            p.update(dt, self.level)
            for fighter in self.all_fighters:
                if fighter.alive and fighter.rect.colliderect(p.rect):
                    p.alive = False
                    fighter.apply_powerup(p.kind, self.texts, self.sounds)
                    break
        self.powerups = [p for p in self.powerups if p.alive]

        # 7. Cząsteczki i latające napisy
        for pt in self.particles:
            pt.update(dt)
        self.particles = [pt for pt in self.particles if pt.life > 0]

        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.life > 0]

        # 8. Wstrząs ekranu, autozapis co 5s i kamera
        if self.save_toast_timer > 0:
            self.save_toast_timer = max(0.0, self.save_toast_timer - dt)
        self.autosave_timer -= dt
        if self.autosave_timer <= 0:
            self.autosave_timer = 5.0
            self.save(show_toast=False)

        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
            if self.shake_timer == 0:
                self.shake_strength = 0.0
        self._update_camera(dt)

        # 9. Sprawdź warunek zwycięstwa!
        if not self.victory_shown and self.player.total_seeds >= WIN_SEEDS_GOAL:
            self.victory_shown = True
            self.save(show_toast=True)
            self.state = "victory"
            self.sounds.play("powerup")

    def _update_online(self, dt: float):
        """Logika gry w trybie Multiplayer Online połączonym z server.py / Render.com."""
        # 1. Odbiór wiadomości z serwera
        for msg in self.net.pop_messages():
            mtype = msg.get("type")
            if mtype in ("welcome", "snapshot"):
                self.net_seeds = msg.get("seeds", [])
                self.net_powerups = msg.get("powerups", [])
                blocks = msg.get("blocks", {})
                for qb in self.level.question_blocks:
                    key = f"{qb.rect.x // TILE_SIZE},{qb.rect.y // TILE_SIZE}"
                    cd = float(blocks.get(key, 0.0))
                    qb.active = cd <= 0.0
                    qb.cooldown = cd
                seen = set()
                for p in msg.get("players", []):
                    pid = p.get("id")
                    if not pid or pid == self.net.player_id:
                        continue
                    seen.add(pid)
                    prev = self.remote_players.get(pid)
                    if prev:
                        prev["tx"] = p["x"]
                        prev["ty"] = p["y"]
                        for k, v in p.items():
                            if k not in ("x", "y"):
                                prev[k] = v
                    else:
                        p["tx"] = p["x"]
                        p["ty"] = p["y"]
                        self.remote_players[pid] = p
                for pid in list(self.remote_players.keys()):
                    if pid not in seen:
                        self.remote_players.pop(pid, None)
            elif mtype == "shoot":
                wid = msg.get("weapon_id", "ziarna")
                b = Bullet(
                    float(msg.get("x", 0)),
                    float(msg.get("y", 0)),
                    float(msg.get("angle", 0)),
                    wid,
                    msg.get("owner_id"),
                    damage_mult=float(msg.get("damage_mult", 1.0)),
                )
                b.owner_name = msg.get("owner_name", "Gracz")
                self.bullets.append(b)
            elif mtype == "damaged" and msg.get("target_id") == self.net.player_id:
                dmg = int(msg.get("damage", 15))
                attacker_id = msg.get("attacker_id", "")
                attacker_name = msg.get("attacker_name", "Wróg")
                died = self.player.take_damage(dmg, None, self.particles, self.texts, self.sounds, [])
                self.shake_timer = 0.14
                self.shake_strength = 6.0
                if died:
                    self.net.send_nowait(
                        {
                            "type": "player_died",
                            "x": self.player.rect.centerx,
                            "y": self.player.rect.centery,
                            "killer_id": attacker_id,
                            "killer_name": attacker_name,
                        }
                    )
            elif mtype == "kill_credit":
                self.player.kills += 1
                self.sounds.play("kill")
                self.texts.append(FloatingText(self.player.rect.centerx, self.player.rect.top - 26, f"Pokonano: {msg.get('victim_name', '')}!", GOLD, 1.3))
            elif mtype == "seed_awarded":
                val = int(msg.get("value", 1))
                self.player.seeds += val
                self.player.total_seeds += val
                self.sounds.play("seed")
                self.texts.append(FloatingText(float(msg.get("x", self.player.rect.centerx)), float(msg.get("y", self.player.rect.top)) - 12, f"+{val} Ziarno", GOLD, 0.7))
            elif mtype == "powerup_awarded":
                self.player.apply_powerup(msg.get("kind", "heal"), self.texts, self.sounds)
            elif mtype == "block_bumped":
                self.sounds.play("block_hit")
            elif mtype == "notice":
                self.texts.append(FloatingText(self.player.rect.centerx, self.player.rect.top - 38, msg.get("text", ""), GOLD, 1.8))

        # 2. Interpolacja pozycji kolegów i botów serwerowych
        for rp in self.remote_players.values():
            rp["x"] += (rp["tx"] - rp["x"]) * min(1.0, 14.0 * dt)
            rp["y"] += (rp["ty"] - rp["y"]) * min(1.0, 14.0 * dt)

        # 3. Ruch lokalnego gracza
        self.player.update_timers(dt)
        if not self.player.alive:
            self.player.respawn_timer -= dt
            if self.player.respawn_timer <= 0:
                self.player.respawn(self.level.bot_spawns)
        else:
            keys = pygame.key.get_pressed()
            move = (-1 if (keys[pygame.K_a] or keys[pygame.K_LEFT]) else 0) + (1 if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) else 0)
            target_vx = move * self.player.get_move_speed()
            accel = 16.0 if self.player.on_ground else 9.0
            self.player.vx += (target_vx - self.player.vx) * min(1.0, accel * dt)

            prev_vy = self.player.vy
            self.player.move_and_collide(dt, self.level, [], [], self.particles, self.texts, self.sounds)
            if prev_vy < 0 and self.player.vy > 0:
                for qb in self.level.question_blocks:
                    if abs(self.player.rect.top - qb.rect.bottom) <= 6 and self.player.rect.right > qb.rect.left and self.player.rect.left < qb.rect.right:
                        self.net.send_nowait({"type": "bump_block", "col": qb.rect.x // TILE_SIZE, "row": qb.rect.y // TILE_SIZE})

            mx, my = pygame.mouse.get_pos()
            dx = (mx + self.cam_x) - self.player.rect.centerx
            dy = (my + self.cam_y) - self.player.rect.centery
            self.player.aim_angle = math.atan2(dy, dx)
            self.player.facing_right = dx >= 0

            if pygame.mouse.get_pressed()[0] and not self.shop_btn_rect.collidepoint((mx, my)):
                before = len(self.bullets)
                shake = self.player.try_shoot(self.bullets, self.particles, self.sounds)
                if len(self.bullets) > before:
                    b0 = self.bullets[before]
                    self.net.send_nowait(
                        {
                            "type": "shoot",
                            "x": round(b0.x, 1),
                            "y": round(b0.y, 1),
                            "angle": round(self.player.aim_angle, 3),
                            "weapon_id": self.player.weapon_id,
                            "damage_mult": 2.0 if self.player.damage_timer > 0 else 1.0,
                        }
                    )
                if shake > 0:
                    self.shake_timer = 0.12
                    self.shake_strength = max(self.shake_strength, shake)

            # Zbieranie ziaren i power-upów z serwera
            for s in self.net_seeds:
                if not s.get("_claimed") and math.hypot(s["x"] - self.player.rect.centerx, s["y"] - self.player.rect.centery) < 28:
                    s["_claimed"] = True
                    self.net.send_nowait({"type": "collect_seed", "seed_id": s["id"]})
            for p in self.net_powerups:
                if not p.get("_claimed") and math.hypot(p["x"] - self.player.rect.centerx, p["y"] - self.player.rect.centery) < 30:
                    p["_claimed"] = True
                    self.net.send_nowait({"type": "collect_powerup", "powerup_id": p["id"]})

        # 4. Pociski w trybie online
        for b in self.bullets:
            b.update(dt, self.level)
            if not b.alive:
                spawn_burst(self.particles, b.x, b.y, b.color, count=4, speed=110)
                continue
            if b.owner is self.player:
                for pid, rp in self.remote_players.items():
                    if not rp.get("alive", True):
                        continue
                    if abs(b.x - rp["x"]) < 18 and abs(b.y - rp["y"]) < 19:
                        b.alive = False
                        spawn_burst(self.particles, b.x, b.y, RED, count=6, speed=140)
                        self.sounds.play("hit")
                        self.net.send_nowait({"type": "hit", "target_id": pid, "damage": b.damage, "weapon_id": b.weapon_id})
                        break
            elif self.player.alive and self.player.rect.collidepoint(int(b.x), int(b.y)):
                b.alive = False
        self.bullets = [b for b in self.bullets if b.alive]

        for pt in self.particles:
            pt.update(dt)
        self.particles = [pt for pt in self.particles if pt.life > 0]
        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.life > 0]

        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
            if self.shake_timer == 0:
                self.shake_strength = 0.0
        self._update_camera(dt)

        # 5. Wysyłanie własnej pozycji do serwera (20 Hz)
        self.net_send_timer -= dt
        if self.net_send_timer <= 0:
            self.net_send_timer = 0.05
            self.net.send_nowait(
                {
                    "type": "update",
                    "name": self.player.name,
                    "x": round(self.player.rect.centerx, 1),
                    "y": round(self.player.rect.centery, 1),
                    "vx": round(self.player.vx, 1),
                    "vy": round(self.player.vy, 1),
                    "aim": round(self.player.aim_angle, 3),
                    "facing_right": self.player.facing_right,
                    "skin_id": self.player.skin_id,
                    "weapon_id": self.player.weapon_id,
                    "hp": self.player.hp,
                    "max_hp": self.player.max_hp,
                    "alive": self.player.alive,
                    "seeds": self.player.seeds,
                    "total_seeds": self.player.total_seeds,
                    "kills": self.player.kills,
                    "shield": round(self.player.shield_timer, 1),
                    "damage_boost": round(self.player.damage_timer, 1),
                }
            )

    def _update_camera(self, dt: float):
        target_x = self.player.rect.centerx - SCREEN_W / 2
        target_y = self.player.rect.centery - SCREEN_H / 2
        target_x = max(0.0, min(WORLD_W - SCREEN_W, target_x))
        target_y = max(0.0, min(WORLD_H - SCREEN_H, target_y))
        self.cam_x += (target_x - self.cam_x) * min(1.0, 8.0 * dt)
        self.cam_y += (target_y - self.cam_y) * min(1.0, 8.0 * dt)

    def draw(self, surf: pygame.Surface):
        ox = random.uniform(-self.shake_strength, self.shake_strength) if self.shake_timer > 0 else 0.0
        oy = random.uniform(-self.shake_strength, self.shake_strength) if self.shake_timer > 0 else 0.0
        cx = self.cam_x + ox
        cy = self.cam_y + oy

        f_q = get_font(22, bold=True)
        f_name = get_font(13, bold=True)
        f_pup = get_font(15, bold=True)
        f_float = get_font(16, bold=True)

        # 1. Zamknięta mapa Mario
        self.level.draw(surf, cx, cy, self.elapsed, f_q)

        # 2–4. Obiekty i postacie (Singleplayer albo Multiplayer Online)
        if self.online_mode:
            # Ziarna z serwera
            for s in self.net_seeds:
                sx = int(s["x"] - cx)
                sy = int(s["y"] - cy + math.sin(self.elapsed * 5.0 + s["id"]) * 3.0)
                pygame.draw.circle(surf, (255, 235, 120), (sx, sy), 11, 2)
                pygame.draw.ellipse(surf, SUNFLOWER_DARK, (sx - 6, sy - 9, 12, 18))
                pygame.draw.ellipse(surf, SUNFLOWER_LIGHT, (sx - 3, sy - 7, 6, 14))
            # Power-upy z serwera
            for p in self.net_powerups:
                info = POWERUP_TYPES.get(p["kind"], POWERUP_TYPES["heal"])
                px = int(p["x"] - cx)
                py = int(p["y"] - cy + math.sin(self.elapsed * 6.0 + p["id"]) * 4.0)
                pygame.draw.circle(surf, WHITE, (px, py), 16)
                pygame.draw.circle(surf, info["color"], (px, py), 14)
                txt = f_pup.render(info["symbol"], True, (20, 20, 28))
                surf.blit(txt, (px - txt.get_width() // 2, py - txt.get_height() // 2))
            # Koledzy i boty z pokoju online
            for rp in self.remote_players.values():
                if not rp.get("alive", True):
                    continue
                rx = int(rp["x"] - cx)
                ry = int(rp["y"] - cy)
                draw_hamster_avatar(surf, rx, ry, rp.get("skin_id", "klasyczny"), rp.get("facing_right", True), float(rp.get("aim", 0.0)))
                draw_weapon_on_hamster(surf, rx, ry, float(rp.get("aim", 0.0)), rp.get("weapon_id", "ziarna"))
                if float(rp.get("shield", 0.0)) > 0:
                    pygame.draw.circle(surf, (90, 210, 255), (rx, ry), 25, 3)
                bar_w = 38
                bx, by = rx - bar_w // 2, ry - 41
                pygame.draw.rect(surf, (30, 30, 35), (bx - 1, by - 1, bar_w + 2, 7))
                ratio = max(0.0, rp.get("hp", 100) / max(1, rp.get("max_hp", 100)))
                pygame.draw.rect(surf, RED, (bx, by, int(bar_w * ratio), 5))
                lbl = f_name.render(rp.get("name", "Gracz"), True, WHITE)
                surf.blit(lbl, (rx - lbl.get_width() // 2, by - 17))
            self.player.draw(surf, cx, cy, self.level, f_name)
        else:
            q_ready = self.is_quest_ready()
            for npc in self.npcs:
                npc.draw(surf, cx, cy, self.player, f_name, quest_ready=(q_ready and npc.npc_id == "mistrz"))
            for s in self.seeds:
                s.draw(surf, cx, cy)
            for p in self.powerups:
                p.draw(surf, cx, cy, f_pup)
            for bot in self.bots:
                bot.draw(surf, cx, cy, self.level, f_name)
            self.player.draw(surf, cx, cy, self.level, f_name)

        # 5. Pociski, cząsteczki i napisy
        for b in self.bullets:
            b.draw(surf, cx, cy)
        for pt in self.particles:
            pt.draw(surf, cx, cy)
        for t in self.texts:
            t.draw(surf, cx, cy, f_float)

        # 6. Interfejs HUD / Sklep / Dialog / Menu / Lobby Online / Wygrana
        if self.state == "playing":
            if self.online_mode:
                class _Row:
                    def __init__(self, name, total_seeds, is_player=False):
                        self.name = name
                        self.total_seeds = total_seeds
                        self.is_player = is_player

                lb_list = [_Row(self.player.name, self.player.total_seeds, True)] + [
                    _Row(rp.get("name", "Gracz"), int(rp.get("total_seeds", 0)), False) for rp in self.remote_players.values()
                ]
                self.shop_btn_rect = draw_hud(
                    surf,
                    self.player,
                    lb_list,
                    None,
                    0,
                    self.sounds.enabled,
                    self.difficulty_id,
                    room_code=self.net.room_code,
                )
            else:
                self.shop_btn_rect = draw_hud(
                    surf,
                    self.player,
                    self.all_fighters,
                    self.current_quest(),
                    self.current_quest_progress(),
                    self.sounds.enabled,
                    self.difficulty_id,
                )
            draw_crosshair(surf, pygame.mouse.get_pos(), self.player.weapon_id)
        elif self.state == "shop":
            self.shop.draw(surf, self.player)
        elif self.state == "dialogue" and self.active_npc is not None:
            self.shop_btn_rect = draw_hud(
                surf,
                self.player,
                self.all_fighters,
                self.current_quest(),
                self.current_quest_progress(),
                self.sounds.enabled,
                self.difficulty_id,
            )
            line = self.dialogue_lines[min(self.dialogue_idx, len(self.dialogue_lines) - 1)]
            draw_dialogue_box(surf, self.active_npc, line)
        elif self.state == "menu":
            self.start_btn_rect, self.name_input_rect, self.diff_btn_rects, self.reset_btn_rect, self.mp_btn_rect = draw_start_screen(
                surf,
                self.elapsed,
                self.player_name_input,
                self.name_input_active,
                self.difficulty_id,
                save_summary=self._save_summary_text(),
                confirm_reset=self.confirm_reset,
            )
        elif self.state == "mp_lobby":
            self.mp_lobby_rects = draw_multiplayer_lobby(
                surf,
                self.elapsed,
                self.mp_server_url,
                self.mp_room_input,
                self.mp_active_field,
                self.mp_status,
            )
        elif self.state == "victory":
            self.victory_btns = draw_victory_overlay(surf, self.player, self.difficulty_id)

        # Mały napis "Zapisano!" w prawym dolnym rogu po zapisie postępu
        if self.save_toast_timer > 0:
            t_font = get_font(15, bold=True)
            lbl = t_font.render("Zapisano postęp!", True, GREEN)
            box = pygame.Rect(SCREEN_W - lbl.get_width() - 32, SCREEN_H - 42, lbl.get_width() + 20, 28)
            pygame.draw.rect(surf, (22, 32, 46), box, border_radius=8)
            pygame.draw.rect(surf, GREEN, box, 2, border_radius=8)
            surf.blit(lbl, (box.x + 10, box.y + 4))


async def main():
    """Asynchroniczna pętla główna — działa i na Windowsie, i w przeglądarce przez Pygbag!"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Hamster Shooter — Bitwa o Ziarna Słonecznika")
    clock = pygame.time.Clock()

    sounds = SoundManager()
    saved_data, has_save = load_progress()
    game = HamsterGame(sounds, save_data=saved_data, has_save=has_save)
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        # Ukryj systemowy kursor tylko podczas celowania na arenie
        pygame.mouse.set_visible(game.state != "playing")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.save(show_toast=False)
                running = False
                break
            res = game.handle_event(event)
            if res == "restart":
                # Nowa runda: skórki i portfel ziaren zostają na stałe, ale bronie resetują się do Ziaren!
                game.save(show_toast=False)
                saved_data, has_save = load_progress()
                saved_data["total_seeds"] = 0
                saved_data["victory_shown"] = False
                saved_data["owned_weapons"] = ["ziarna"]
                saved_data["weapon_id"] = "ziarna"
                game = HamsterGame(sounds, save_data=saved_data, has_save=has_save)
                game.save(show_toast=False)
                game.state = "playing"
            elif res == "reset_all":
                await game.net.disconnect()
                game = HamsterGame(sounds, save_data=default_save_data(), has_save=False)
                game.state = "menu"

        if game.pending_connect:
            game.pending_connect = False
            await game.connect_online()

        game.update(dt)
        game.draw(screen)
        pygame.display.flip()

        # Niezbędna linijka dla Pygbag (uruchamianie gry w przeglądarce)
        await asyncio.sleep(0)

    await game.net.disconnect()
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
