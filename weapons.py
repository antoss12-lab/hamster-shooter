"""
weapons.py — Pociski ze smugami, błyski z lufy, wyrzucane łuski, fale uderzeniowe
oraz szczegółowe rysowanie 4 broni (na chomiku i jako ikonki w HUD).
"""

import math
import random
import pygame
from settings import WEAPONS, GOLD, WHITE, SUNFLOWER_DARK, SUNFLOWER_LIGHT


class Bullet:
    """Pojedynczy pocisk z gładką, świecącą smugą."""

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
        self.max_trail = 11 if weapon_id == "awp" else (5 if weapon_id != "shotgun" else 4)

    def update(self, dt: float, level):
        self.prev_x, self.prev_y = self.x, self.y
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            return

        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

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

        if len(self.trail) >= 2:
            pts = [(int(px - cam_x), int(py - cam_y)) for px, py in self.trail]
            if self.weapon_id == "awp":
                pygame.draw.lines(surf, (255, 110, 75), False, pts, 6)
                pygame.draw.lines(surf, (255, 232, 140), False, pts, 3)
                pygame.draw.lines(surf, WHITE, False, pts, 1)
            else:
                pygame.draw.lines(surf, self.color, False, pts, 3 if self.weapon_id != "shotgun" else 2)

        if self.weapon_id == "ziarna":
            dx = math.cos(self.angle) * 6
            dy = math.sin(self.angle) * 6
            pygame.draw.line(surf, SUNFLOWER_DARK, (sx - dx, sy - dy), (sx + dx, sy + dy), 6)
            pygame.draw.line(surf, SUNFLOWER_LIGHT, (sx - dx * 0.6, sy - dy * 0.6), (sx + dx * 0.6, sy + dy * 0.6), 2)
        elif self.weapon_id == "awp":
            pygame.draw.circle(surf, (255, 195, 95), (sx, sy), 7)
            pygame.draw.circle(surf, WHITE, (sx, sy), 4)
        else:
            pygame.draw.circle(surf, self.color, (sx, sy), self.radius + 1)
            pygame.draw.circle(surf, WHITE, (sx, sy), max(2, self.radius - 1))


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


class ShockwaveRing:
    """Rozchodzący się pierścień światła (przy podwójnym skoku, sprężynie, trafieniu lub pokonaniu!)."""

    def __init__(self, x: float, y: float, color, max_radius: float = 34.0, life: float = 0.28, width: int = 3):
        self.x = x
        self.y = y
        self.color = color
        self.max_radius = max_radius
        self.life = life
        self.max_life = life
        self.width = width

    def update(self, dt: float):
        self.life -= dt

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        if self.life <= 0:
            return
        prog = 1.0 - (self.life / self.max_life)
        r = max(3, int(6 + (self.max_radius - 6) * prog))
        alpha = max(0, min(255, int(215 * (1.0 - prog))))
        s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        w = max(1, int(self.width * (1.0 - prog * 0.5)))
        pygame.draw.circle(s, (self.color[0], self.color[1], self.color[2], alpha), (r + 2, r + 2), r, w)
        surf.blit(s, (int(self.x - cam_x) - r - 2, int(self.y - cam_y) - r - 2))


class MuzzleFlash:
    """Krótki, efektowny błysk gwiazdki przy końcu lufy podczas strzału."""

    def __init__(self, x: float, y: float, angle: float, color, size: float = 13.0):
        self.x = x
        self.y = y
        self.angle = angle
        self.color = color
        self.size = size
        self.life = 0.075
        self.max_life = 0.075

    def update(self, dt: float):
        self.life -= dt

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r = max(3, int(self.size * ratio))
        # Złota poświata + 4-ramienna gwiazdka
        pts = []
        for i in range(8):
            ang = self.angle + i * (math.pi / 4)
            rad = r * (1.45 if i % 2 == 0 else 0.45)
            pts.append((sx + int(math.cos(ang) * rad), sy + int(math.sin(ang) * rad)))
        pygame.draw.polygon(surf, self.color, pts)
        pygame.draw.circle(surf, WHITE, (sx, sy), max(2, r // 2))


class ShellCasing:
    """Obracająca się mosiężna łuska lub łupinka wylatująca z broni podczas strzelania."""

    def __init__(self, x: float, y: float, facing_right: bool, weapon_id: str):
        self.x = x
        self.y = y
        d = -1 if facing_right else 1
        self.vx = d * random.uniform(60, 130)
        self.vy = random.uniform(-190, -110)
        self.angle = random.uniform(0, math.tau)
        self.spin = random.uniform(-14, 14)
        self.color = (225, 65, 55) if weapon_id == "shotgun" else ((235, 200, 95) if weapon_id != "ziarna" else SUNFLOWER_LIGHT)
        self.life = 0.75
        self.max_life = 0.75

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 680.0 * dt
        self.angle += self.spin * dt
        self.life -= dt

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        if self.life <= 0:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        dx = int(math.cos(self.angle) * 3.5)
        dy = int(math.sin(self.angle) * 3.5)
        pygame.draw.line(surf, self.color, (sx - dx, sy - dy), (sx + dx, sy + dy), 3)


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
        pygame.draw.line(surf, (115, 72, 36), pt(2, 4), pt(7, 9), 5)
        pygame.draw.line(surf, (135, 86, 44), pt(3), pt(22), 8)
        pygame.draw.line(surf, (245, 206, 78), pt(8, -1), pt(23, -1), 4)
        pygame.draw.circle(surf, (255, 242, 165), pt(12, -2), 2)
        pygame.draw.circle(surf, (68, 48, 28), pt(23), 4)
    elif weapon_id == "karabin":
        pygame.draw.line(surf, (145, 92, 46), pt(-2, 1), pt(10, 1), 7)
        pygame.draw.line(surf, (44, 48, 58), pt(8), pt(29), 7)
        pygame.draw.line(surf, (120, 130, 148), pt(9, -2), pt(26, -2), 2)
        pygame.draw.line(surf, (32, 35, 42), pt(15, 2), pt(17, 9), 4)
        pygame.draw.line(surf, (255, 195, 70), pt(28), pt(31), 3)
    elif weapon_id == "shotgun":
        pygame.draw.line(surf, (128, 74, 38), pt(-1, 2), pt(10, 1), 8)
        pygame.draw.line(surf, (52, 56, 66), pt(8), pt(27), 9)
        pygame.draw.line(surf, (140, 148, 165), pt(9, -2), pt(26, -2), 2)
        pygame.draw.line(surf, (238, 125, 42), pt(13, 2), pt(21, 2), 6)
    elif weapon_id == "awp":
        pygame.draw.line(surf, (56, 118, 62), pt(-2, 1), pt(22, 0), 8)
        pygame.draw.line(surf, (92, 162, 96), pt(0, -2), pt(20, -2), 2)
        pygame.draw.line(surf, (36, 40, 48), pt(20), pt(39), 4)
        pygame.draw.line(surf, (24, 28, 35), pt(37), pt(41), 6)
        pygame.draw.line(surf, (26, 30, 38), pt(7, -6), pt(22, -6), 5)
        pygame.draw.circle(surf, (95, 220, 255), pt(22, -6), 2)
        pygame.draw.circle(surf, (255, 55, 55), pt(41), 2)


def draw_weapon_icon(surf: pygame.Surface, cx: int, cy: int, weapon_id: str):
    """Rysuje małą ikonkę broni w pasku HUD na dole ekranu."""
    draw_weapon_on_hamster(surf, cx - 16, cy, -0.12, weapon_id)
