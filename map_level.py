"""
map_level.py — Zamknięta mapa w stylu Mario!
Zawiera:
- ceglane mury dookoła całej areny (nikt nie wypadnie poza ekran),
- platformy z cegieł na kilku poziomach,
- złote bloki ze znakiem zapytania '?' (uderzenie głową od dołu wyrzuca ziarna albo power-upy!),
- zielone rury (jak w Mario) służące za osłony i punkty odradzania botów,
- sprężyste grzybki-trampoliny wybijające chomiki wysoko w górę.
"""

import math
import pygame
from settings import TILE_SIZE, MAP_COLS, MAP_ROWS, WORLD_W, WORLD_H, SKY_TOP, SKY_BOTTOM, GOLD


# Mapa zapisana tekstowo — łatwo ją edytować!
# '#' = mur/ziemia zewnętrzna
# 'B' = cegły Mario (platforma)
# '?' = złoty blok ze znakiem zapytania (daje ziarna/power-up po uderzeniu od dołu!)
# 'P' = zielona rura (przeszkoda/osłona)
# '^' = trampolina-grzybek (wybija w górę)
# '1','2','3' = boty fabularne (NPC)
# 'S' = miejsce startu gracza
# 'E' = punkty odradzania 7 atakujących botów

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


class QuestionBlock:
    """Złoty blok '?' z Mario — po uderzeniu głową od dołu podskakuje i daje nagrodę!"""

    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.active = True
        self.cooldown = 0.0
        self.bump_offset = 0.0
        self.bump_vel = 0.0

    def trigger(self) -> bool:
        if not self.active:
            return False
        self.active = False
        self.cooldown = 12.0  # Po 12 sekundach blok '?' znowu jest gotowy!
        self.bump_vel = -180.0
        return True

    def update(self, dt: float):
        if not self.active:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.active = True
                self.cooldown = 0.0

        # Sprężysta animacja podskoku bloku
        if self.bump_offset != 0.0 or self.bump_vel != 0.0:
            self.bump_offset += self.bump_vel * dt
            self.bump_vel += 1400.0 * dt
            if self.bump_offset >= 0.0:
                self.bump_offset = 0.0
                self.bump_vel = 0.0


class MarioArena:
    """Przechowuje wszystkie bloki, rury, trampoliny i punkty na zamkniętej mapie."""

    def __init__(self):
        self.solids: list[pygame.Rect] = []
        self.brick_rects: list[pygame.Rect] = []
        self.ground_rects: list[pygame.Rect] = []
        self.pipe_rects: list[pygame.Rect] = []
        self.question_blocks: list[QuestionBlock] = []
        self.springs: list[pygame.Rect] = []
        self.player_spawn = (200, WORLD_H - 140)
        self.bot_spawns: list[tuple[int, int]] = []
        self.npc_spawns: dict[str, tuple[int, int]] = {}
        self.seed_spots: list[tuple[int, int]] = []

        self._parse_layout()
        self._build_sky_surface()

    def _parse_layout(self):
        for r, row in enumerate(LEVEL_LAYOUT):
            for c, ch in enumerate(row):
                x = c * TILE_SIZE
                y = r * TILE_SIZE
                rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

                if ch == "#":
                    self.solids.append(rect)
                    self.ground_rects.append(rect)
                elif ch == "B":
                    self.solids.append(rect)
                    self.brick_rects.append(rect)
                elif ch == "?":
                    self.solids.append(rect)
                    self.question_blocks.append(QuestionBlock(rect))
                elif ch == "P":
                    self.solids.append(rect)
                    self.pipe_rects.append(rect)
                elif ch == "^":
                    self.springs.append(pygame.Rect(x + 4, y + 18, TILE_SIZE - 8, 22))
                elif ch == "S":
                    self.player_spawn = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                elif ch == "E":
                    self.bot_spawns.append((x + TILE_SIZE // 2, y + TILE_SIZE // 2))
                elif ch in ("1", "2", "3"):
                    self.npc_spawns[ch] = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)

        # Wyznaczamy dobre miejsca na pojawianie się ziaren słonecznika (nad platformami i podłogą)
        for r in range(2, MAP_ROWS - 2):
            for c in range(2, MAP_COLS - 2):
                if LEVEL_LAYOUT[r][c] == " " and LEVEL_LAYOUT[r + 1][c] in ("#", "B", "?"):
                    self.seed_spots.append((c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2))

    def _build_sky_surface(self):
        """Tworzy gradientowe niebo w stylu Mario raz na starcie (szybsze rysowanie)."""
        self.sky_surf = pygame.Surface((WORLD_W, WORLD_H))
        for y in range(WORLD_H):
            t = y / WORLD_H
            col = (
                int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t),
                int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t),
                int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t),
            )
            pygame.draw.line(self.sky_surf, col, (0, y), (WORLD_W, y))

        # Zielone wzgórza w tle (jak w Super Mario!)
        hills = [(240, 800, 220, 170), (650, 800, 290, 230), (1120, 800, 240, 185), (1440, 800, 210, 150)]
        for hx, hy, hw, hh in hills:
            pygame.draw.ellipse(self.sky_surf, (95, 195, 105), (hx - hw, hy - hh, hw * 2, hh * 2))
            pygame.draw.ellipse(self.sky_surf, (118, 212, 125), (hx - hw + 18, hy - hh + 14, hw * 2 - 36, hh * 2 - 20))

        # Puszyste chmurki na niebie
        clouds = [(220, 160), (540, 120), (880, 180), (1230, 130), (1460, 220), (380, 290), (1050, 300)]
        for cx, cy in clouds:
            pygame.draw.ellipse(self.sky_surf, (245, 252, 255), (cx - 48, cy - 16, 96, 36))
            pygame.draw.ellipse(self.sky_surf, (255, 255, 255), (cx - 30, cy - 28, 62, 42))

    def update(self, dt: float):
        for qb in self.question_blocks:
            qb.update(dt)

    def point_hits_solid(self, x: float, y: float) -> bool:
        if x < TILE_SIZE or x > WORLD_W - TILE_SIZE or y < TILE_SIZE or y > WORLD_H - TILE_SIZE * 2:
            return True
        col = int(x // TILE_SIZE)
        row = int(y // TILE_SIZE)
        if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS:
            return LEVEL_LAYOUT[row][col] in ("#", "B", "?", "P")
        return True

    def raycast_wall(self, x0: float, y0: float, angle: float, max_dist: float = 950.0) -> tuple[float, float]:
        """Zwraca punkt uderzenia promienia lasera AWP o najbliższą ścianę."""
        dx = math.cos(angle)
        dy = math.sin(angle)
        step = 10.0
        dist = 20.0
        while dist < max_dist:
            px = x0 + dx * dist
            py = y0 + dy * dist
            if self.point_hits_solid(px, py):
                return (px, py)
            dist += step
        return (x0 + dx * max_dist, y0 + dy * max_dist)

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, elapsed: float, q_font: pygame.font.Font):
        # 1. Tło nieba i wzgórz
        surf.blit(self.sky_surf, (-int(cam_x), -int(cam_y)))

        view = pygame.Rect(int(cam_x) - 40, int(cam_y) - 40, surf.get_width() + 80, surf.get_height() + 80)

        # 2. Zewnętrzne mury i ziemia z trawką
        for r in self.ground_rects:
            if not view.colliderect(r):
                continue
            dr = pygame.Rect(r.x - int(cam_x), r.y - int(cam_y), r.w, r.h)
            is_top_floor = (r.y == (MAP_ROWS - 2) * TILE_SIZE)
            pygame.draw.rect(surf, (145, 92, 52), dr)
            pygame.draw.rect(surf, (112, 68, 36), dr, 2)
            if is_top_floor:
                pygame.draw.rect(surf, (68, 192, 74), (dr.x, dr.y, dr.w, 10))
                pygame.draw.rect(surf, (48, 145, 55), (dr.x, dr.y + 8, dr.w, 3))

        # 3. Ceglane platformy Mario
        for r in self.brick_rects:
            if not view.colliderect(r):
                continue
            dr = pygame.Rect(r.x - int(cam_x), r.y - int(cam_y), r.w, r.h)
            pygame.draw.rect(surf, (198, 98, 52), dr)
            pygame.draw.rect(surf, (232, 136, 84), (dr.x + 2, dr.y + 2, dr.w - 4, 6))
            pygame.draw.line(surf, (110, 48, 24), (dr.x, dr.y + 20), (dr.right, dr.y + 20), 2)
            pygame.draw.line(surf, (110, 48, 24), (dr.x + 20, dr.y), (dr.x + 20, dr.y + 20), 2)
            pygame.draw.line(surf, (110, 48, 24), (dr.x + 10, dr.y + 20), (dr.x + 10, dr.bottom), 2)
            pygame.draw.line(surf, (110, 48, 24), (dr.x + 30, dr.y + 20), (dr.x + 30, dr.bottom), 2)
            pygame.draw.rect(surf, (95, 42, 20), dr, 2)

        # 4. Zielone rury Mario
        for r in self.pipe_rects:
            if not view.colliderect(r):
                continue
            dr = pygame.Rect(r.x - int(cam_x), r.y - int(cam_y), r.w, r.h)
            pygame.draw.rect(surf, (46, 178, 66), dr)
            pygame.draw.rect(surf, (110, 232, 118), (dr.x + 5, dr.y, 9, dr.h))
            pygame.draw.rect(surf, (26, 122, 42), (dr.right - 9, dr.y, 9, dr.h))
            pygame.draw.rect(surf, (18, 86, 30), dr, 2)
            # Górny kołnierz rury, jeśli nad nią jest pusto
            row_above = (r.y // TILE_SIZE) - 1
            col = r.x // TILE_SIZE
            if row_above >= 0 and LEVEL_LAYOUT[row_above][col] != "P":
                rim = pygame.Rect(dr.x - 4, dr.y, dr.w + 8, 12)
                pygame.draw.rect(surf, (58, 198, 78), rim)
                pygame.draw.rect(surf, (18, 86, 30), rim, 2)

        # 5. Złote bloki ze znakiem zapytania '?'
        pulse = int(math.sin(elapsed * 5.0) * 14)
        for qb in self.question_blocks:
            if not view.colliderect(qb.rect):
                continue
            dr = pygame.Rect(
                qb.rect.x - int(cam_x),
                qb.rect.y - int(cam_y) + int(qb.bump_offset),
                qb.rect.w,
                qb.rect.h,
            )
            if qb.active:
                col = (min(255, 242 + pulse), min(255, 192 + pulse), 42)
                pygame.draw.rect(surf, col, dr, border_radius=4)
                pygame.draw.rect(surf, (165, 108, 18), dr, 3, border_radius=4)
                q_surf = q_font.render("?", True, (115, 62, 10))
                surf.blit(q_surf, (dr.centerx - q_surf.get_width() // 2, dr.centery - q_surf.get_height() // 2))
            else:
                pygame.draw.rect(surf, (132, 112, 92), dr, border_radius=4)
                pygame.draw.rect(surf, (78, 64, 52), dr, 2, border_radius=4)
                # Mały pasek ładowania na dole zużytego bloku
                prog = 1.0 - (qb.cooldown / 12.0)
                pygame.draw.rect(surf, GOLD, (dr.x + 4, dr.bottom - 6, int((dr.w - 8) * prog), 3))

        # 6. Sprężyste grzybki-trampoliny
        for sp in self.springs:
            if not view.colliderect(sp):
                continue
            dr = pygame.Rect(sp.x - int(cam_x), sp.y - int(cam_y), sp.w, sp.h)
            # Nóżka grzybka
            pygame.draw.rect(surf, (245, 232, 200), (dr.centerx - 7, dr.y + 8, 14, dr.h - 8))
            # Czerwony kapelusz w białe kropki
            cap = pygame.Rect(dr.x - 4, dr.y, dr.w + 8, 14)
            pygame.draw.ellipse(surf, (232, 48, 56), cap)
            pygame.draw.circle(surf, (255, 255, 255), (cap.x + 10, cap.y + 6), 3)
            pygame.draw.circle(surf, (255, 255, 255), (cap.centerx, cap.y + 5), 3)
            pygame.draw.circle(surf, (255, 255, 255), (cap.right - 10, cap.y + 6), 3)
            pygame.draw.ellipse(surf, (145, 22, 28), cap, 2)
