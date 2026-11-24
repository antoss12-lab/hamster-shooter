"""
map_level.py — Zamknięta mapa 2.5D w stylu Super Mario 3D World!
Zawiera:
- dynamiczną perspektywę 2.5D: wszystkie cegły, złote bloki '?', podłoga i zielone rury
  mają widoczne słoneczne górne ścianki 3D oraz cieniowane boczne ścianki głębi,
  które lekko obracają się w perspektywie wraz z ruchem kamery!
- ikoniczną trawiastą podłogę 3D w szachownicę (jak w Super Mario 3D World!),
- rury Warp Pipe z trójwymiarowym eliptycznym otworem u góry i cylindrycznym połyskiem,
- unoszące się w tle wyspy 3D, zamek Mario, promienie słońca, chmury 3D i słoneczniki,
- funkcję find_ground_y() do rzucania dynamicznego cienia 3D pod skaczącymi chomikami!
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


def _is_solid_cell(col: int, row: int) -> bool:
    if 0 <= row < MAP_ROWS and 0 <= col < MAP_COLS:
        return LEVEL_LAYOUT[row][col] in ("#", "B", "?", "P")
    return True


class QuestionBlock:
    """Złoty blok '?' 3D z Mario — po uderzeniu głową od dołu podskakuje i daje nagrodę!"""

    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.col = rect.x // TILE_SIZE
        self.row = rect.y // TILE_SIZE
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
    """Przechowuje wszystkie bloki 2.5D, tekstury, dekoracje i punkty na zamkniętej mapie."""

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

        self.clouds = [
            {"x": 180.0, "y": 140, "scale": 1.05, "speed": 14.0},
            {"x": 520.0, "y": 105, "scale": 1.25, "speed": 10.0},
            {"x": 880.0, "y": 170, "scale": 0.92, "speed": 16.0},
            {"x": 1240.0, "y": 120, "scale": 1.18, "speed": 12.0},
            {"x": 1520.0, "y": 210, "scale": 0.88, "speed": 18.0},
            {"x": 360.0, "y": 275, "scale": 0.82, "speed": 11.0},
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
        """Tworzy wypukłe, błyszczące frontowe tekstury 3D kafelków 40x40."""
        t = TILE_SIZE

        # 1. Cegła Super Mario 3D z wypukłym połyskiem i głębokimi fugami
        self.tex_brick = pygame.Surface((t, t))
        self.tex_brick.fill((176, 82, 42))
        for bx in (0, 20):
            pygame.draw.rect(self.tex_brick, (216, 108, 56), (bx + 2, 2, 16, 16), border_radius=2)
            pygame.draw.line(self.tex_brick, (248, 166, 112), (bx + 3, 3), (bx + 16, 3), 2)
            pygame.draw.line(self.tex_brick, (238, 142, 88), (bx + 3, 3), (bx + 3, 15), 2)
            pygame.draw.line(self.tex_brick, (124, 48, 22), (bx + 3, 17), (bx + 17, 17), 2)
        for bx, bw in ((0, 10), (10, 20), (30, 10)):
            pygame.draw.rect(self.tex_brick, (206, 98, 50), (bx + 1, 22, bw - 2, 16), border_radius=2)
            pygame.draw.line(self.tex_brick, (242, 152, 98), (bx + 2, 23), (bx + bw - 3, 23), 2)
            pygame.draw.line(self.tex_brick, (114, 44, 20), (bx + 2, 37), (bx + bw - 3, 37), 2)
        pygame.draw.line(self.tex_brick, (84, 34, 16), (0, 20), (t, 20), 2)
        pygame.draw.line(self.tex_brick, (84, 34, 16), (20, 0), (20, 20), 2)
        pygame.draw.line(self.tex_brick, (84, 34, 16), (10, 20), (10, t), 2)
        pygame.draw.line(self.tex_brick, (84, 34, 16), (30, 20), (30, t), 2)
        pygame.draw.rect(self.tex_brick, (74, 28, 12), (0, 0, t, t), 2)

        # 2. Ziemia / mur z kamyczkami 3D
        self.tex_ground = pygame.Surface((t, t))
        self.tex_ground.fill((132, 82, 46))
        pygame.draw.rect(self.tex_ground, (152, 96, 56), (3, 3, t - 6, t - 6), border_radius=3)
        for px, py, pr, col in ((10, 14, 4, (108, 64, 34)), (27, 20, 5, (102, 58, 30)), (16, 31, 4, (172, 118, 74)), (31, 33, 3, (112, 66, 36))):
            pygame.draw.circle(self.tex_ground, col, (px, py), pr)
        pygame.draw.rect(self.tex_ground, (88, 52, 26), (0, 0, t, t), 2)

        # 3. Front ziemi z zaokrąglonym zwisem trawy Super Mario 3D World!
        self.tex_grass = self.tex_ground.copy()
        pygame.draw.rect(self.tex_grass, (46, 174, 58), (0, 0, t, 12))
        pygame.draw.rect(self.tex_grass, (118, 236, 102), (0, 0, t, 4))
        for gx in range(0, t, 10):
            pygame.draw.circle(self.tex_grass, (46, 174, 58), (gx + 5, 11), 6)
            pygame.draw.arc(self.tex_grass, (28, 112, 36), (gx - 1, 5, 12, 12), math.pi, math.tau, 2)

        # 4. Zielona rura 3D z gładkim cylindrycznym połyskiem
        self.tex_pipe = pygame.Surface((t, t))
        bands = [
            (0, 5, (24, 120, 38)),
            (5, 6, (56, 192, 70)),
            (11, 5, (115, 236, 118)),
            (16, 4, (192, 255, 190)),
            (20, 8, (54, 186, 68)),
            (28, 7, (30, 138, 46)),
            (35, 5, (16, 88, 28)),
        ]
        for bx, bw, col in bands:
            pygame.draw.rect(self.tex_pipe, col, (bx, 0, bw, t))
        pygame.draw.rect(self.tex_pipe, (12, 64, 20), (0, 0, t, t), 2)

        # 5. Zużyty blok '?' 3D
        self.tex_q_used = pygame.Surface((t, t))
        self.tex_q_used.fill((120, 100, 84))
        pygame.draw.rect(self.tex_q_used, (144, 122, 102), (3, 3, t - 6, t - 6), border_radius=4)
        for nx, ny in ((6, 6), (t - 7, 6), (6, t - 7), (t - 7, t - 7)):
            pygame.draw.circle(self.tex_q_used, (72, 58, 44), (nx, ny), 2)
        pygame.draw.rect(self.tex_q_used, (64, 50, 38), (0, 0, t, t), 2, border_radius=4)

        self.shadow_strip = pygame.Surface((t, 12), pygame.SRCALPHA)
        pygame.draw.rect(self.shadow_strip, (12, 22, 42, 68), (0, 0, t, 9), border_radius=3)

    def _build_sky_surface(self):
        """Tworzy bogate, głębokie tło w stylu Super Mario 3D World."""
        self.sky_surf = pygame.Surface((WORLD_W, WORLD_H))
        for y in range(WORLD_H):
            t = y / WORLD_H
            col = (
                int(68 + (182 - 68) * t),
                int(162 + (234 - 162) * t),
                int(255 + (255 - 255) * t),
            )
            pygame.draw.line(self.sky_surf, col, (0, y), (WORLD_W, y))

        # Słońce z ciepłą koroną światła
        sun_x, sun_y = 1360, 128
        glow = pygame.Surface((280, 280), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 246, 170, 42), (140, 140), 130)
        pygame.draw.circle(glow, (255, 240, 128, 82), (140, 140), 82)
        self.sky_surf.blit(glow, (sun_x - 140, sun_y - 140))
        pygame.draw.circle(self.sky_surf, (255, 238, 108), (sun_x, sun_y), 46)
        pygame.draw.circle(self.sky_surf, (255, 252, 195), (sun_x - 10, sun_y - 10), 22)

        # Latające wysepki 3D w oddali (jak w Super Mario 3D World / Galaxy!)
        for ix, iy, iw in ((300, 295, 90), (1080, 245, 110)):
            # Stożek skalny pod wyspą
            pts = [(ix - iw // 2, iy), (ix + iw // 2, iy), (ix + iw // 5, iy + 46), (ix - iw // 4, iy + 36)]
            pygame.draw.polygon(self.sky_surf, (152, 120, 95), pts)
            pygame.draw.polygon(self.sky_surf, (120, 92, 70), [(ix, iy), (ix + iw // 2, iy), (ix + iw // 5, iy + 46)])
            # Zielony owalny wierzch 3D wyspy
            pygame.draw.ellipse(self.sky_surf, (78, 198, 92), (ix - iw // 2 - 4, iy - 12, iw + 8, 22))
            pygame.draw.ellipse(self.sky_surf, (118, 232, 122), (ix - iw // 2 + 4, iy - 10, iw - 8, 12))
            # Mini drzewko Mario 3D na wyspie
            pygame.draw.rect(self.sky_surf, (132, 86, 48), (ix - 18, iy - 34, 8, 26))
            pygame.draw.circle(self.sky_surf, (58, 178, 72), (ix - 14, iy - 42), 16)
            pygame.draw.circle(self.sky_surf, (96, 218, 102), (ix - 18, iy - 46), 9)

        # Warstwa 1 (dalekie niebieskawe góry dla głębi atmosferycznej)
        for mx, my, mw, mh in ((160, 800, 290, 295), (540, 800, 350, 345), (1020, 800, 320, 315), (1440, 800, 295, 285)):
            pygame.draw.ellipse(self.sky_surf, (122, 194, 184), (mx - mw, my - mh, mw * 2, mh * 2))

        # Warstwa 2 (gładkie cieniowane wzgórza Super Mario 3D z kropkami)
        for hx, hy, hw, hh in ((240, 800, 230, 185), (660, 800, 300, 240), (1140, 800, 255, 195), (1470, 800, 220, 165)):
            pygame.draw.ellipse(self.sky_surf, (68, 172, 82), (hx - hw, hy - hh, hw * 2, hh * 2))
            pygame.draw.ellipse(self.sky_surf, (104, 210, 108), (hx - hw + 18, hy - hh + 12, hw * 2 - 46, hh * 2 - 22))
            pygame.draw.ellipse(self.sky_surf, (138, 232, 134), (hx - 24, hy - hh + 42, 18, 28))
            pygame.draw.ellipse(self.sky_surf, (138, 232, 134), (hx + 16, hy - hh + 62, 16, 24))

        ground_y = (MAP_ROWS - 2) * TILE_SIZE

        # Zamek Chomików w stylu Super Mario 3D na wzgórzu!
        castle_x, castle_y = 660, ground_y - 175
        pygame.draw.rect(self.sky_surf, (236, 224, 206), (castle_x - 42, castle_y - 54, 84, 72))
        pygame.draw.rect(self.sky_surf, (206, 190, 170), (castle_x + 12, castle_y - 54, 30, 72))  # cień 3D boku zamku
        pygame.draw.rect(self.sky_surf, (172, 152, 132), (castle_x - 42, castle_y - 54, 84, 72), 2)
        for tx, tw, th in ((castle_x - 52, 24, 78), (castle_x + 28, 24, 78), (castle_x - 16, 32, 102)):
            pygame.draw.rect(self.sky_surf, (242, 232, 214), (tx, castle_y + 18 - th, tw, th))
            pygame.draw.rect(self.sky_surf, (208, 192, 172), (tx + tw // 2, castle_y + 18 - th, tw // 2, th))
            pygame.draw.rect(self.sky_surf, (172, 152, 132), (tx, castle_y + 18 - th, tw, th), 2)
            roof = [(tx - 4, castle_y + 18 - th), (tx + tw + 4, castle_y + 18 - th), (tx + tw // 2, castle_y - 8 - th)]
            pygame.draw.polygon(self.sky_surf, (224, 58, 66), roof)
            pygame.draw.polygon(self.sky_surf, (165, 34, 42), [(tx + tw // 2, castle_y - 8 - th), (tx + tw + 4, castle_y + 18 - th), (tx + tw // 2, castle_y + 18 - th)])
            pygame.draw.line(self.sky_surf, (120, 82, 42), (tx + tw // 2, castle_y - 8 - th), (tx + tw // 2, castle_y - 22 - th), 2)
            pygame.draw.polygon(self.sky_surf, GOLD, [(tx + tw // 2, castle_y - 22 - th), (tx + tw // 2 + 12, castle_y - 18 - th), (tx + tw // 2, castle_y - 14 - th)])
        pygame.draw.ellipse(self.sky_surf, (88, 56, 38), (castle_x - 13, castle_y - 16, 26, 36))
        pygame.draw.rect(self.sky_surf, (88, 56, 38), (castle_x - 13, castle_y, 26, 18))

        # Drewniany płotek 3D + krzaczki z kwiatuszkami
        for fx in range(420, 560, 22):
            pygame.draw.rect(self.sky_surf, (206, 156, 100), (fx, ground_y - 26, 10, 24), border_radius=2)
            pygame.draw.rect(self.sky_surf, (142, 98, 56), (fx, ground_y - 26, 10, 24), 1, border_radius=2)
        pygame.draw.rect(self.sky_surf, (190, 142, 88), (416, ground_y - 19, 152, 5))
        pygame.draw.rect(self.sky_surf, (190, 142, 88), (416, ground_y - 10, 152, 5))

        for bx in (180, 440, 740, 960, 1220, 1410):
            pygame.draw.circle(self.sky_surf, (46, 154, 62), (bx - 18, ground_y - 8), 18)
            pygame.draw.circle(self.sky_surf, (68, 192, 84), (bx, ground_y - 16), 24)
            pygame.draw.circle(self.sky_surf, (108, 224, 114), (bx - 6, ground_y - 22), 11)
            pygame.draw.circle(self.sky_surf, (46, 154, 62), (bx + 20, ground_y - 8), 18)
            pygame.draw.circle(self.sky_surf, (255, 240, 110), (bx - 8, ground_y - 15), 3)
            pygame.draw.circle(self.sky_surf, (255, 165, 195), (bx + 9, ground_y - 10), 3)

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

    def find_ground_y(self, x: float, start_y: float) -> float | None:
        """Znajduje dokładną wysokość (Y) platformy bezpośrednio pod chomikiem (dla cienia 3D!)."""
        col = int(x // TILE_SIZE)
        if col < 0 or col >= MAP_COLS:
            return None
        start_row = max(0, int(start_y // TILE_SIZE))
        for row in range(start_row, MAP_ROWS):
            if LEVEL_LAYOUT[row][col] in ("#", "B", "?", "P"):
                return float(row * TILE_SIZE)
        return None

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
        h = int(46 * scale)
        hx = sx + int(sway)
        hy = sy - h
        pygame.draw.line(surf, (44, 142, 52), (sx, sy), (hx, hy), max(2, int(4 * scale)))
        pygame.draw.ellipse(surf, (66, 178, 72), (sx - int(14 * scale), sy - h // 2, int(14 * scale), int(7 * scale)))
        pygame.draw.ellipse(surf, (66, 178, 72), (sx + int(2 * scale), sy - h // 2 - 4, int(14 * scale), int(7 * scale)))
        pr = max(3, int(5 * scale))
        dist = int(10 * scale)
        for deg in range(0, 360, 45):
            rad = math.radians(deg)
            pygame.draw.circle(surf, (255, 212, 48), (hx + int(math.cos(rad) * dist), hy + int(math.sin(rad) * dist)), pr)
        pygame.draw.circle(surf, (92, 54, 24), (hx, hy), max(4, int(8 * scale)))
        pygame.draw.circle(surf, (138, 86, 40), (hx - 2, hy - 2), max(2, int(3 * scale)))

    def _draw_3d_extrusion(
        self,
        surf: pygame.Surface,
        dx: int,
        dy: int,
        col: int,
        row: int,
        ox: int,
        oy: int,
        top_col,
        side_col,
        outline_col,
    ):
        """Rysuje 3D górną i boczną ściankę sześcianu (efekt Super Mario 3D World!)."""
        t = TILE_SIZE
        # Górna słoneczna ścianka 3D (tylko jeśli nad klockiem jest pusto)
        if not _is_solid_cell(col, row - 1):
            top_poly = [(dx, dy), (dx + t, dy), (dx + t + ox, dy + oy), (dx + ox, dy + oy)]
            pygame.draw.polygon(surf, top_col, top_poly)
            pygame.draw.polygon(surf, outline_col, top_poly, 1)

        # Boczna cieniowana ścianka głębi 3D (dynamicznie po lewej albo prawej względem środka ekranu!)
        if ox > 0 and not _is_solid_cell(col + 1, row):
            side_poly = [(dx + t, dy), (dx + t + ox, dy + oy), (dx + t + ox, dy + t + oy), (dx + t, dy + t)]
            pygame.draw.polygon(surf, side_col, side_poly)
            pygame.draw.polygon(surf, outline_col, side_poly, 1)
        elif ox < 0 and not _is_solid_cell(col - 1, row):
            side_poly = [(dx, dy), (dx + ox, dy + oy), (dx + ox, dy + t + oy), (dx, dy + t)]
            pygame.draw.polygon(surf, side_col, side_poly)
            pygame.draw.polygon(surf, outline_col, side_poly, 1)

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, elapsed: float, q_font: pygame.font.Font):
        sw = surf.get_width()
        half_sw = sw * 0.5
        oy = -10  # Podwyższona perspektywa 2.5D (patrzymy lekko z góry jak w Mario 3D World!)

        def get_ox(screen_x: int) -> int:
            return max(-9, min(9, int((half_sw - (screen_x + TILE_SIZE * 0.5)) * 0.022)))

        # 1. Tło nieba, wysp 3D, zamku i wzgórz
        surf.blit(self.sky_surf, (-int(cam_x), -int(cam_y)))

        # 1a. Obracające się złote promienie słońca
        sun_sx = int(1360 - cam_x)
        sun_sy = int(128 - cam_y)
        if -260 <= sun_sx <= sw + 260:
            ray_surf = pygame.Surface((sw, surf.get_height()), pygame.SRCALPHA)
            for i in range(6):
                a1 = elapsed * 0.14 + i * (math.pi / 3.0)
                a2 = a1 + 0.16
                p1 = (sun_sx, sun_sy)
                p2 = (sun_sx + int(math.cos(a1) * 520), sun_sy + int(math.sin(a1) * 520))
                p3 = (sun_sx + int(math.cos(a2) * 520), sun_sy + int(math.sin(a2) * 520))
                pygame.draw.polygon(ray_surf, (255, 248, 185, 22), (p1, p2, p3))
            surf.blit(ray_surf, (0, 0))

        # 1b. Puszyste chmury 3D (z jasnym wierzchem i pastelowo-niebieskim spodem)
        for cl in self.clouds:
            cx = int(cl["x"] - cam_x * 0.75)
            cy = int(cl["y"] - cam_y * 0.5)
            sc = cl["scale"]
            if -120 <= cx <= sw + 120:
                pygame.draw.ellipse(surf, (192, 224, 248), (cx - int(48 * sc), cy - int(6 * sc), int(96 * sc), int(30 * sc)))
                pygame.draw.ellipse(surf, (242, 250, 255), (cx - int(46 * sc), cy - int(16 * sc), int(92 * sc), int(34 * sc)))
                pygame.draw.ellipse(surf, (255, 255, 255), (cx - int(30 * sc), cy - int(29 * sc), int(60 * sc), int(42 * sc)))

        # 1c. Kołyszące się słoneczniki na trawiastej łące 3D
        for fx, fy, fsc in self.bg_sunflowers:
            sx = int(fx - cam_x)
            sy = int(fy - cam_y) - 10
            if -40 <= sx <= sw + 40:
                sway = math.sin(elapsed * 2.2 + fx * 0.02) * 5.0 * fsc
                self._draw_bg_sunflower(surf, sx, sy, fsc, sway)

        view = pygame.Rect(int(cam_x) - 60, int(cam_y) - 60, sw + 120, surf.get_height() + 120)
        top_floor_y = (MAP_ROWS - 2) * TILE_SIZE

        # --- WARSTWA 2.5D: Trawiasta łąka w szachownicę 3D (ikoniczny styl Super Mario 3D World!) ---
        floor_dy = top_floor_y - int(cam_y)
        if -40 <= floor_dy <= surf.get_height() + 40:
            for c in range(1, MAP_COLS - 1):
                dx = c * TILE_SIZE - int(cam_x)
                if dx < -TILE_SIZE or dx > sw + TILE_SIZE:
                    continue
                ox = get_ox(dx)
                g_col = (94, 214, 96) if c % 2 == 0 else (72, 192, 78)
                top_poly = [(dx, floor_dy), (dx + TILE_SIZE, floor_dy), (dx + TILE_SIZE + ox, floor_dy - 14), (dx + ox, floor_dy - 14)]
                pygame.draw.polygon(surf, g_col, top_poly)
                # Drugi, głębszy pas szachownicy 3D
                g_col2 = (72, 192, 78) if c % 2 == 0 else (94, 214, 96)
                back_poly = [(dx + ox, floor_dy - 14), (dx + TILE_SIZE + ox, floor_dy - 14), (dx + TILE_SIZE + ox * 2, floor_dy - 24), (dx + ox * 2, floor_dy - 24)]
                pygame.draw.polygon(surf, g_col2, back_poly)

        # --- PASS 1: 3D Głębia wszystkich cegieł i bloków '?' (górne i boczne ścianki) ---
        for r in self.brick_rects:
            if not view.colliderect(r):
                continue
            dx, dy = r.x - int(cam_x), r.y - int(cam_y)
            ox = get_ox(dx)
            surf.blit(self.shadow_strip, (dx + 4, dy + TILE_SIZE))
            self._draw_3d_extrusion(
                surf, dx, dy, r.x // TILE_SIZE, r.y // TILE_SIZE, ox, oy,
                top_col=(96, 214, 92), side_col=(142, 60, 28), outline_col=(68, 34, 16)
            )

        for qb in self.question_blocks:
            if not view.colliderect(qb.rect):
                continue
            dx = qb.rect.x - int(cam_x)
            dy = qb.rect.y - int(cam_y) + int(qb.bump_offset)
            ox = get_ox(dx)
            surf.blit(self.shadow_strip, (dx + 4, dy + TILE_SIZE))
            t_col = (255, 232, 108) if qb.active else (154, 134, 114)
            s_col = (182, 122, 18) if qb.active else (92, 76, 62)
            self._draw_3d_extrusion(surf, dx, dy, qb.col, qb.row, ox, oy, t_col, s_col, (112, 68, 12))

        # --- PASS 2: Frontowe ściany 3D (ziemia, cegły, rury z otworem 3D, bloki '?') ---
        for r in self.ground_rects:
            if not view.colliderect(r):
                continue
            dx, dy = r.x - int(cam_x), r.y - int(cam_y)
            surf.blit(self.tex_grass if r.y == top_floor_y else self.tex_ground, (dx, dy))

        for r in self.brick_rects:
            if not view.colliderect(r):
                continue
            dx, dy = r.x - int(cam_x), r.y - int(cam_y)
            surf.blit(self.tex_brick, (dx, dy))

        # Zielone rury Mario 3D z trójwymiarowym eliptycznym otworem u góry!
        for r in self.pipe_rects:
            if not view.colliderect(r):
                continue
            dx, dy = r.x - int(cam_x), r.y - int(cam_y)
            surf.blit(self.tex_pipe, (dx, dy))
            row_above = (r.y // TILE_SIZE) - 1
            col = r.x // TILE_SIZE
            if row_above >= 0 and LEVEL_LAYOUT[row_above][col] != "P":
                rim = pygame.Rect(dx - 5, dy, r.w + 10, 15)
                pygame.draw.rect(surf, (44, 182, 64), rim, border_radius=4)
                pygame.draw.rect(surf, (176, 255, 176), (rim.x + 11, rim.y + 2, 7, rim.h - 4))
                pygame.draw.rect(surf, (18, 98, 30), (rim.right - 9, rim.y + 2, 7, rim.h - 4))
                pygame.draw.rect(surf, (12, 64, 20), rim, 2, border_radius=4)
                # 3D eliptyczny wierzch rury i ciemna głębia tunelu w środku!
                oval_top = pygame.Rect(dx - 5, dy - 8, r.w + 10, 14)
                pygame.draw.ellipse(surf, (92, 224, 98), oval_top)
                pygame.draw.ellipse(surf, (12, 64, 20), oval_top, 2)
                hole = pygame.Rect(dx + 3, dy - 5, r.w - 6, 8)
                pygame.draw.ellipse(surf, (10, 44, 18), hole)
                pygame.draw.line(surf, (14, 72, 24), (dx, dy + 15), (dx + r.w, dy + 15), 3)

        # Złote sześciany '?' 3D
        pulse = int(math.sin(elapsed * 5.5) * 14)
        gleam_pos = (elapsed * 38.0) % 72.0
        for qb in self.question_blocks:
            if not view.colliderect(qb.rect):
                continue
            dx = qb.rect.x - int(cam_x)
            dy = qb.rect.y - int(cam_y) + int(qb.bump_offset)
            dr = pygame.Rect(dx, dy, qb.rect.w, qb.rect.h)
            if qb.active:
                col = (min(255, 245 + pulse), min(255, 192 + pulse), 36)
                pygame.draw.rect(surf, col, dr, border_radius=5)
                pygame.draw.rect(surf, (255, 246, 168), (dr.x + 3, dr.y + 3, dr.w - 6, 7), border_radius=3)
                if gleam_pos < 36.0:
                    gx = int(gleam_pos)
                    pygame.draw.line(surf, (255, 255, 232), (dr.x + gx, dr.y + 4), (dr.x + max(4, gx - 8), dr.bottom - 5), 3)
                for nx, ny in ((dr.x + 6, dr.y + 6), (dr.right - 7, dr.y + 6), (dr.x + 6, dr.bottom - 7), (dr.right - 7, dr.bottom - 7)):
                    pygame.draw.circle(surf, (152, 92, 14), (nx, ny), 2)
                pygame.draw.rect(surf, (142, 82, 10), dr, 3, border_radius=5)
                q_sh = q_font.render("?", True, (124, 62, 8))
                q_fg = q_font.render("?", True, (255, 252, 232))
                qx = dr.centerx - q_fg.get_width() // 2
                qy = dr.centery - q_fg.get_height() // 2
                surf.blit(q_sh, (qx + 2, qy + 2))
                surf.blit(q_fg, (qx, qy))
            else:
                surf.blit(self.tex_q_used, (dx, dy))
                prog = 1.0 - (qb.cooldown / 12.0)
                pygame.draw.rect(surf, GOLD, (dr.x + 4, dr.bottom - 6, int((dr.w - 8) * prog), 3))

        # Grzybki-trampoliny 3D z wypukłym połyskiem kopuły
        for sp in self.springs:
            if not view.colliderect(sp):
                continue
            dr = pygame.Rect(sp.x - int(cam_x), sp.y - int(cam_y), sp.w, sp.h)
            pygame.draw.ellipse(surf, (20, 42, 24), (dr.x + 2, dr.bottom - 5, dr.w - 4, 7))
            pygame.draw.rect(surf, (245, 232, 200), (dr.centerx - 8, dr.y + 8, 16, dr.h - 9), border_radius=4)
            pygame.draw.rect(surf, (212, 194, 158), (dr.centerx + 1, dr.y + 8, 7, dr.h - 9), border_radius=3)
            cap = pygame.Rect(dr.x - 6, dr.y - 2, dr.w + 12, 17)
            pygame.draw.ellipse(surf, (218, 34, 44), cap)
            pygame.draw.ellipse(surf, (252, 96, 102), (cap.x + 5, cap.y + 2, cap.w - 14, 7))
            pygame.draw.circle(surf, (255, 255, 255), (cap.x + 11, cap.y + 8), 3)
            pygame.draw.circle(surf, (255, 255, 255), (cap.centerx, cap.y + 6), 3)
            pygame.draw.circle(surf, (255, 255, 255), (cap.right - 11, cap.y + 8), 3)
            pygame.draw.ellipse(surf, (124, 16, 22), cap, 2)

        # Złote pyłki słonecznika dryfujące po całej arenie
        for m in self.ambient_motes:
            mx = int(m["x"] - cam_x)
            my = int(m["y"] + math.sin(m["phase"]) * 8.0 - cam_y)
            if 0 <= mx <= sw and 0 <= my <= surf.get_height():
                pygame.draw.circle(surf, m["col"], (mx, my), m["r"])
