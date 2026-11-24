"""
weapons.py — Pociski, efekty cząsteczkowe i latające teksty obrażeń.
"""

import math
import random
import pygame
from settings import WEAPONS, GOLD, WHITE, SUNFLOWER_DARK, SUNFLOWER_LIGHT


class Bullet:
    """Pojedynczy pocisk wystrzelony przez gracza lub bota."""

    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        weapon_id: str,
        owner,
        damage_mult: float = 1.0,
    ):
        spec = WEAPONS[weapon_id]
        self.x = x
        self.y = y
        self.prev_x = x
        self.prev_y = y
        self.angle = angle
        self.weapon_id = weapon_id
        self.owner = owner
        self.speed = spec["speed"]
        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed
        self.damage = int(spec["damage"] * damage_mult)
        self.color = spec["color"]
        self.radius = 5 if weapon_id == "ziarna" else (4 if weapon_id == "karabin" else (3 if weapon_id == "shotgun" else 5))
        self.lifetime = 1.5 if weapon_id != "shotgun" else 0.55
        self.alive = True
        self.trail: list[tuple[float, float]] = [(x, y)]

    def update(self, dt: float, level):
        self.prev_x, self.prev_y = self.x, self.y
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            return

        if self.weapon_id == "awp":
            self.trail.append((self.x, self.y))
            if len(self.trail) > 9:
                self.trail.pop(0)

        # Sprawdź kolizję ze ścianami i platformami (dla szybkiego AWP sprawdzamy też punkt w połowie)
        if self.weapon_id == "awp":
            mid_x = (self.prev_x + self.x) * 0.5
            mid_y = (self.prev_y + self.y) * 0.5
            if level.point_hits_solid(mid_x, mid_y):
                self.x, self.y = mid_x, mid_y
                self.alive = False
                return

        if level.point_hits_solid(self.x, self.y):
            self.alive = False

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        if self.weapon_id == "ziarna":
            # Ładnie narysowane ziarenko słonecznika lecące w powietrzu!
            dx = math.cos(self.angle) * 6
            dy = math.sin(self.angle) * 6
            pygame.draw.line(surf, SUNFLOWER_DARK, (sx - dx, sy - dy), (sx + dx, sy + dy), 6)
            pygame.draw.line(surf, SUNFLOWER_LIGHT, (sx - dx * 0.6, sy - dy * 0.6), (sx + dx * 0.6, sy + dy * 0.6), 2)
        elif self.weapon_id == "awp":
            # Jasna smuga snajperska AWP
            if len(self.trail) >= 2:
                pts = [(int(px - cam_x), int(py - cam_y)) for px, py in self.trail]
                pygame.draw.lines(surf, (255, 220, 120), False, pts, 4)
                pygame.draw.lines(surf, WHITE, False, pts, 2)
            pygame.draw.circle(surf, (255, 80, 80), (sx, sy), 5)
        else:
            # Pociski karabinu i shotguna
            tx = int(self.x - math.cos(self.angle) * 10 - cam_x)
            ty = int(self.y - math.sin(self.angle) * 10 - cam_y)
            pygame.draw.line(surf, self.color, (tx, ty), (sx, sy), 4)
            pygame.draw.circle(surf, WHITE, (sx, sy), self.radius - 1)


class Particle:
    """Mała cząsteczka (dymek przy podwójnym skoku, iskry, konfetti)."""

    def __init__(self, x: float, y: float, vx: float, vy: float, color, radius: float, life: float, gravity: float = 300.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = radius
        self.life = life
        self.max_life = life
        self.gravity = gravity

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        if self.life <= 0:
            return
        ratio = max(0.0, self.life / self.max_life)
        r = max(1, int(self.radius * ratio))
        pygame.draw.circle(surf, self.color, (int(self.x - cam_x), int(self.y - cam_y)), r)


class FloatingText:
    """Latający napis nad miejscem zdarzenia (np. '-88!', '+1 Ziarno', 'TARCZA!')."""

    def __init__(self, x: float, y: float, text: str, color=GOLD, life: float = 0.85):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = life
        self.max_life = life

    def update(self, dt: float):
        self.y -= 48 * dt
        self.life -= dt

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, font: pygame.font.Font):
        if self.life <= 0:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        shadow = font.render(self.text, True, (20, 20, 20))
        img = font.render(self.text, True, self.color)
        surf.blit(shadow, (sx - img.get_width() // 2 + 1, sy + 1))
        surf.blit(img, (sx - img.get_width() // 2, sy))


def spawn_burst(particles: list[Particle], x: float, y: float, color, count: int = 8, speed: float = 180.0):
    """Tworzy małą eksplozję cząsteczek w punkcie (x, y)."""
    for _ in range(count):
        ang = random.uniform(0, math.tau)
        spd = random.uniform(speed * 0.35, speed)
        particles.append(
            Particle(
                x,
                y,
                math.cos(ang) * spd,
                math.sin(ang) * spd - 40,
                color,
                random.uniform(3, 6),
                random.uniform(0.25, 0.55),
            )
        )


def draw_weapon_on_hamster(surf: pygame.Surface, cx: int, cy: int, angle: float, weapon_id: str):
    """Rysuje szczegółową broń z połyskiem obracającą się w stronę kursora myszy."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    flip = -1 if cos_a < 0 else 1
    perp_x = -sin_a * flip
    perp_y = cos_a * flip

    def pt(fwd: float, side: float = 0.0) -> tuple[int, int]:
        return (int(cx + cos_a * fwd + perp_x * side), int(cy + sin_a * fwd + perp_y * side))

    if weapon_id == "ziarna":
        # Miotacz Ziaren — drewniany uchwyt, złota lufa i komora na słonecznik
        pygame.draw.line(surf, (115, 72, 36), pt(2, 4), pt(7, 9), 5)  # rękojeść
        pygame.draw.line(surf, (135, 86, 44), pt(3), pt(22), 8)
        pygame.draw.line(surf, (245, 206, 78), pt(8, -1), pt(23, -1), 4)
        pygame.draw.circle(surf, (255, 242, 165), pt(12, -2), 2)
        pygame.draw.circle(surf, (68, 48, 28), pt(23), 4)
    elif weapon_id == "karabin":
        # Karabin Chomik-AR — kolba, magazynek bananowy, szyna celownicza i metaliczny blik
        pygame.draw.line(surf, (145, 92, 46), pt(-2, 1), pt(10, 1), 7)  # kolba
        pygame.draw.line(surf, (44, 48, 58), pt(8), pt(29), 7)         # korpus i lufa
        pygame.draw.line(surf, (120, 130, 148), pt(9, -2), pt(26, -2), 2)  # połysk
        pygame.draw.line(surf, (32, 35, 42), pt(15, 2), pt(17, 9), 4)  # magazynek
        pygame.draw.line(surf, (255, 195, 70), pt(28), pt(31), 3)      # końcówka lufy
    elif weapon_id == "shotgun":
        # Shotgun Orzechowy — szeroka podwójna lufa, kolba i pomarańczowa pompka
        pygame.draw.line(surf, (128, 74, 38), pt(-1, 2), pt(10, 1), 8)  # kolba
        pygame.draw.line(surf, (52, 56, 66), pt(8), pt(27), 9)          # gruba lufa
        pygame.draw.line(surf, (140, 148, 165), pt(9, -2), pt(26, -2), 2)
        pygame.draw.line(surf, (238, 125, 42), pt(13, 2), pt(21, 2), 6)  # pompka
    elif weapon_id == "awp":
        # Snajperka AWP — oliwkowy korpus, luneta ze szkiełkiem, długa lufa i hamulec wylotowy
        pygame.draw.line(surf, (56, 118, 62), pt(-2, 1), pt(22, 0), 8)
        pygame.draw.line(surf, (92, 162, 96), pt(0, -2), pt(20, -2), 2)
        pygame.draw.line(surf, (36, 40, 48), pt(20), pt(39), 4)         # długa lufa
        pygame.draw.line(surf, (24, 28, 35), pt(37), pt(41), 6)         # hamulec wylotowy
        pygame.draw.line(surf, (26, 30, 38), pt(7, -6), pt(22, -6), 5)  # luneta
        pygame.draw.circle(surf, (95, 220, 255), pt(22, -6), 2)         # szkiełko lunety
        pygame.draw.circle(surf, (255, 55, 55), pt(41), 2)              # laser
