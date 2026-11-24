"""
map_level.py — Zamknięta mapa w stylu Super Mario z ulepszoną grafiką!
Zawiera:
- wstępnie wyrenderowane tekstury kafelków (cegły 3D, ziemia z kamyczkami i trawką,
  błyszczące zielone rury, złote bloki '?' z nitami w rogach),
- wielowarstwowe tło (słońce z promieniami, góry w oddali, wzgórza z krzaczkami,
  płynące po niebie chmurki i kołyszące się na wietrze słoneczniki!),
- cienie pod platformami i sprężyste grzybki-trampoliny.
"""

import math
import random
import pygame
from settings import TILE_SIZE, MAP_COLS, MAP_ROWS, WORLD_W, WORLD_H, SKY_TOP, SKY_BOTTOM, GOLD


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
        self.cooldown = 12.0
        self.bump_vel = -180.0
        return True

    def update(self, dt: float):
        if not self.active:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.active = True
                self.cooldown = 0.0

        if self.bump_offset != 0.0 or self.bump_vel != 0.0:
            self.bump_offset += self.bump_vel * dt
            self.bump_vel += 1400.0 * dt
            if self.bump_offset >= 0.0:
                self.bump_offset = 0.0
                self.bump_vel = 0.0


class MarioArena:
    """Przechowuje wszystkie bloki, tekstury, dekoracje i punkty na zamkniętej mapie."""

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

        # Ruchome chmurki i dekoracyjne słoneczniki w tle
        self.clouds = [
            {"x": 180.0, "y": 145, "scale": 1.0, "speed": 14.0},
            {"x": 520.0, "y": 110, "scale": 1.2, "speed": 10.0},
            {"x": 880.0, "y": 175, "scale": 0.9, "speed": 16.0},
            {"x": 1240.0, "y": 125, "scale": 1.15, "speed": 12.0},
            {"x": 1520.0, "y": 215, "scale": 0.85, "speed": 18.0},
            {"x": 360.0, "y": 280, "scale": 0.8, "speed": 11.0},
        ]
        self.bg_sunflowers = [
            (110, (MAP_ROWS - 2) * TILE_SIZE, 1.0),
            (315, (MAP_ROWS - 2) * TILE_SIZE, 0.85),
            (590, (MAP_ROWS - 2) * TILE_SIZE, 1.1),
            (840, (MAP_ROWS - 2) * TILE_SIZE, 0.9),
            (1030, (MAP_ROWS - 2) * TILE_SIZE, 1.05),
            (1310, (MAP_ROWS - 2) * TILE_SIZE, 0.95),
            (1490, (MAP_ROWS - 2) * TILE_SIZE, 1.0),
        ]
        # Złote pyłki słonecznika / motylki unoszące się powoli w powietrzu
        self.ambient_motes = [
            {
                "x": random.uniform(80, WORLD_W - 80),
                "y": random.uniform(90, WORLD_H - 120),
                "vx": random.uniform(-14, 14),
                "phase": random.uniform(0, 6.28),
                "r": random.choice([2, 2, 3]),
                "col": random.choice([(255, 245, 160), (255, 255, 230), (255, 215, 90)]),
            }
            for _ in range(28)
        ]

        self._parse_layout()
        self._build_tile_textures()
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

        for r in range(2, MAP_ROWS - 2):
            for c in range(2, MAP_COLS - 2):
                if LEVEL_LAYOUT[r][c] == " " and LEVEL_LAYOUT[r + 1][c] in ("#", "B", "?"):
                    self.seed_spots.append((c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2))

    def _build_tile_textures(self):
        """Tworzy szczegółowe, wypukłe tekstury kafelków 40x40 (szybsze i dużo ładniejsze!)."""
        t = TILE_SIZE

        # 1. Cegła Mario 3D z połyskiem i cieniami
        self.tex_brick = pygame.Surface((t, t))
        self.tex_brick.fill((188, 88, 46))
        # Górny wiersz cegieł
        for bx in (0, 20):
            pygame.draw.rect(self.tex_brick, (214, 108, 58), (bx + 2, 2, 16, 16))
            pygame.draw.line(self.tex_brick, (242, 152, 98), (bx + 2, 2), (bx + 17, 2), 2)
            pygame.draw.line(self.tex_brick, (232, 134, 82), (bx + 2, 2), (bx + 2, 16), 2)
            pygame.draw.line(self.tex_brick, (128, 52, 24), (bx + 2, 17), (bx + 17, 17), 2)
        # Dolny wiersz cegieł (przesunięty jak prawdziwy mur)
        for bx, bw in ((0, 10), (10, 20), (30, 10)):
            pygame.draw.rect(self.tex_brick, (206, 100, 52), (bx + 1, 22, bw - 2, 16))
            pygame.draw.line(self.tex_brick, (236, 142, 90), (bx + 1, 22), (bx + bw - 2, 22), 2)
            pygame.draw.line(self.tex_brick, (120, 48, 22), (bx + 1, 37), (bx + bw - 2, 37), 2)
        # Fugi i obrys
        pygame.draw.line(self.tex_brick, (88, 36, 18), (0, 20), (t, 20), 2)
        pygame.draw.line(self.tex_brick, (88, 36, 18), (20, 0), (20, 20), 2)
        pygame.draw.line(self.tex_brick, (88, 36, 18), (10, 20), (10, t), 2)
        pygame.draw.line(self.tex_brick, (88, 36, 18), (30, 20), (30, t), 2)
        pygame.draw.rect(self.tex_brick, (76, 30, 14), (0, 0, t, t), 2)

        # 2. Ziemia / mur zewnętrzny z kamyczkami
        self.tex_ground = pygame.Surface((t, t))
        self.tex_ground.fill((134, 84, 48))
        pygame.draw.rect(self.tex_ground, (150, 96, 56), (3, 3, t - 6, t - 6))
        for px, py, pr, col in ((10, 14, 4, (112, 68, 38)), (27, 19, 5, (106, 62, 34)), (16, 30, 4, (162, 108, 66)), (31, 32, 3, (116, 70, 38))):
            pygame.draw.circle(self.tex_ground, col, (px, py), pr)
        pygame.draw.rect(self.tex_ground, (92, 54, 28), (0, 0, t, t), 2)

        # 3. Ziemia z soczystą trawką Mario na wierzchu
        self.tex_grass = self.tex_ground.copy()
        pygame.draw.rect(self.tex_grass, (54, 178, 62), (0, 0, t, 12))
        pygame.draw.rect(self.tex_grass, (106, 224, 96), (0, 0, t, 5))
        # Fala trawy zwisająca na ziemię
        for gx in range(2, t, 8):
            pygame.draw.polygon(self.tex_grass, (54, 178, 62), [(gx, 11), (gx + 4, 16), (gx + 8, 11)])
        pygame.draw.line(self.tex_grass, (36, 122, 42), (0, 12), (t, 12), 2)

        # 4. Zielona rura (Warp Pipe) z cylindrycznym połyskiem
        self.tex_pipe = pygame.Surface((t, t))
        bands = [
            (0, 6, (28, 132, 44)),
            (6, 7, (62, 198, 76)),
            (13, 6, (148, 248, 148)),
            (19, 9, (52, 184, 68)),
            (28, 7, (32, 142, 48)),
            (35, 5, (20, 102, 34)),
        ]
        for bx, bw, col in bands:
            pygame.draw.rect(self.tex_pipe, col, (bx, 0, bw, t))
        pygame.draw.rect(self.tex_pipe, (14, 72, 24), (0, 0, t, t), 2)

        # 5. Zużyty blok '?' (z nitami)
        self.tex_q_used = pygame.Surface((t, t))
        self.tex_q_used.fill((124, 104, 86))
        pygame.draw.rect(self.tex_q_used, (142, 120, 100), (3, 3, t - 6, t - 6), border_radius=3)
        for nx, ny in ((6, 6), (t - 7, 6), (6, t - 7), (t - 7, t - 7)):
            pygame.draw.circle(self.tex_q_used, (78, 62, 48), (nx, ny), 2)
        pygame.draw.rect(self.tex_q_used, (68, 54, 42), (0, 0, t, t), 2, border_radius=3)

        # Półprzezroczysty miękki cień rzucany pod platformami
        self.shadow_strip = pygame.Surface((t, 10), pygame.SRCALPHA)
        pygame.draw.rect(self.shadow_strip, (15, 25, 45, 58), (0, 0, t, 8))

    def _build_sky_surface(self):
        """Tworzy bogate, warstwowe tło Mario (niebo, słońce, góry, wzgórza, krzaczki)."""
        self.sky_surf = pygame.Surface((WORLD_W, WORLD_H))
        for y in range(WORLD_H):
            t = y / WORLD_H
            col = (
                int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t),
                int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t),
                int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t),
            )
            pygame.draw.line(self.sky_surf, col, (0, y), (WORLD_W, y))

        # Słoneczko z delikatną poświatą w prawym górnym rogu nieba
        sun_x, sun_y = 1360, 130
        glow = pygame.Surface((260, 260), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 245, 165, 45), (130, 130), 120)
        pygame.draw.circle(glow, (255, 238, 120, 85), (130, 130), 78)
        self.sky_surf.blit(glow, (sun_x - 130, sun_y - 130))
        pygame.draw.circle(self.sky_surf, (255, 236, 105), (sun_x, sun_y), 46)
        pygame.draw.circle(self.sky_surf, (255, 250, 180), (sun_x - 10, sun_y - 10), 22)

        # Warstwa 1 (dalekie góry)
        far_mountains = [(160, 800, 280, 290), (540, 800, 340, 340), (1020, 800, 310, 310), (1440, 800, 290, 280)]
        for mx, my, mw, mh in far_mountains:
            pygame.draw.ellipse(self.sky_surf, (118, 192, 168), (mx - mw, my - mh, mw * 2, mh * 2))

        # Warstwa 2 (soczyste wzgórza w stylu Super Mario z jasnymi plamkami!)
        hills = [(240, 800, 230, 185), (660, 800, 300, 240), (1140, 800, 255, 195), (1470, 800, 220, 165)]
        for hx, hy, hw, hh in hills:
            pygame.draw.ellipse(self.sky_surf, (76, 178, 86), (hx - hw, hy - hh, hw * 2, hh * 2))
            pygame.draw.ellipse(self.sky_surf, (104, 206, 108), (hx - hw + 18, hy - hh + 14, hw * 2 - 36, hh * 2 - 20))
            # Urocze jasne kropki na wzgórzach jak w Super Mario World
            pygame.draw.ellipse(self.sky_surf, (132, 226, 132), (hx - 24, hy - hh + 42, 18, 28))
            pygame.draw.ellipse(self.sky_surf, (132, 226, 132), (hx + 16, hy - hh + 62, 16, 24))

        # Krzaczki, drewniany płotek i kolorowe kwiatuszki przy linii ziemi
        ground_y = (MAP_ROWS - 2) * TILE_SIZE

        # Zamek Chomików w stylu Mario na dalekim wzgórzu!
        castle_x, castle_y = 660, ground_y - 175
        pygame.draw.rect(self.sky_surf, (232, 218, 198), (castle_x - 42, castle_y - 54, 84, 72))
        pygame.draw.rect(self.sky_surf, (188, 168, 145), (castle_x - 42, castle_y - 54, 84, 72), 2)
        # Dwie boczne wieżyczki + środkowa wysoka wieża
        for tx, tw, th in ((castle_x - 52, 24, 78), (castle_x + 28, 24, 78), (castle_x - 16, 32, 102)):
            pygame.draw.rect(self.sky_surf, (238, 226, 206), (tx, castle_y + 18 - th, tw, th))
            pygame.draw.rect(self.sky_surf, (182, 162, 140), (tx, castle_y + 18 - th, tw, th), 2)
            # Czerwony spiczasty dach Mario
            roof = [(tx - 4, castle_y + 18 - th), (tx + tw + 4, castle_y + 18 - th), (tx + tw // 2, castle_y - 8 - th)]
            pygame.draw.polygon(self.sky_surf, (218, 62, 68), roof)
            pygame.draw.polygon(self.sky_surf, (152, 32, 38), roof, 2)
            # Złota chorągiewka na czubku
            pygame.draw.line(self.sky_surf, (120, 82, 42), (tx + tw // 2, castle_y - 8 - th), (tx + tw // 2, castle_y - 22 - th), 2)
            pygame.draw.polygon(self.sky_surf, GOLD, [(tx + tw // 2, castle_y - 22 - th), (tx + tw // 2 + 12, castle_y - 18 - th), (tx + tw // 2, castle_y - 14 - th)])
        # Brama zamku
        pygame.draw.ellipse(self.sky_surf, (92, 62, 44), (castle_x - 13, castle_y - 16, 26, 36))
        pygame.draw.rect(self.sky_surf, (92, 62, 44), (castle_x - 13, castle_y, 26, 18))

        # Drewniany płotek w tle
        for fx in range(420, 560, 22):
            pygame.draw.rect(self.sky_surf, (198, 150, 96), (fx, ground_y - 24, 10, 24), border_radius=2)
            pygame.draw.rect(self.sky_surf, (142, 98, 56), (fx, ground_y - 24, 10, 24), 1, border_radius=2)
        pygame.draw.rect(self.sky_surf, (186, 138, 86), (416, ground_y - 17, 152, 5))
        pygame.draw.rect(self.sky_surf, (186, 138, 86), (416, ground_y - 8, 152, 5))

        for bx in (180, 440, 740, 960, 1220, 1410):
            pygame.draw.circle(self.sky_surf, (52, 162, 68), (bx - 18, ground_y - 4), 18)
            pygame.draw.circle(self.sky_surf, (66, 188, 82), (bx, ground_y - 12), 24)
            pygame.draw.circle(self.sky_surf, (52, 162, 68), (bx + 20, ground_y - 4), 18)
            # Drobne kwiatuszki na krzaczkach
            pygame.draw.circle(self.sky_surf, (255, 240, 110), (bx - 8, ground_y - 12), 3)
            pygame.draw.circle(self.sky_surf, (255, 165, 195), (bx + 9, ground_y - 7), 3)

    def update(self, dt: float):
        for qb in self.question_blocks:
            qb.update(dt)
        for cl in self.clouds:
            cl["x"] += cl["speed"] * dt
            if cl["x"] > WORLD_W + 90:
                cl["x"] = -90.0
        for m in self.ambient_motes:
            m["x"] += m["vx"] * dt
            m["phase"] += dt * 1.8
            if m["x"] < 50:
                m["x"] = WORLD_W - 50
            elif m["x"] > WORLD_W - 50:
                m["x"] = 50

    def point_hits_solid(self, x: float, y: float) -> bool:
        if x < TILE_SIZE or x > WORLD_W - TILE_SIZE or y < TILE_SIZE or y > WORLD_H - TILE_SIZE * 2:
            return True
        col = int(x // TILE_SIZE)
        row = int(y // TILE_SIZE)
        if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS:
            return LEVEL_LAYOUT[row][col] in ("#", "B", "?", "P")
        return True

    def raycast_wall(self, x0: float, y0: float, angle: float, max_dist: float = 950.0) -> tuple[float, float]:
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

    def _draw_bg_sunflower(self, surf: pygame.Surface, sx: int, sy: int, scale: float, sway: float):
        """Rysuje kołyszący się w tle kwitnący słonecznik."""
        h = int(46 * scale)
        hx = sx + int(sway)
        hy = sy - h
        # Łodyga i dwa listki
        pygame.draw.line(surf, (48, 148, 56), (sx, sy), (hx, hy), max(2, int(4 * scale)))
        pygame.draw.ellipse(surf, (66, 178, 72), (sx - int(14 * scale), sy - h // 2, int(14 * scale), int(7 * scale)))
        pygame.draw.ellipse(surf, (66, 178, 72), (sx + int(2 * scale), sy - h // 2 - 4, int(14 * scale), int(7 * scale)))
        # Złote płatki
        pr = max(3, int(5 * scale))
        dist = int(10 * scale)
        for deg in range(0, 360, 45):
            rad = math.radians(deg)
            pygame.draw.circle(surf, (255, 212, 48), (hx + int(math.cos(rad) * dist), hy + int(math.sin(rad) * dist)), pr)
        # Brązowy środek z ziarenkami
        pygame.draw.circle(surf, (92, 54, 24), (hx, hy), max(4, int(8 * scale)))
        pygame.draw.circle(surf, (132, 82, 38), (hx - 2, hy - 2), max(2, int(3 * scale)))

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, elapsed: float, q_font: pygame.font.Font):
        # 1. Tło nieba, słońca, zamku i wzgórz
        surf.blit(self.sky_surf, (-int(cam_x), -int(cam_y)))

        # 1a. Obracające się delikatne promienie słońca (god rays)
        sun_sx = int(1360 - cam_x)
        sun_sy = int(130 - cam_y)
        if -260 <= sun_sx <= surf.get_width() + 260:
            ray_surf = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
            for i in range(6):
                a1 = elapsed * 0.14 + i * (math.pi / 3.0)
                a2 = a1 + 0.16
                p1 = (sun_sx, sun_sy)
                p2 = (sun_sx + int(math.cos(a1) * 520), sun_sy + int(math.sin(a1) * 520))
                p3 = (sun_sx + int(math.cos(a2) * 520), sun_sy + int(math.sin(a2) * 520))
                pygame.draw.polygon(ray_surf, (255, 248, 185, 22), (p1, p2, p3))
            surf.blit(ray_surf, (0, 0))

        # 1b. Płynące puszyste chmurki z delikatnym cieniem
        for cl in self.clouds:
            cx = int(cl["x"] - cam_x * 0.75)
            cy = int(cl["y"] - cam_y * 0.5)
            sc = cl["scale"]
            if -120 <= cx <= surf.get_width() + 120:
                pygame.draw.ellipse(surf, (215, 236, 250), (cx - int(48 * sc), cy - int(8 * sc), int(96 * sc), int(30 * sc)))
                pygame.draw.ellipse(surf, (255, 255, 255), (cx - int(46 * sc), cy - int(16 * sc), int(92 * sc), int(34 * sc)))
                pygame.draw.ellipse(surf, (255, 255, 255), (cx - int(28 * sc), cy - int(28 * sc), int(58 * sc), int(40 * sc)))

        # 1c. Kołyszące się słoneczniki w tle
        for fx, fy, fsc in self.bg_sunflowers:
            sx = int(fx - cam_x)
            sy = int(fy - cam_y)
            if -40 <= sx <= surf.get_width() + 40:
                sway = math.sin(elapsed * 2.2 + fx * 0.02) * 5.0 * fsc
                self._draw_bg_sunflower(surf, sx, sy, fsc, sway)

        view = pygame.Rect(int(cam_x) - 40, int(cam_y) - 40, surf.get_width() + 80, surf.get_height() + 80)

        # 2. Zewnętrzne mury i ziemia z trawką
        top_floor_y = (MAP_ROWS - 2) * TILE_SIZE
        for r in self.ground_rects:
            if not view.colliderect(r):
                continue
            dx, dy = r.x - int(cam_x), r.y - int(cam_y)
            surf.blit(self.tex_grass if r.y == top_floor_y else self.tex_ground, (dx, dy))

        # 3. Ceglane platformy Mario + miękki cień pod spodem + delikatna trawka na wierzchu
        for r in self.brick_rects:
            if not view.colliderect(r):
                continue
            dx, dy = r.x - int(cam_x), r.y - int(cam_y)
            surf.blit(self.shadow_strip, (dx + 3, dy + TILE_SIZE))
            surf.blit(self.tex_brick, (dx, dy))
            row_above = (r.y // TILE_SIZE) - 1
            col = r.x // TILE_SIZE
            if row_above >= 0 and LEVEL_LAYOUT[row_above][col] not in ("#", "B", "?", "P"):
                pygame.draw.rect(surf, (78, 198, 76), (dx + 2, dy, TILE_SIZE - 4, 4), border_radius=2)
                pygame.draw.rect(surf, (132, 236, 118), (dx + 4, dy, TILE_SIZE - 8, 2))

        # 4. Zielone rury Mario z cylindrycznym połyskiem i ciemnym wlotem
        for r in self.pipe_rects:
            if not view.colliderect(r):
                continue
            dx, dy = r.x - int(cam_x), r.y - int(cam_y)
            surf.blit(self.tex_pipe, (dx, dy))
            row_above = (r.y // TILE_SIZE) - 1
            col = r.x // TILE_SIZE
            if row_above >= 0 and LEVEL_LAYOUT[row_above][col] != "P":
                rim = pygame.Rect(dx - 5, dy, r.w + 10, 14)
                pygame.draw.rect(surf, (48, 188, 68), rim, border_radius=3)
                pygame.draw.rect(surf, (148, 248, 148), (rim.x + 12, rim.y + 2, 8, rim.h - 4))
                pygame.draw.rect(surf, (22, 110, 36), (rim.right - 10, rim.y + 2, 8, rim.h - 4))
                pygame.draw.rect(surf, (14, 72, 24), rim, 2, border_radius=3)
                pygame.draw.line(surf, (10, 48, 18), (dx + 4, dy + 2), (dx + r.w - 4, dy + 2), 2)
                pygame.draw.line(surf, (16, 78, 26), (dx, dy + 14), (dx + r.w, dy + 14), 3)

        # 5. Złote bloki ze znakiem zapytania '?' (z połyskiem, przesuwającym się blikiem i 4 nitami!)
        pulse = int(math.sin(elapsed * 5.5) * 14)
        gleam_pos = (elapsed * 38.0) % 72.0
        for qb in self.question_blocks:
            if not view.colliderect(qb.rect):
                continue
            dx = qb.rect.x - int(cam_x)
            dy = qb.rect.y - int(cam_y) + int(qb.bump_offset)
            surf.blit(self.shadow_strip, (dx + 3, dy + TILE_SIZE))
            dr = pygame.Rect(dx, dy, qb.rect.w, qb.rect.h)
            if qb.active:
                col = (min(255, 245 + pulse), min(255, 192 + pulse), 36)
                pygame.draw.rect(surf, col, dr, border_radius=5)
                pygame.draw.rect(surf, (255, 242, 150), (dr.x + 3, dr.y + 3, dr.w - 6, 7), border_radius=3)
                # Przesuwający się ukośny błysk światła po bloku '?'
                if gleam_pos < 36.0:
                    gx = int(gleam_pos)
                    pygame.draw.line(surf, (255, 255, 225), (dr.x + gx, dr.y + 4), (dr.x + max(4, gx - 8), dr.bottom - 5), 3)
                for nx, ny in ((dr.x + 6, dr.y + 6), (dr.right - 7, dr.y + 6), (dr.x + 6, dr.bottom - 7), (dr.right - 7, dr.bottom - 7)):
                    pygame.draw.circle(surf, (152, 92, 14), (nx, ny), 2)
                pygame.draw.rect(surf, (148, 88, 12), dr, 3, border_radius=5)
                q_sh = q_font.render("?", True, (130, 68, 8))
                q_fg = q_font.render("?", True, (255, 250, 225))
                qx = dr.centerx - q_fg.get_width() // 2
                qy = dr.centery - q_fg.get_height() // 2
                surf.blit(q_sh, (qx + 2, qy + 2))
                surf.blit(q_fg, (qx, qy))
            else:
                surf.blit(self.tex_q_used, (dx, dy))
                prog = 1.0 - (qb.cooldown / 12.0)
                pygame.draw.rect(surf, GOLD, (dr.x + 4, dr.bottom - 6, int((dr.w - 8) * prog), 3))

        # 6. Sprężyste grzybki-trampoliny z połyskiem
        for sp in self.springs:
            if not view.colliderect(sp):
                continue
            dr = pygame.Rect(sp.x - int(cam_x), sp.y - int(cam_y), sp.w, sp.h)
            pygame.draw.rect(surf, (245, 232, 200), (dr.centerx - 7, dr.y + 8, 14, dr.h - 8), border_radius=3)
            pygame.draw.rect(surf, (195, 178, 145), (dr.centerx - 7, dr.y + 8, 14, 4))
            cap = pygame.Rect(dr.x - 5, dr.y, dr.w + 10, 15)
            pygame.draw.ellipse(surf, (228, 42, 52), cap)
            pygame.draw.ellipse(surf, (250, 92, 96), (cap.x + 4, cap.y + 2, cap.w - 8, 6))
            pygame.draw.circle(surf, (255, 255, 255), (cap.x + 11, cap.y + 7), 3)
            pygame.draw.circle(surf, (255, 255, 255), (cap.centerx, cap.y + 5), 3)
            pygame.draw.circle(surf, (255, 255, 255), (cap.right - 11, cap.y + 7), 3)
            pygame.draw.ellipse(surf, (132, 18, 24), cap, 2)

        # 7. Złote pyłki słonecznika dryfujące po całej arenie
        for m in self.ambient_motes:
            mx = int(m["x"] - cam_x)
            my = int(m["y"] + math.sin(m["phase"]) * 8.0 - cam_y)
            if 0 <= mx <= surf.get_width() and 0 <= my <= surf.get_height():
                pygame.draw.circle(surf, m["col"], (mx, my), m["r"])
