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
    """Rysuje aktualnie trzymaną broń obracającą się w stronę kursora myszy."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    # Wektor prostopadły do lufy (do rysowania detali broni)
    perp_x = -sin_a
    perp_y = cos_a

    def pt(fwd: float, side: float = 0.0) -> tuple[int, int]:
        return (int(cx + cos_a * fwd + perp_x * side), int(cy + sin_a * fwd + perp_y * side))

    if weapon_id == "ziarna":
        # Miotacz Ziaren (drewniano-złota wyrzutnia)
        pygame.draw.line(surf, (130, 85, 45), pt(4), pt(22), 7)
        pygame.draw.line(surf, (240, 200, 75), pt(10), pt(23), 4)
        pygame.draw.circle(surf, (95, 65, 35), pt(23), 4)
    elif weapon_id == "karabin":
        # Karabin Chomik-AR
        pygame.draw.line(surf, (55, 60, 70), pt(2), pt(28), 6)
        pygame.draw.line(surf, (145, 95, 50), pt(2), pt(11), 6)
        pygame.draw.line(surf, (35, 38, 45), pt(14, 0), pt(15, 7), 4)  # magazynek
    elif weapon_id == "shotgun":
        # Shotgun Orzechowy (krótki, gruby)
        pygame.draw.line(surf, (125, 72, 38), pt(2), pt(12), 7)
        pygame.draw.line(surf, (70, 75, 85), pt(10), pt(26), 8)
        pygame.draw.line(surf, (230, 120, 45), pt(13), pt(19), 5)  # pompka
    elif weapon_id == "awp":
        # Snajperka AWP (długa, zielona z lunetą!)
        pygame.draw.line(surf, (60, 115, 65), pt(0), pt(22), 7)
        pygame.draw.line(surf, (40, 45, 52), pt(20), pt(38), 4)  # długa lufa
        pygame.draw.line(surf, (30, 35, 42), pt(9, -6), pt(21, -6), 4)  # luneta
        pygame.draw.circle(surf, (255, 60, 60), pt(38), 2)  # końcówka lasera
