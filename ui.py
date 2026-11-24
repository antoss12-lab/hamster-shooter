"""
ui.py — Interfejs użytkownika:
- HUD podczas gry (HP, tarcza, ziarna, pasek broni 1-4, power-upy, ranking TOP 3, aktywne zadanie),
- Sklep (kupowanie broni, skórek chomików i ulepszeń za ziarna słonecznika),
- Okno rozmowy z botami fabularnymi (NPC),
- Ekran startowy, pauza, ekran zwycięstwa oraz celownik myszy.
"""

import pygame
from settings import (
    SCREEN_W,
    SCREEN_H,
    WIN_SEEDS_GOAL,
    DIFFICULTIES,
    DIFFICULTY_ORDER,
    WEAPONS,
    WEAPON_ORDER,
    SKINS,
    SKIN_ORDER,
    UPGRADES,
    POWERUP_TYPES,
    WHITE,
    BLACK,
    DARK_UI,
    GOLD,
    RED,
    GREEN,
    BLUE,
    PURPLE,
    ORANGE,
    get_font,
)
from entities import draw_hamster_avatar


def draw_panel(surf: pygame.Surface, rect: pygame.Rect, alpha: int = 215, border_col=GOLD):
    # Subtelny cień pod panelem UI dla efektu głębi
    shadow = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (6, 10, 18, 110), (0, 0, rect.w, rect.h), border_radius=12)
    surf.blit(shadow, (rect.x + 3, rect.y + 4))

    panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (DARK_UI[0], DARK_UI[1], DARK_UI[2], alpha), (0, 0, rect.w, rect.h), border_radius=12)
    # Delikatny górny blik na panelu
    pygame.draw.rect(panel, (255, 255, 255, 18), (4, 3, rect.w - 8, min(14, rect.h // 3)), border_radius=8)
    pygame.draw.rect(panel, border_col, (0, 0, rect.w, rect.h), 2, border_radius=12)
    surf.blit(panel, rect.topleft)


def draw_crosshair(surf: pygame.Surface, pos: tuple[int, int], weapon_id: str):
    mx, my = pos
    col = (255, 65, 65) if weapon_id == "awp" else WHITE
    r = 14 if weapon_id == "shotgun" else (11 if weapon_id == "awp" else 9)
    pygame.draw.circle(surf, (20, 20, 25), (mx, my), r + 1, 2)
    pygame.draw.circle(surf, col, (mx, my), r, 2)
    pygame.draw.line(surf, col, (mx - r - 5, my), (mx - 4, my), 2)
    pygame.draw.line(surf, col, (mx + 4, my), (mx + r + 5, my), 2)
    pygame.draw.line(surf, col, (mx, my - r - 5), (mx, my - 4), 2)
    pygame.draw.line(surf, col, (mx, my + 4), (mx, my + r + 5), 2)
    pygame.draw.circle(surf, GOLD, (mx, my), 2)


def draw_hud(
    surf: pygame.Surface,
    player,
    all_fighters: list,
    quest_info: dict | None,
    quest_progress: int,
    sound_on: bool,
    difficulty_id: str = "normalny",
    room_code: str = "",
) -> pygame.Rect:
    """Rysuje cały interfejs podczas gry. Zwraca prostokąt przycisku Sklepu (do klikania myszką)."""
    f_sm = get_font(15, bold=True)
    f_md = get_font(19, bold=True)
    f_xs = get_font(13)

    # --- 1. Lewy górny róg: Nick, HP, Ziarna, Sklep ---
    draw_panel(surf, pygame.Rect(14, 12, 294, 108), alpha=205, border_col=GOLD)

    # Nick + Pasek HP z połyskiem arcade
    hp_txt = f_sm.render(f"{player.name}  —  HP: {player.hp} / {player.max_hp}", True, WHITE)
    surf.blit(hp_txt, (26, 20))
    bar_rect = pygame.Rect(26, 42, 268, 16)
    pygame.draw.rect(surf, (55, 25, 30), bar_rect, border_radius=6)
    ratio = max(0.0, player.hp / max(1, player.max_hp))
    fill_w = int(bar_rect.w * ratio)
    if fill_w > 0:
        hp_col = GREEN if ratio > 0.35 else RED
        hi_col = (135, 240, 150) if ratio > 0.35 else (255, 130, 130)
        pygame.draw.rect(surf, hp_col, (bar_rect.x, bar_rect.y, fill_w, bar_rect.h), border_radius=6)
        pygame.draw.rect(surf, hi_col, (bar_rect.x + 2, bar_rect.y + 2, max(2, fill_w - 4), 5), border_radius=3)
    pygame.draw.rect(surf, WHITE, bar_rect, 1, border_radius=6)

    # Ikonka ziarna słonecznika + licznik ziaren
    pygame.draw.ellipse(surf, (65, 55, 45), (27, 68, 12, 18))
    pygame.draw.ellipse(surf, (240, 225, 190), (30, 70, 6, 14))
    pygame.draw.ellipse(surf, GOLD, (26, 67, 14, 20), 1)
    seeds_txt = f_md.render(f"Ziarna: {player.seeds}  (Cel: {player.total_seeds}/{WIN_SEEDS_GOAL})", True, GOLD)
    surf.blit(seeds_txt, (46, 66))

    kills_txt = f_xs.render(f"Boty: {player.kills}  |  [ESC] Menu  |  [M] Dźwięk: {'ON' if sound_on else 'OFF'}", True, (215, 225, 240))
    surf.blit(kills_txt, (26, 94))

    # Przycisk Sklepu + odznaka poziomu trudności
    shop_btn = pygame.Rect(318, 14, 124, 42)
    draw_panel(surf, shop_btn, alpha=220, border_col=GOLD)
    s_lbl = f_sm.render("SKLEP [B]", True, GOLD)
    surf.blit(s_lbl, (shop_btn.centerx - s_lbl.get_width() // 2, shop_btn.centery - s_lbl.get_height() // 2))

    diff = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normalny"])
    diff_badge = pygame.Rect(318, 62, 124, 30)
    draw_panel(surf, diff_badge, alpha=205, border_col=BLUE if room_code else diff["color"])
    if room_code:
        d_lbl = f_xs.render(f"POKÓJ: {room_code}", True, GOLD)
    else:
        d_lbl = f_xs.render(f"Poziom: {diff['name']}", True, diff["color"])
    surf.blit(d_lbl, (diff_badge.centerx - d_lbl.get_width() // 2, diff_badge.centery - d_lbl.get_height() // 2))

    # Baner z kodem pokoju na górze (tryb Multiplayer Online)
    if room_code:
        r_box = pygame.Rect(SCREEN_W // 2 - 155, 12, 310, 36)
        draw_panel(surf, r_box, alpha=220, border_col=GOLD)
        rl = f_sm.render(f"MULTIPLAYER ONLINE  |  KOD: {room_code}", True, GOLD)
        surf.blit(rl, (r_box.centerx - rl.get_width() // 2, r_box.centery - rl.get_height() // 2))

    # --- 2. Aktywne power-upy (pod paskiem HP) ---
    py_y = 128
    active_pups = [
        ("speed", player.speed_timer),
        ("shield", player.shield_timer),
        ("damage", player.damage_timer),
    ]
    for kind, timer in active_pups:
        if timer > 0:
            info = POWERUP_TYPES[kind]
            r = pygame.Rect(14, py_y, 200, 26)
            draw_panel(surf, r, alpha=200, border_col=info["color"])
            t_lbl = f_xs.render(f"{info['name']}: {timer:.1f}s", True, info["color"])
            surf.blit(t_lbl, (r.x + 10, r.y + 5))
            py_y += 32

    # --- 3. Prawy górny róg: Zadanie fabularne + Ranking TOP 3 ---
    if quest_info is not None:
        q_rect = pygame.Rect(SCREEN_W - 336, 12, 322, 74)
        done = quest_progress >= quest_info["target"]
        draw_panel(surf, q_rect, alpha=205, border_col=GREEN if done else BLUE)
        hdr = f_xs.render("ZADANIE FABULARNE (Mistrz Ziarno):", True, GREEN if done else (140, 210, 255))
        surf.blit(hdr, (q_rect.x + 12, q_rect.y + 8))
        qt = f_sm.render(quest_info["title"], True, WHITE)
        surf.blit(qt, (q_rect.x + 12, q_rect.y + 27))
        status_str = "UKOŃCZONE! Wróć do Mistrza [E]" if done else f"Postęp: {min(quest_progress, quest_info['target'])} / {quest_info['target']}  (Nagroda: +{quest_info['reward']} ziaren)"
        st = f_xs.render(status_str, True, GOLD if done else (210, 220, 235))
        surf.blit(st, (q_rect.x + 12, q_rect.y + 50))

    # Ranking TOP 3 chomików
    lb_rect = pygame.Rect(SCREEN_W - 220, 94, 206, 102)
    draw_panel(surf, lb_rect, alpha=190, border_col=(130, 145, 175))
    surf.blit(f_xs.render("RANKING ZIAREN (TOP 3):", True, GOLD), (lb_rect.x + 12, lb_rect.y + 8))
    ranked = sorted(all_fighters, key=lambda f: f.total_seeds, reverse=True)[:3]
    for i, f in enumerate(ranked):
        col = GOLD if f.is_player else WHITE
        row_txt = f_sm.render(f"{i + 1}. {f.name}: {f.total_seeds}", True, col)
        surf.blit(row_txt, (lb_rect.x + 14, lb_rect.y + 28 + i * 22))

    # --- 4. Dół ekranu: Pasek broni [1] [2] [3] [4] ---
    slot_w = 152
    slot_h = 54
    gap = 10
    total_w = len(WEAPON_ORDER) * slot_w + (len(WEAPON_ORDER) - 1) * gap
    start_x = (SCREEN_W - total_w) // 2
    y = SCREEN_H - slot_h - 12

    for i, wid in enumerate(WEAPON_ORDER):
        spec = WEAPONS[wid]
        owned = wid in player.owned_weapons
        selected = player.weapon_id == wid
        rect = pygame.Rect(start_x + i * (slot_w + gap), y, slot_w, slot_h)
        border = GOLD if selected else ((120, 195, 130) if owned else (85, 85, 100))
        draw_panel(surf, rect, alpha=230 if selected else 175, border_col=border)

        key_lbl = f_sm.render(f"[{spec['key']}]", True, GOLD if selected else (180, 190, 210))
        surf.blit(key_lbl, (rect.x + 8, rect.y + 6))

        name_col = WHITE if owned else (130, 135, 150)
        w_lbl = f_sm.render(spec["name"].split()[0], True, name_col)
        surf.blit(w_lbl, (rect.x + 36, rect.y + 6))

        sub = "Wybrana" if selected else ("Gotowa" if owned else f"Sklep: {spec['cost']} z.")
        sub_col = GREEN if selected else ((180, 220, 190) if owned else (225, 165, 110))
        surf.blit(f_xs.render(sub, True, sub_col), (rect.x + 10, rect.y + 30))

    return shop_btn


class ShopOverlay:
    """Ekran Sklepu: zakładki Bronie, Skórki (ze stronami!) i Ulepszenia."""

    SKINS_PER_PAGE = 6

    def __init__(self):
        self.tab = "weapons"  # "weapons", "skins", "upgrades"
        self.skin_page = 0
        self.message = "Kupuj za zebrane ziarna słonecznika!"
        self.buttons: list[tuple[pygame.Rect, str, str]] = []

    def total_skin_pages(self) -> int:
        return max(1, (len(SKIN_ORDER) + self.SKINS_PER_PAGE - 1) // self.SKINS_PER_PAGE)

    def change_skin_page(self, delta: int):
        total = self.total_skin_pages()
        self.skin_page = (self.skin_page + delta) % total

    def draw(self, surf: pygame.Surface, player):
        # Przyciemnienie tła
        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((10, 12, 20, 175))
        surf.blit(dim, (0, 0))

        box = pygame.Rect(140, 60, SCREEN_W - 280, SCREEN_H - 120)
        draw_panel(surf, box, alpha=245, border_col=GOLD)

        f_title = get_font(30, bold=True)
        f_md = get_font(19, bold=True)
        f_sm = get_font(15, bold=True)
        f_xs = get_font(14)

        surf.blit(f_title.render("SKLEP CHOMIKA PYSIA", True, GOLD), (box.x + 28, box.y + 18))
        seed_lbl = f_md.render(f"Twoje ziarna: {player.seeds}", True, GOLD)
        surf.blit(seed_lbl, (box.right - seed_lbl.get_width() - 32, box.y + 26))

        self.buttons = []

        # Zakładki
        tabs = [("weapons", "BRONIE"), ("skins", "SKÓRKI CHOMIKA"), ("upgrades", "ULEPSZENIA")]
        tx = box.x + 28
        for tid, tlabel in tabs:
            tr = pygame.Rect(tx, box.y + 68, 190, 38)
            active = self.tab == tid
            pygame.draw.rect(surf, (60, 75, 115) if active else (36, 42, 62), tr, border_radius=8)
            pygame.draw.rect(surf, GOLD if active else (100, 110, 140), tr, 2, border_radius=8)
            lbl = f_sm.render(tlabel, True, GOLD if active else WHITE)
            surf.blit(lbl, (tr.centerx - lbl.get_width() // 2, tr.centery - lbl.get_height() // 2))
            self.buttons.append((tr, "tab", tid))
            tx += 204

        # Przycisk Zamknij
        close_r = pygame.Rect(box.right - 150, box.y + 68, 122, 38)
        pygame.draw.rect(surf, (150, 45, 55), close_r, border_radius=8)
        pygame.draw.rect(surf, WHITE, close_r, 2, border_radius=8)
        cl = f_sm.render("ZAMKNIJ [B]", True, WHITE)
        surf.blit(cl, (close_r.centerx - cl.get_width() // 2, close_r.centery - cl.get_height() // 2))
        self.buttons.append((close_r, "close", ""))

        # Zawartość zakładek
        content_y = box.y + 124
        if self.tab == "weapons":
            for i, wid in enumerate(WEAPON_ORDER):
                spec = WEAPONS[wid]
                owned = wid in player.owned_weapons
                equipped = player.weapon_id == wid
                card = pygame.Rect(box.x + 28, content_y + i * 96, box.w - 56, 84)
                pygame.draw.rect(surf, (38, 45, 68), card, border_radius=10)
                pygame.draw.rect(surf, GOLD if equipped else (90, 100, 130), card, 2, border_radius=10)

                surf.blit(f_md.render(f"[{spec['key']}] {spec['name']}", True, WHITE), (card.x + 18, card.y + 10))
                surf.blit(f_xs.render(spec["desc"], True, (200, 210, 230)), (card.x + 18, card.y + 36))
                stats = f"Obrażenia: {spec['damage']}x{spec['pellets']}   |   Szybkość pocisku: {spec['speed']}"
                surf.blit(f_xs.render(stats, True, (165, 225, 195)), (card.x + 18, card.y + 56))

                btn = pygame.Rect(card.right - 175, card.y + 20, 155, 44)
                if equipped:
                    bcol, btxt = (50, 135, 75), "WYBRANA"
                elif owned:
                    bcol, btxt = (65, 110, 185), "WYBIERZ"
                else:
                    can = player.seeds >= spec["cost"]
                    bcol = (195, 135, 35) if can else (75, 75, 88)
                    btxt = f"KUP ({spec['cost']} z.)"
                pygame.draw.rect(surf, bcol, btn, border_radius=8)
                pygame.draw.rect(surf, WHITE, btn, 1, border_radius=8)
                bl = f_sm.render(btxt, True, WHITE)
                surf.blit(bl, (btn.centerx - bl.get_width() // 2, btn.centery - bl.get_height() // 2))
                self.buttons.append((btn, "weapon", wid))

        elif self.tab == "skins":
            cols = 3
            cw = (box.w - 56 - 24) // cols
            ch = 172
            start_i = self.skin_page * self.SKINS_PER_PAGE
            page_skins = SKIN_ORDER[start_i : start_i + self.SKINS_PER_PAGE]
            for i, sid in enumerate(page_skins):
                skin = SKINS[sid]
                owned = sid in player.owned_skins
                equipped = player.skin_id == sid
                r = i // cols
                c = i % cols
                card = pygame.Rect(box.x + 28 + c * (cw + 12), content_y + r * (ch + 12), cw, ch)
                pygame.draw.rect(surf, (38, 45, 68), card, border_radius=10)
                pygame.draw.rect(surf, GOLD if equipped else (90, 100, 130), card, 2, border_radius=10)

                # Podgląd skórki chomika (z zapasem miejsca nad głową na wysokie czapki!)
                draw_hamster_avatar(surf, card.centerx, card.y + 60, sid, True, 0.0, scale=1.16)

                nl = f_md.render(skin["name"], True, WHITE)
                surf.blit(nl, (card.centerx - nl.get_width() // 2, card.y + 92))
                dl = f_xs.render(skin["desc"][:34], True, (190, 200, 220))
                surf.blit(dl, (card.centerx - dl.get_width() // 2, card.y + 114))

                btn = pygame.Rect(card.x + 24, card.bottom - 38, card.w - 48, 30)
                if equipped:
                    bcol, btxt = (50, 135, 75), "ZAŁOŻONA"
                elif owned:
                    bcol, btxt = (65, 110, 185), "ZAŁÓŻ"
                else:
                    can = player.seeds >= skin["cost"]
                    bcol = (195, 135, 35) if can else (75, 75, 88)
                    btxt = f"KUP ({skin['cost']} z.)"
                pygame.draw.rect(surf, bcol, btn, border_radius=8)
                pygame.draw.rect(surf, WHITE, btn, 1, border_radius=8)
                bl = f_sm.render(btxt, True, WHITE)
                surf.blit(bl, (btn.centerx - bl.get_width() // 2, btn.centery - bl.get_height() // 2))
                self.buttons.append((btn, "skin", sid))

            # Pasek stron (np. Strona 1 / 4 — łącznie 22 skórki!)
            nav_y = box.bottom - 76
            prev_r = pygame.Rect(box.centerx - 255, nav_y, 135, 32)
            next_r = pygame.Rect(box.centerx + 120, nav_y, 135, 32)
            for nr, ntxt, act in ((prev_r, "< POPRZEDNIA", "page_prev"), (next_r, "NASTĘPNA >", "page_next")):
                pygame.draw.rect(surf, (58, 72, 108), nr, border_radius=8)
                pygame.draw.rect(surf, GOLD, nr, 1, border_radius=8)
                nlbl = f_sm.render(ntxt, True, WHITE)
                surf.blit(nlbl, (nr.centerx - nlbl.get_width() // 2, nr.centery - nlbl.get_height() // 2))
                self.buttons.append((nr, act, ""))

            pg_lbl = f_sm.render(f"Strona {self.skin_page + 1} / {self.total_skin_pages()}  ({len(SKIN_ORDER)} skórek)", True, GOLD)
            surf.blit(pg_lbl, (box.centerx - pg_lbl.get_width() // 2, nav_y + 6))

        elif self.tab == "upgrades":
            for i, (uid, up) in enumerate(UPGRADES.items()):
                lvl = player.upgrade_levels.get(uid, 0)
                max_lvl = up["max_level"]
                cost = up["base_cost"] + lvl * 8
                card = pygame.Rect(box.x + 28, content_y + i * 118, box.w - 56, 100)
                pygame.draw.rect(surf, (38, 45, 68), card, border_radius=10)
                pygame.draw.rect(surf, BLUE, card, 2, border_radius=10)

                surf.blit(f_md.render(f"{up['name']}   (Poziom {lvl}/{max_lvl})", True, WHITE), (card.x + 18, card.y + 14))
                surf.blit(f_xs.render(up["desc"], True, (200, 215, 235)), (card.x + 18, card.y + 46))

                btn = pygame.Rect(card.right - 185, card.y + 26, 165, 48)
                if lvl >= max_lvl:
                    bcol, btxt = (50, 135, 75), "MAKSYMALNY"
                else:
                    can = player.seeds >= cost
                    bcol = (195, 135, 35) if can else (75, 75, 88)
                    btxt = f"ULEPSZ ({cost} z.)"
                pygame.draw.rect(surf, bcol, btn, border_radius=8)
                pygame.draw.rect(surf, WHITE, btn, 1, border_radius=8)
                bl = f_sm.render(btxt, True, WHITE)
                surf.blit(bl, (btn.centerx - bl.get_width() // 2, btn.centery - bl.get_height() // 2))
                self.buttons.append((btn, "upgrade", uid))

        # Stopka z komunikatem
        msg_s = f_sm.render(self.message, True, GOLD)
        surf.blit(msg_s, (box.centerx - msg_s.get_width() // 2, box.bottom - 34))

    def handle_click(self, pos: tuple[int, int], player, sounds) -> str | None:
        """Obsługuje kliknięcia w sklepie. Może zwrócić 'close'."""
        for rect, action, val in self.buttons:
            if not rect.collidepoint(pos):
                continue
            if action == "close":
                return "close"
            elif action == "page_prev":
                self.change_skin_page(-1)
                sounds.play("talk")
                return None
            elif action == "page_next":
                self.change_skin_page(1)
                sounds.play("talk")
                return None
            elif action == "tab":
                self.tab = val
                sounds.play("talk")
                return None
            elif action == "weapon":
                spec = WEAPONS[val]
                if val in player.owned_weapons:
                    player.weapon_id = val
                    self.message = f"Wybrano broń: {spec['name']}!"
                    sounds.play("talk")
                elif player.seeds >= spec["cost"]:
                    player.seeds -= spec["cost"]
                    player.owned_weapons.add(val)
                    player.weapon_id = val
                    self.message = f"Kupiono {spec['name']} (na tę rundę)!"
                    sounds.play("buy")
                else:
                    self.message = f"Za mało ziaren! Potrzebujesz {spec['cost']} ziaren."
                    sounds.play("error")
                return None
            elif action == "skin":
                skin = SKINS[val]
                if val in player.owned_skins:
                    player.skin_id = val
                    self.message = f"Założono skórkę: {skin['name']} (zapisano)!"
                    sounds.play("talk")
                elif player.seeds >= skin["cost"]:
                    player.seeds -= skin["cost"]
                    player.owned_skins.add(val)
                    player.skin_id = val
                    self.message = f"Kupiono skórkę: {skin['name']} (zostaje na stałe)!"
                    sounds.play("buy")
                else:
                    self.message = f"Za mało ziaren! Potrzebujesz {skin['cost']} ziaren."
                    sounds.play("error")
                return None
            elif action == "upgrade":
                up = UPGRADES[val]
                lvl = player.upgrade_levels.get(val, 0)
                cost = up["base_cost"] + lvl * 8
                if lvl >= up["max_level"]:
                    self.message = "To ulepszenie ma już maksymalny poziom!"
                    sounds.play("talk")
                elif player.seeds >= cost:
                    player.seeds -= cost
                    player.upgrade_levels[val] = lvl + 1
                    if val == "max_hp":
                        player.max_hp += 25
                        player.hp = player.max_hp
                    self.message = f"Ulepszono: {up['name']}!"
                    sounds.play("buy")
                else:
                    self.message = f"Za mało ziaren! Potrzebujesz {cost} ziaren."
                    sounds.play("error")
                return None
        return None


def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_dialogue_box(surf: pygame.Surface, npc, text: str, hint: str = "[Spacja / E / Klik] Dalej"):
    """Okno rozmowy z botem fabularnym w stylu retro RPG."""
    box = pygame.Rect(140, SCREEN_H - 185, SCREEN_W - 280, 155)
    draw_panel(surf, box, alpha=240, border_col=GOLD)

    # Portret bota fabularnego po lewej
    portrait_r = pygame.Rect(box.x + 18, box.y + 22, 108, 108)
    pygame.draw.rect(surf, (45, 55, 82), portrait_r, border_radius=10)
    pygame.draw.rect(surf, GOLD, portrait_r, 2, border_radius=10)
    draw_hamster_avatar(surf, portrait_r.centerx, portrait_r.centery + 10, npc.skin_id, True, 0.0, scale=1.4, hat_override=npc.hat)

    f_name = get_font(22, bold=True)
    f_body = get_font(18)
    f_hint = get_font(14, bold=True)

    surf.blit(f_name.render(f"{npc.name} — {npc.role}", True, GOLD), (box.x + 144, box.y + 18))

    lines = _wrap_text(text, f_body, box.w - 170)
    for i, ln in enumerate(lines[:3]):
        surf.blit(f_body.render(ln, True, WHITE), (box.x + 144, box.y + 54 + i * 26))

    h_surf = f_hint.render(hint, True, (165, 225, 255))
    surf.blit(h_surf, (box.right - h_surf.get_width() - 20, box.bottom - 28))


def draw_start_screen(
    surf: pygame.Surface,
    elapsed: float,
    player_name: str,
    name_active: bool,
    difficulty_id: str,
    save_summary: str = "",
    confirm_reset: bool = False,
) -> tuple[pygame.Rect, pygame.Rect, list[tuple[pygame.Rect, str]], pygame.Rect | None]:
    """Kolorowy ekran startowy gry z wpisywaniem nicku, poziomem trudności i statusem zapisu."""
    dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    dim.fill((14, 22, 42, 195))
    surf.blit(dim, (0, 0))

    card = pygame.Rect(160, 26, SCREEN_W - 320, SCREEN_H - 52)
    draw_panel(surf, card, alpha=238, border_col=GOLD)

    f_big = get_font(40, bold=True)
    f_sub = get_font(18, bold=True)
    f_md = get_font(16, bold=True)
    f_sm = get_font(15)
    f_xs = get_font(14, bold=True)
    f_input = get_font(22, bold=True)
    f_btn = get_font(24, bold=True)

    title = f_big.render("HAMSTER SHOOTER", True, GOLD)
    sub = f_sub.render("Wielka Bitwa o Ziarna Słonecznika!", True, WHITE)
    surf.blit(title, (card.centerx - title.get_width() // 2, card.y + 14))
    surf.blit(sub, (card.centerx - sub.get_width() // 2, card.y + 60))

    # Trzy chomiki w różnych skórkach na powitanie!
    draw_hamster_avatar(surf, card.centerx - 120, card.y + 122, "ninja", True, 0.0, scale=1.4)
    draw_hamster_avatar(surf, card.centerx, card.y + 116, "krol", True, 0.0, scale=1.65)
    draw_hamster_avatar(surf, card.centerx + 120, card.y + 122, "diament", False, 3.14, scale=1.4)

    # --- 1. Pole wpisywania nazwy gracza (Nick) ---
    nick_y = card.y + 166
    nick_lbl = f_md.render("TWÓJ NICK (kliknij i wpisz):", True, GOLD)
    surf.blit(nick_lbl, (card.centerx - nick_lbl.get_width() // 2, nick_y))

    name_rect = pygame.Rect(card.centerx - 170, nick_y + 24, 340, 40)
    bg_col = (46, 56, 86) if name_active else (34, 40, 62)
    pygame.draw.rect(surf, bg_col, name_rect, border_radius=9)
    pygame.draw.rect(surf, GOLD if name_active else (120, 130, 160), name_rect, 2, border_radius=9)

    cursor = "|" if (name_active and int(elapsed * 2.5) % 2 == 0) else ""
    shown_name = (player_name + cursor) if (player_name or name_active) else "Chomik"
    name_col = WHITE if (player_name or name_active) else (150, 160, 185)
    n_surf = f_input.render(shown_name, True, name_col)
    surf.blit(n_surf, (name_rect.centerx - n_surf.get_width() // 2, name_rect.centery - n_surf.get_height() // 2))

    # --- 2. Wybór poziomu trudności ---
    diff_y = nick_y + 76
    d_hdr = f_md.render("POZIOM TRUDNOŚCI:", True, GOLD)
    surf.blit(d_hdr, (card.centerx - d_hdr.get_width() // 2, diff_y))

    diff_buttons: list[tuple[pygame.Rect, str]] = []
    bw = 160
    bh = 40
    gap = 16
    total_bw = len(DIFFICULTY_ORDER) * bw + (len(DIFFICULTY_ORDER) - 1) * gap
    bx = card.centerx - total_bw // 2
    for did in DIFFICULTY_ORDER:
        d = DIFFICULTIES[did]
        selected = did == difficulty_id
        r = pygame.Rect(bx, diff_y + 24, bw, bh)
        fill = (55, 68, 102) if selected else (34, 40, 60)
        pygame.draw.rect(surf, fill, r, border_radius=9)
        pygame.draw.rect(surf, d["color"] if selected else (95, 105, 135), r, 3 if selected else 1, border_radius=9)
        lbl = f_md.render(d["name"].upper(), True, d["color"] if selected else (200, 210, 225))
        surf.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))
        diff_buttons.append((r, did))
        bx += bw + gap

    cur_diff = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normalny"])
    d_desc = f_sm.render(cur_diff["desc"], True, cur_diff["color"])
    surf.blit(d_desc, (card.centerx - d_desc.get_width() // 2, diff_y + 72))

    # --- 3. Skrócone sterowanie ---
    ctrl_y = diff_y + 104
    controls = [
        "A / D — bieg   |   W / Spacja — skok i PODWÓJNY SKOK   |   Myszka + LPM — celowanie i strzał",
        "1–4 / Kółko — Ziarna, Karabin, Shotgun, AWP   |   E — rozmowa z NPC   |   B — Sklep",
        "Wskakuj głową w złote bloki '?' jak w Mario, aby zdobyć ziarna i power-upy!",
    ]
    for i, line in enumerate(controls):
        s = f_sm.render(line, True, (215, 228, 245))
        surf.blit(s, (card.centerx - s.get_width() // 2, ctrl_y + i * 24))

    # --- 4. Informacja o zapisanym postępie + przycisk Resetuj zapis ---
    reset_btn = None
    if save_summary:
        s_surf = f_xs.render(save_summary, True, GREEN)
        surf.blit(s_surf, (card.centerx - s_surf.get_width() // 2, card.bottom - 110))

        reset_btn = pygame.Rect(card.right - 184, card.bottom - 68, 162, 44)
        r_col = (210, 45, 55) if confirm_reset else (95, 45, 55)
        pygame.draw.rect(surf, r_col, reset_btn, border_radius=9)
        pygame.draw.rect(surf, WHITE if confirm_reset else (200, 120, 120), reset_btn, 2, border_radius=9)
        r_txt = "NA PEWNO? KLIK" if confirm_reset else "RESETUJ ZAPIS"
        rl = f_xs.render(r_txt, True, WHITE)
        surf.blit(rl, (reset_btn.centerx - rl.get_width() // 2, reset_btn.centery - rl.get_height() // 2))

    # Przyciski SINGLEPLAYER (7 Botów) i MULTIPLAYER (Bez botów)
    btn = pygame.Rect(card.x + 24, card.bottom - 74, 316, 54)
    pygame.draw.rect(surf, (58, 185, 82), btn, border_radius=12)
    pygame.draw.rect(surf, WHITE, btn, 3, border_radius=12)
    bl = get_font(20, bold=True).render("SINGLEPLAYER (7 BOTÓW)", True, WHITE)
    surf.blit(bl, (btn.centerx - bl.get_width() // 2, btn.centery - bl.get_height() // 2))

    mp_btn = pygame.Rect(btn.right + 14, card.bottom - 74, 316, 54)
    pygame.draw.rect(surf, (42, 130, 225), mp_btn, border_radius=12)
    pygame.draw.rect(surf, GOLD, mp_btn, 3, border_radius=12)
    ml = get_font(20, bold=True).render("MULTIPLAYER (BEZ BOTÓW)", True, WHITE)
    surf.blit(ml, (mp_btn.centerx - ml.get_width() // 2, mp_btn.centery - ml.get_height() // 2))

    return btn, name_rect, diff_buttons, reset_btn, mp_btn


def draw_multiplayer_lobby(
    surf: pygame.Surface,
    elapsed: float,
    server_url: str,
    room_code: str,
    active_field: str,
    status_text: str,
) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect, pygame.Rect]:
    """Panel łączenia z serwerem Multiplayer (lokalnie lub na Render.com)."""
    dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    dim.fill((12, 18, 36, 205))
    surf.blit(dim, (0, 0))

    card = pygame.Rect(210, 96, SCREEN_W - 420, 520)
    draw_panel(surf, card, alpha=245, border_col=GOLD)

    f_big = get_font(34, bold=True)
    f_md = get_font(17, bold=True)
    f_sm = get_font(15)
    f_inp = get_font(20, bold=True)
    f_btn = get_font(22, bold=True)

    t = f_big.render("MULTIPLAYER ONLINE", True, GOLD)
    surf.blit(t, (card.centerx - t.get_width() // 2, card.y + 24))
    sub = f_sm.render("Cross-play na Render.com — czyste PvP z kolegami (bez botów!)", True, (205, 222, 245))
    surf.blit(sub, (card.centerx - sub.get_width() // 2, card.y + 70))

    cursor = "|" if int(elapsed * 2.5) % 2 == 0 else ""

    # Pole 1: Adres serwera
    y1 = card.y + 118
    surf.blit(f_md.render("ADRES SERWERA (np. twoja-gra.onrender.com lub localhost:8000):", True, GOLD), (card.x + 48, y1))
    url_rect = pygame.Rect(card.x + 48, y1 + 28, card.w - 96, 44)
    pygame.draw.rect(surf, (46, 56, 86) if active_field == "url" else (34, 40, 62), url_rect, border_radius=9)
    pygame.draw.rect(surf, GOLD if active_field == "url" else (115, 125, 155), url_rect, 2, border_radius=9)
    u_txt = server_url + (cursor if active_field == "url" else "")
    u_s = f_inp.render(u_txt, True, WHITE)
    surf.blit(u_s, (url_rect.x + 14, url_rect.centery - u_s.get_height() // 2))

    # Pole 2: Kod pokoju
    y2 = y1 + 96
    surf.blit(f_md.render("KOD POKOJU (zostaw puste, żeby STWORZYĆ nowy pokój):", True, GOLD), (card.x + 48, y2))
    room_rect = pygame.Rect(card.x + 48, y2 + 28, 280, 44)
    pygame.draw.rect(surf, (46, 56, 86) if active_field == "room" else (34, 40, 62), room_rect, border_radius=9)
    pygame.draw.rect(surf, GOLD if active_field == "room" else (115, 125, 155), room_rect, 2, border_radius=9)
    r_txt = room_code + (cursor if active_field == "room" else "")
    r_s = f_inp.render(r_txt if r_txt else "NOWY POKÓJ", True, WHITE if r_txt else (130, 145, 175))
    surf.blit(r_s, (room_rect.x + 14, room_rect.centery - r_s.get_height() // 2))

    hint = f_sm.render("Po wejściu dostaniesz 4-literowy kod pokoju — wyślij go kolegom!", True, (175, 225, 195))
    surf.blit(hint, (card.x + 48, y2 + 86))

    # Status połączenia
    if status_text:
        st_col = RED if "Błąd" in status_text else GOLD
        st = f_md.render(status_text[:68], True, st_col)
        surf.blit(st, (card.centerx - st.get_width() // 2, card.bottom - 120))

    # Przyciski
    connect_btn = pygame.Rect(card.x + 48, card.bottom - 78, 360, 54)
    back_btn = pygame.Rect(card.right - 220, card.bottom - 78, 172, 54)

    pygame.draw.rect(surf, (58, 185, 82), connect_btn, border_radius=10)
    pygame.draw.rect(surf, WHITE, connect_btn, 2, border_radius=10)
    cl = f_btn.render("POŁĄCZ I GRAJ! [ENTER]", True, WHITE)
    surf.blit(cl, (connect_btn.centerx - cl.get_width() // 2, connect_btn.centery - cl.get_height() // 2))

    pygame.draw.rect(surf, (130, 55, 65), back_btn, border_radius=10)
    pygame.draw.rect(surf, WHITE, back_btn, 2, border_radius=10)
    bl = f_btn.render("POWRÓT", True, WHITE)
    surf.blit(bl, (back_btn.centerx - bl.get_width() // 2, back_btn.centery - bl.get_height() // 2))

    return connect_btn, back_btn, url_rect, room_rect


def draw_victory_overlay(surf: pygame.Surface, player, difficulty_id: str) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
    """Ekran wygranej po zebraniu wymaganej liczby ziaren słonecznika."""
    dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    dim.fill((12, 18, 34, 185))
    surf.blit(dim, (0, 0))

    card = pygame.Rect(230, 120, SCREEN_W - 460, 460)
    draw_panel(surf, card, alpha=245, border_col=GOLD)

    f_big = get_font(38, bold=True)
    f_md = get_font(20, bold=True)
    f_sm = get_font(17, bold=True)

    t = f_big.render(f"ZWYCIĘSTWO, {player.name.upper()}!", True, GOLD)
    surf.blit(t, (card.centerx - t.get_width() // 2, card.y + 28))

    draw_hamster_avatar(surf, card.centerx, card.y + 132, player.skin_id, True, 0.0, scale=2.1)

    diff = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normalny"])
    l1 = f_md.render(f"Zebrałeś {player.total_seeds} ziaren słonecznika!", True, WHITE)
    l2 = f_md.render(f"Pokonane boty: {player.kills}   |   Poziom: {diff['name']}", True, diff["color"])
    surf.blit(l1, (card.centerx - l1.get_width() // 2, card.y + 205))
    surf.blit(l2, (card.centerx - l2.get_width() // 2, card.y + 242))

    cont_btn = pygame.Rect(card.centerx - 285, card.bottom - 102, 180, 54)
    restart_btn = pygame.Rect(card.centerx - 90, card.bottom - 102, 180, 54)
    menu_btn = pygame.Rect(card.centerx + 105, card.bottom - 102, 180, 54)

    for btn, col, txt in (
        (cont_btn, (58, 175, 85), "GRAJ DALEJ"),
        (restart_btn, (65, 115, 200), "NOWA RUNDA"),
        (menu_btn, (175, 115, 45), "MENU"),
    ):
        pygame.draw.rect(surf, col, btn, border_radius=10)
        pygame.draw.rect(surf, WHITE, btn, 2, border_radius=10)
        lbl = f_sm.render(txt, True, WHITE)
        surf.blit(lbl, (btn.centerx - lbl.get_width() // 2, btn.centery - lbl.get_height() // 2))

    return cont_btn, restart_btn, menu_btn
