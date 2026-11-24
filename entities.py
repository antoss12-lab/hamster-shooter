"""
entities.py — Postacie i obiekty na arenie:
- SunflowerSeed (ziarna słonecznika do zbierania),
- PowerUp (bonusy: szybkość, tarcza, apteczka, podwójne obrażenia),
- Hamster (Gracz oraz 7 atakujących botów z podwójnym skokiem, skórkami i SI),
- StoryBot (boty fabularne NPC, z którymi można rozmawiać klawiszem E).
"""

import math
import random
import pygame
from settings import (
    GRAVITY,
    MAX_FALL_SPEED,
    PLAYER_SPEED,
    JUMP_SPEED,
    DOUBLE_JUMP_SPEED,
    SPRING_JUMP_SPEED,
    BOT_DAMAGE_MULT,
    DIFFICULTIES,
    WEAPONS,
    SKINS,
    POWERUP_TYPES,
    GOLD,
    WHITE,
    RED,
    GREEN,
    BLUE,
    SUNFLOWER_DARK,
    SUNFLOWER_LIGHT,
)
from weapons import Bullet, Particle, ShockwaveRing, MuzzleFlash, ShellCasing, FloatingText, spawn_burst, draw_weapon_on_hamster


class SunflowerSeed:
    """Ziarno słonecznika leżące na mapie lub wypadające z bloków '?' i botów."""

    def __init__(self, x: float, y: float, vx: float = 0.0, vy: float = -180.0, value: int = 1):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.value = value
        self.alive = True
        self.age = random.uniform(0, 6.28)
        self.rect = pygame.Rect(int(x - 10), int(y - 10), 20, 20)

    def update(self, dt: float, level):
        self.age += dt
        self.vy = min(MAX_FALL_SPEED, self.vy + GRAVITY * 0.65 * dt)
        self.vx *= max(0.0, 1.0 - 4.0 * dt)

        # Ruch w poziomie
        self.x += self.vx * dt
        self.rect.center = (int(self.x), int(self.y))
        for solid in level.solids:
            if self.rect.colliderect(solid):
                if self.vx > 0:
                    self.rect.right = solid.left
                elif self.vx < 0:
                    self.rect.left = solid.right
                self.x = self.rect.centerx
                self.vx *= -0.4

        # Ruch w pionie
        self.y += self.vy * dt
        self.rect.center = (int(self.x), int(self.y))
        for solid in level.solids:
            if self.rect.colliderect(solid):
                if self.vy > 0:
                    self.rect.bottom = solid.top
                    self.vy = 0.0
                elif self.vy < 0:
                    self.rect.top = solid.bottom
                    self.vy = 0.0
                self.y = self.rect.centery

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float):
        bob = math.sin(self.age * 5.0) * 3.5
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob)

        # Efekt obrotu 3D jak złote monety w Super Mario 3D World!
        spin_w = max(2, int(abs(math.cos(self.age * 4.2)) * 6.5))
        glow_r = 12 + int(math.sin(self.age * 7.0) * 2)
        glow = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 225, 80, 82), (glow_r + 2, glow_r + 2), glow_r)
        surf.blit(glow, (sx - glow_r - 2, sy - glow_r - 2))
        # Złota krawędź głębi 3D obracającego się ziarna
        pygame.draw.ellipse(surf, (235, 178, 35), (sx - spin_w - 1, sy - 9, spin_w * 2 + 3, 18))
        pygame.draw.ellipse(surf, SUNFLOWER_DARK, (sx - spin_w, sy - 9, spin_w * 2, 18))
        if spin_w >= 3:
            pygame.draw.ellipse(surf, SUNFLOWER_LIGHT, (sx - spin_w // 2, sy - 7, max(2, spin_w), 14))
        pygame.draw.circle(surf, WHITE, (sx - max(1, spin_w // 3), sy - 4), 2)


class PowerUp:
    """Kolorowy power-up wyskakujący z bloków '?' lub pojawiający się na mapie."""

    def __init__(self, x: float, y: float, kind: str):
        self.x = x
        self.y = y
        self.vy = -260.0
        self.kind = kind
        self.alive = True
        self.age = 0.0
        self.rect = pygame.Rect(int(x - 14), int(y - 14), 28, 28)

    def update(self, dt: float, level):
        self.age += dt
        self.vy = min(MAX_FALL_SPEED, self.vy + GRAVITY * 0.6 * dt)
        self.y += self.vy * dt
        self.rect.center = (int(self.x), int(self.y))
        for solid in level.solids:
            if self.rect.colliderect(solid):
                if self.vy > 0:
                    self.rect.bottom = solid.top
                    self.vy = 0.0
                elif self.vy < 0:
                    self.rect.top = solid.bottom
                    self.vy = 0.0
                self.y = self.rect.centery

        # Po 20 sekundach niepodniesiony power-up znika
        if self.age > 20.0:
            self.alive = False

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, font: pygame.font.Font):
        info = POWERUP_TYPES[self.kind]
        bob = math.sin(self.age * 6.0) * 4.0
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob)
        col = info["color"]

        # Świecąca aura i szklany połysk power-upa
        glow = pygame.Surface((46, 46), pygame.SRCALPHA)
        pygame.draw.circle(glow, (col[0], col[1], col[2], 70), (23, 23), 21 + int(math.sin(self.age * 7) * 2))
        surf.blit(glow, (sx - 23, sy - 23))
        pygame.draw.circle(surf, WHITE, (sx, sy), 16)
        pygame.draw.circle(surf, col, (sx, sy), 14)
        pygame.draw.ellipse(surf, (255, 255, 255), (sx - 8, sy - 12, 12, 5))
        pygame.draw.circle(surf, (30, 30, 40), (sx, sy), 16, 2)
        txt = font.render(info["symbol"], True, (20, 20, 28))
        surf.blit(txt, (sx - txt.get_width() // 2, sy - txt.get_height() // 2))


def draw_hamster_avatar(
    surf: pygame.Surface,
    cx: int,
    cy: int,
    skin_id: str,
    facing_right: bool,
    aim_angle: float,
    body_override=None,
    scale: float = 1.0,
    bob_y: float = 0.0,
    hat_override: str | None = None,
    walk_phase: float = 0.0,
):
    """Rysuje uroczego chomika wraz ze skórką, ogonkiem, cieniowaniem 3D i ruszającymi się łapkami."""
    skin = SKINS.get(skin_id, SKINS["klasyczny"])
    body_col = body_override if body_override is not None else skin["body"]
    belly_col = skin["belly"]
    ear_col = skin["ear"]
    accent = skin["accent"]

    r = int(17 * scale)
    cy = int(cy + bob_y)
    d = 1 if facing_right else -1

    def s(v: float) -> int:
        return int(round(v * scale))

    # Uroczy puszysty ogonek chomika z tyłu!
    tail_bob = int(math.sin(walk_phase * 2.0) * 2.0 * scale)
    pygame.draw.circle(surf, belly_col, (cx - d * s(16), cy + s(8) + tail_bob), max(3, s(4.5)))
    pygame.draw.circle(surf, (40, 30, 25), (cx - d * s(16), cy + s(8) + tail_bob), max(3, s(4.5)), 1)

    # Peleryny (za plecami) dla Króla, Wampira i Super-Chomika
    if hat_override is None and skin_id in ("krol", "wampir", "superbohater"):
        cape_col = (40, 22, 48) if skin_id == "wampir" else accent
        cape_pts = [
            (cx - d * s(8), cy - s(6)),
            (cx - d * s(24), cy + s(16)),
            (cx - d * s(6), cy + s(16)),
        ]
        pygame.draw.polygon(surf, cape_col, cape_pts)
        if skin_id == "wampir":
            pygame.draw.polygon(surf, accent, cape_pts, 2)

    # Uszka chomika (specjalne kształty dla kota, psa, królika, pandy!)
    ear_off_x = s(10)
    ear_off_y = s(13)
    ear_r = s(6)
    ear_outer = (32, 34, 40) if skin_id == "panda" else body_col
    if hat_override is None and skin_id == "kroliczek":
        # Długie stojące uszy królika!
        for side in (-1, 1):
            ex = cx + side * s(8)
            pygame.draw.ellipse(surf, body_col, (ex - s(4), cy - r - s(16), s(8), s(20)))
            pygame.draw.ellipse(surf, ear_col, (ex - s(2), cy - r - s(13), s(4), s(14)))
            pygame.draw.ellipse(surf, (40, 30, 25), (ex - s(4), cy - r - s(16), s(8), s(20)), 1)
    elif hat_override is None and skin_id == "kotek":
        # Spiczaste kocie uszka!
        for side in (-1, 1):
            pts = [(cx + side * s(14), cy - s(9)), (cx + side * s(11), cy - r - s(8)), (cx + side * s(4), cy - s(14))]
            pygame.draw.polygon(surf, body_col, pts)
            pygame.draw.polygon(surf, (40, 30, 25), pts, 1)
    elif hat_override is None and skin_id == "piesek":
        # Klapnięte uszka pieska po bokach!
        for side in (-1, 1):
            pygame.draw.ellipse(surf, ear_col, (cx + side * s(14) - s(4), cy - s(8), s(8), s(17)))
            pygame.draw.ellipse(surf, (40, 30, 25), (cx + side * s(14) - s(4), cy - s(8), s(8), s(17)), 1)
    elif hat_override is None and skin_id == "pszczolka":
        # Małe białe skrzydełka pszczółki za plecami
        pygame.draw.ellipse(surf, (230, 248, 255), (cx - d * s(21) - s(4), cy - s(9), s(13), s(9)))
        pygame.draw.ellipse(surf, (150, 195, 225), (cx - d * s(21) - s(4), cy - s(9), s(13), s(9)), 1)
        for ex in (cx - ear_off_x, cx + ear_off_x):
            pygame.draw.circle(surf, ear_outer, (ex, cy - ear_off_y), ear_r)
            pygame.draw.circle(surf, ear_col, (ex, cy - ear_off_y), max(2, s(3.5)))
    else:
        for ex in (cx - ear_off_x, cx + ear_off_x):
            pygame.draw.circle(surf, ear_outer, (ex, cy - ear_off_y), ear_r)
            pygame.draw.circle(surf, ear_col, (ex, cy - ear_off_y), max(2, s(3.5)))
            pygame.draw.circle(surf, (40, 30, 25), (ex, cy - ear_off_y), ear_r, 1)

    # Okrągłe puszyste ciałko ze sferycznym cieniowaniem 3D (styl figurki Super Mario 3D!)
    shadow_col = (max(0, body_col[0] - 34), max(0, body_col[1] - 34), max(0, body_col[2] - 28))
    pygame.draw.circle(surf, shadow_col, (cx, cy), r)
    pygame.draw.circle(surf, body_col, (cx - s(1.5), cy - s(1.5)), max(2, r - s(1.2)))
    hi_col = (min(255, body_col[0] + 38), min(255, body_col[1] + 38), min(255, body_col[2] + 36))
    pygame.draw.ellipse(surf, hi_col, (cx - s(11), cy - s(14), s(16), s(9)))
    pygame.draw.circle(surf, (min(255, hi_col[0] + 22), min(255, hi_col[1] + 22), min(255, hi_col[2] + 22)), (cx - s(6), cy - s(11)), max(2, s(3.2)))
    # Jasny brzuszek
    pygame.draw.ellipse(surf, belly_col, (cx - s(10), cy + s(1), s(20), s(14)))

    # Specjalne wzory na futerku (pszczółka, biedronka, mumia, galaktyka, kaktus)
    if hat_override is None:
        if skin_id == "pszczolka":
            pygame.draw.line(surf, (35, 32, 28), (cx - s(14), cy + s(3)), (cx + s(14), cy + s(3)), max(2, s(3)))
            pygame.draw.line(surf, (35, 32, 28), (cx - s(11), cy + s(10)), (cx + s(11), cy + s(10)), max(2, s(3)))
        elif skin_id == "biedronka":
            for dx_dot, dy_dot in ((-9, 4), (9, 5), (0, 10), (-6, 11), (6, -10)):
                pygame.draw.circle(surf, (28, 28, 32), (cx + s(dx_dot), cy + s(dy_dot)), max(2, s(2.4)))
        elif skin_id == "mumia":
            for my_off in (-8, -1, 6, 12):
                pygame.draw.line(surf, (165, 152, 125), (cx - s(14), cy + s(my_off)), (cx + s(14), cy + s(my_off - 2)), max(1, s(2)))
        elif skin_id == "galaktyka":
            for sx_off, sy_off in ((-9, -6), (8, -9), (-5, 9), (9, 6), (2, -12)):
                pygame.draw.circle(surf, (240, 245, 255), (cx + s(sx_off), cy + s(sy_off)), max(1, s(1.5)))
        elif skin_id == "balwan":
            # Zimowy czerwony szalik
            pygame.draw.rect(surf, (220, 42, 52), (cx - s(13), cy + s(5), s(26), s(5)), border_radius=2)
            pygame.draw.rect(surf, (220, 42, 52), (cx + d * s(6), cy + s(7), s(5), s(9)), border_radius=2)
        elif skin_id == "kaktus":
            # Małe kolce po bokach
            for side in (-1, 1):
                for ky in (-4, 3, 9):
                    pygame.draw.line(surf, (225, 245, 195), (cx + side * r, cy + s(ky)), (cx + side * (r + s(4)), cy + s(ky - 1)), 2)

    # Obrys ciała
    outline_col = (255, 255, 255) if skin_id in ("diament", "galaktyka") else ((255, 240, 130) if skin_id == "zloty" else (40, 30, 25))
    pygame.draw.circle(surf, outline_col, (cx, cy), r, 2)

    # Złota gwiazda na brzuszku Super-Chomika
    if hat_override is None and skin_id == "superbohater":
        pygame.draw.circle(surf, GOLD, (cx, cy + s(8)), max(3, s(4.5)))
        pygame.draw.circle(surf, accent, (cx, cy + s(8)), max(1, s(2)))

    # Chustka Kowboja pod szyją
    if hat_override is None and skin_id == "kowboj":
        scarf = [(cx - s(10), cy + s(4)), (cx + s(10), cy + s(4)), (cx + d * s(2), cy + s(13))]
        pygame.draw.polygon(surf, accent, scarf)

    # Pulchne różowe policzki (poza robotem/duchem)
    if skin_id not in ("robot", "duch"):
        cheek_y = cy + s(2)
        cheek_col = (145, 200, 120) if skin_id == "zombie" else (245, 160, 165)
        pygame.draw.circle(surf, cheek_col, (cx + d * s(9), cheek_y), max(2, s(4)))
        pygame.draw.circle(surf, cheek_col, (cx - d * s(4), cheek_y), max(2, s(3.5)))

    # Oczy patrzące lekko w stronę celowania
    look_x = s(math.cos(aim_angle) * 2.5)
    look_y = s(math.sin(aim_angle) * 2.0)
    eye1 = (cx + d * s(6), cy - s(4))
    eye2 = (cx - d * s(2), cy - s(4))

    if skin_id == "cyber" and hat_override is None:
        visor = pygame.Rect(cx - s(11), cy - s(8), s(22), s(8))
        pygame.draw.rect(surf, (20, 30, 50), visor, border_radius=3)
        pygame.draw.rect(surf, accent, visor.inflate(-3, -3), border_radius=2)
    elif skin_id == "robot" and hat_override is None:
        screen_r = pygame.Rect(cx - s(10), cy - s(8), s(20), s(9))
        pygame.draw.rect(surf, (25, 32, 42), screen_r, border_radius=3)
        pygame.draw.circle(surf, (255, 230, 70), (cx - s(4), cy - s(4)), max(2, s(2.5)))
        pygame.draw.circle(surf, (255, 230, 70), (cx + s(5), cy - s(4)), max(2, s(2.5)))
    else:
        if skin_id == "panda" and hat_override is None:
            for ex, ey in (eye1, eye2):
                pygame.draw.circle(surf, (32, 34, 40), (ex, ey), max(3, s(5.2)))
        elif skin_id == "piesek" and hat_override is None:
            pygame.draw.circle(surf, (135, 82, 42), eye1, max(3, s(5.4)))
        elif skin_id == "szkielet" and hat_override is None:
            for ex, ey in (eye1, eye2):
                pygame.draw.circle(surf, (25, 26, 32), (ex, ey), max(3, s(4.8)))
        elif skin_id == "superbohater" and hat_override is None:
            mask_r = pygame.Rect(cx - s(12), cy - s(8), s(24), s(8))
            pygame.draw.rect(surf, accent, mask_r, border_radius=4)

        eye_col = (
            (230, 35, 45)
            if skin_id == "wampir"
            else (
                (255, 235, 85)
                if skin_id in ("duch", "dynia", "mumia")
                else ((120, 235, 255) if skin_id == "galaktyka" else (25, 22, 22))
            )
        )
        for idx, (ex, ey) in enumerate((eye1, eye2)):
            er = max(2, s(3.8 if (skin_id == "zombie" and idx == 0) else 3.2))
            if skin_id == "pirat" and hat_override is None and idx == 1:
                pygame.draw.line(surf, (25, 25, 30), (cx - r + 2, cy - s(9)), (cx + r - 2, cy - s(1)), 2)
                pygame.draw.circle(surf, (25, 25, 30), (ex, ey), max(3, s(4.5)))
            else:
                pygame.draw.circle(surf, eye_col, (ex + look_x // 2, ey + look_y // 2), er)
                pygame.draw.circle(surf, WHITE, (ex + look_x // 2 - 1, ey + look_y // 2 - 1), max(1, s(1.2)))
        if skin_id == "dj" and hat_override is None:
            # Ciemne okulary przeciwsłoneczne DJ-a
            pygame.draw.rect(surf, (22, 24, 34), (cx - s(12), cy - s(8), s(11), s(7)), border_radius=2)
            pygame.draw.rect(surf, (22, 24, 34), (cx + s(1), cy - s(8), s(11), s(7)), border_radius=2)
            pygame.draw.line(surf, accent, (cx - s(12), cy - s(6)), (cx + s(12), cy - s(6)), 2)
        elif skin_id == "detektyw" and hat_override is None:
            # Złoty monokl detektywa
            pygame.draw.circle(surf, GOLD, eye1, max(3, s(5)), 2)

    # Nosek + kły Wampira / szew Zombie / nos Klauna / marchewka Bałwanka / wąsiki Kotka / ząbki Rekina
    nose = (cx + d * s(3), cy + s(1))
    if hat_override is None and skin_id == "klaun":
        pygame.draw.circle(surf, (235, 35, 45), nose, max(3, s(4.8)))
    elif hat_override is None and skin_id == "balwan":
        pygame.draw.polygon(surf, (245, 130, 32), [(nose[0], nose[1] - s(2)), (nose[0] + d * s(9), nose[1] + s(1)), (nose[0], nose[1] + s(3))])
    else:
        pygame.draw.circle(surf, (235, 120, 130), nose, max(2, s(2.2)))

    if hat_override is None and skin_id == "wampir":
        pygame.draw.polygon(surf, WHITE, [(cx - s(2), cy + s(3)), (cx, cy + s(8)), (cx + s(2), cy + s(3))])
        pygame.draw.polygon(surf, WHITE, [(cx + s(4), cy + s(3)), (cx + s(6), cy + s(8)), (cx + s(8), cy + s(3))])
    elif hat_override is None and skin_id == "rekin":
        for tx_off in (-4, 0, 4):
            pygame.draw.polygon(surf, WHITE, [(cx + s(tx_off), cy + s(4)), (cx + s(tx_off + 2), cy + s(8)), (cx + s(tx_off + 4), cy + s(4))])
    elif hat_override is None and skin_id == "kotek":
        for side in (-1, 1):
            pygame.draw.line(surf, (70, 45, 28), (cx + side * s(8), cy + s(1)), (cx + side * s(18), cy - s(1)), 1)
            pygame.draw.line(surf, (70, 45, 28), (cx + side * s(8), cy + s(4)), (cx + side * s(18), cy + s(5)), 1)
    elif hat_override is None and skin_id == "zombie":
        pygame.draw.line(surf, (75, 45, 50), (cx - s(8), cy - s(11)), (cx + s(6), cy - s(10)), 2)
        for sx_off in (-5, -1, 3):
            pygame.draw.line(surf, (75, 45, 50), (cx + s(sx_off), cy - s(13)), (cx + s(sx_off), cy - s(8)), 1)

    # Uroczy uśmiech i chomiczy ząbek (dla skórek bez kłów/rekinich zębów)
    if hat_override is None and skin_id not in ("wampir", "rekin", "zombie", "robot", "cyber"):
        pygame.draw.arc(surf, (65, 38, 30), (cx + d * s(1) - s(3), cy + s(1), s(7), s(5)), math.pi, math.tau, 1)
        pygame.draw.rect(surf, WHITE, (cx + d * s(2), cy + s(4), max(2, s(3)), max(2, s(3))))

    # Animowane łapki na dole (poruszają się naprzemiennie przy biegu!)
    paw_swing = int(math.sin(walk_phase) * 4.5 * scale)
    pygame.draw.ellipse(surf, ear_col, (cx - s(11) + paw_swing, cy + s(13), s(8), s(5)))
    pygame.draw.ellipse(surf, (40, 30, 25), (cx - s(11) + paw_swing, cy + s(13), s(8), s(5)), 1)
    pygame.draw.ellipse(surf, ear_col, (cx + s(3) - paw_swing, cy + s(13), s(8), s(5)))
    pygame.draw.ellipse(surf, (40, 30, 25), (cx + s(3) - paw_swing, cy + s(13), s(8), s(5)), 1)

    # --- Akcesoria skórek lub czapki botów fabularnych (równo osadzone na głowie!) ---
    top_y = cy - r  # dokładny czubek głowy chomika
    if hat_override == "wizard":
        pts = [(cx - s(15), top_y + s(4)), (cx + s(15), top_y + s(4)), (cx + s(2), top_y - s(18))]
        pygame.draw.polygon(surf, (85, 55, 165), pts)
        pygame.draw.polygon(surf, GOLD, pts, 2)
        pygame.draw.rect(surf, (65, 40, 135), (cx - s(19), top_y + s(1), s(38), s(5)), border_radius=3)
        pygame.draw.circle(surf, GOLD, (cx + s(2), top_y - s(6)), max(2, s(3)))
    elif hat_override == "merchant":
        pygame.draw.ellipse(surf, (45, 155, 85), (cx - s(17), top_y - s(7), s(34), s(13)))
        pygame.draw.ellipse(surf, GOLD, (cx - s(17), top_y - s(7), s(34), s(13)), 2)
        pygame.draw.circle(surf, GOLD, (cx, top_y - s(1)), max(2, s(3.5)))
    elif hat_override == "scout":
        pygame.draw.rect(surf, (150, 98, 52), (cx - s(20), top_y + s(1), s(40), s(5)), border_radius=2)
        pygame.draw.rect(surf, (175, 118, 65), (cx - s(12), top_y - s(9), s(24), s(11)), border_radius=4)
        pygame.draw.line(surf, (235, 185, 55), (cx - s(12), top_y), (cx + s(12), top_y), 2)
    elif skin_id == "ninja":
        pygame.draw.rect(surf, accent, (cx - r + 1, cy - s(11), r * 2 - 2, s(5)), border_radius=2)
        pygame.draw.line(surf, accent, (cx - d * r, cy - s(9)), (cx - d * (r + s(10)), cy - s(13)), 3)
        pygame.draw.line(surf, accent, (cx - d * r, cy - s(7)), (cx - d * (r + s(8)), cy - s(4)), 3)
    elif skin_id == "rycerz":
        # Pełny stalowy hełm rycerski z opaską i czerwonym pióropuszem
        dome = [(cx - s(16), top_y + s(6)), (cx - s(13), top_y - s(3)), (cx, top_y - s(6)), (cx + s(13), top_y - s(3)), (cx + s(16), top_y + s(6))]
        pygame.draw.polygon(surf, (195, 205, 220), dome)
        pygame.draw.polygon(surf, (95, 105, 120), dome, 2)
        pygame.draw.rect(surf, (145, 155, 172), (cx - s(17), top_y + s(3), s(34), s(4)), border_radius=2)
        pygame.draw.polygon(
            surf,
            accent,
            [(cx, top_y - s(14)), (cx - d * s(10), top_y - s(6)), (cx + d * s(5), top_y - s(5))],
        )
    elif skin_id == "kosmita":
        for side in (-1, 1):
            ax = cx + side * s(9)
            ay = top_y - s(10)
            pygame.draw.line(surf, (70, 170, 75), (cx + side * s(5), top_y + s(2)), (ax, ay), 2)
            pygame.draw.circle(surf, accent, (ax, ay), max(2, s(3.5)))
    elif skin_id == "krol":
        crown = [
            (cx - s(12), top_y + s(4)),
            (cx - s(12), top_y - s(8)),
            (cx - s(5), top_y - s(2)),
            (cx, top_y - s(11)),
            (cx + s(5), top_y - s(2)),
            (cx + s(12), top_y - s(8)),
            (cx + s(12), top_y + s(4)),
        ]
        pygame.draw.polygon(surf, GOLD, crown)
        pygame.draw.polygon(surf, (165, 115, 20), crown, 2)
        pygame.draw.circle(surf, (225, 45, 65), (cx, top_y - s(2)), max(2, s(2.5)))
    elif skin_id == "pirat":
        # Kapelusz pirata równo osadzony nad oczami + biała czaszka
        hat = [
            (cx - s(19), top_y + s(4)),
            (cx + s(19), top_y + s(4)),
            (cx + s(13), top_y - s(8)),
            (cx, top_y - s(12)),
            (cx - s(13), top_y - s(8)),
        ]
        pygame.draw.polygon(surf, (32, 32, 38), hat)
        pygame.draw.polygon(surf, GOLD, hat, 2)
        pygame.draw.circle(surf, WHITE, (cx, top_y - s(3)), max(2, s(3.2)))
        pygame.draw.line(surf, WHITE, (cx - s(5), top_y + s(1)), (cx + s(5), top_y - s(6)), 1)
        pygame.draw.line(surf, WHITE, (cx - s(5), top_y - s(6)), (cx + s(5), top_y + s(1)), 1)
    elif skin_id == "czarodziej":
        pts = [(cx - s(14), top_y + s(3)), (cx + s(14), top_y + s(3)), (cx + d * s(4), top_y - s(16))]
        pygame.draw.polygon(surf, (60, 42, 145), pts)
        pygame.draw.polygon(surf, GOLD, pts, 2)
        pygame.draw.rect(surf, (50, 35, 125), (cx - s(18), top_y + s(1), s(36), s(5)), border_radius=2)
        pygame.draw.circle(surf, GOLD, (cx, top_y - s(5)), max(2, s(2.8)))
    elif skin_id == "szef_kuchni":
        # Puszysta biała czapka kucharska na głowie
        pygame.draw.circle(surf, WHITE, (cx - s(7), top_y - s(6)), max(3, s(6)))
        pygame.draw.circle(surf, WHITE, (cx, top_y - s(9)), max(4, s(7)))
        pygame.draw.circle(surf, WHITE, (cx + s(7), top_y - s(6)), max(3, s(6)))
        pygame.draw.rect(surf, WHITE, (cx - s(12), top_y - s(5), s(24), s(9)), border_radius=3)
        pygame.draw.rect(surf, (190, 196, 208), (cx - s(12), top_y + s(1), s(24), s(3)), border_radius=1)
    elif skin_id == "kowboj":
        # Kapelusz kowbojski z rondem i złotą wstążką
        pygame.draw.rect(surf, (155, 95, 48), (cx - s(11), top_y - s(9), s(22), s(11)), border_radius=5)
        pygame.draw.rect(surf, (95, 55, 25), (cx - s(11), top_y - s(9), s(22), s(11)), 2, border_radius=5)
        pygame.draw.ellipse(surf, (135, 82, 42), (cx - s(21), top_y - s(1), s(42), s(7)))
        pygame.draw.ellipse(surf, (85, 48, 22), (cx - s(21), top_y - s(1), s(42), s(7)), 1)
        pygame.draw.line(surf, GOLD, (cx - s(11), top_y), (cx + s(11), top_y), 2)
    elif skin_id == "astronauta":
        # Kosmiczna szklana bańka hełmu wokół głowy
        pygame.draw.circle(surf, (180, 235, 255), (cx, cy - s(1)), r + s(5), 3)
        pygame.draw.line(surf, WHITE, (cx - s(10), top_y - s(1)), (cx - s(4), top_y - s(3)), 2)
    elif skin_id == "wiking":
        # Pełny stalowy hełm wikinga + dwa wyraźne zakrzywione rogi
        dome = [(cx - s(16), top_y + s(5)), (cx - s(12), top_y - s(4)), (cx, top_y - s(6)), (cx + s(12), top_y - s(4)), (cx + s(16), top_y + s(5))]
        pygame.draw.polygon(surf, (165, 176, 192), dome)
        pygame.draw.polygon(surf, (80, 90, 105), dome, 2)
        pygame.draw.rect(surf, (125, 136, 152), (cx - s(17), top_y + s(2), s(34), s(4)), border_radius=2)
        pygame.draw.polygon(surf, (245, 238, 215), [(cx - s(13), top_y + s(2)), (cx - s(22), top_y - s(10)), (cx - s(8), top_y - s(2))])
        pygame.draw.polygon(surf, (245, 238, 215), [(cx + s(13), top_y + s(2)), (cx + s(22), top_y - s(10)), (cx + s(8), top_y - s(2))])
    elif skin_id == "samuraj":
        # Czerwony hełm Kabuto + złoty półksiężyc
        kabuto = [(cx - s(17), top_y + s(5)), (cx + s(17), top_y + s(5)), (cx + s(12), top_y - s(6)), (cx - s(12), top_y - s(6))]
        pygame.draw.polygon(surf, accent, kabuto)
        pygame.draw.polygon(surf, (40, 20, 25), kabuto, 2)
        pygame.draw.polygon(surf, GOLD, [(cx - s(9), top_y - s(13)), (cx, top_y - s(3)), (cx + s(9), top_y - s(13)), (cx, top_y - s(7))])
    elif skin_id == "robot":
        # Antenka ze świecącą czerwoną diodą
        pygame.draw.line(surf, (95, 108, 122), (cx, top_y + s(1)), (cx, top_y - s(10)), 3)
        pygame.draw.circle(surf, accent, (cx, top_y - s(11)), max(2, s(4)))
    elif skin_id == "ogien":
        # Płonąca korona płomieni na głowie!
        flames = [
            (cx - s(13), top_y + s(4)),
            (cx - s(10), top_y - s(8)),
            (cx - s(4), top_y - s(1)),
            (cx, top_y - s(13)),
            (cx + s(5), top_y - s(2)),
            (cx + s(11), top_y - s(9)),
            (cx + s(13), top_y + s(4)),
        ]
        pygame.draw.polygon(surf, (255, 115, 30), flames)
        pygame.draw.polygon(surf, accent, [(cx - s(7), top_y + s(3)), (cx, top_y - s(8)), (cx + s(7), top_y + s(3))])
    elif skin_id == "lod":
        # Kryształy lodu na głowie
        ice = [
            (cx - s(12), top_y + s(4)),
            (cx - s(8), top_y - s(8)),
            (cx - s(2), top_y),
            (cx + s(1), top_y - s(12)),
            (cx + s(6), top_y - s(1)),
            (cx + s(11), top_y - s(7)),
            (cx + s(12), top_y + s(4)),
        ]
        pygame.draw.polygon(surf, (175, 240, 255), ice)
        pygame.draw.polygon(surf, WHITE, ice, 2)
    elif skin_id == "duch":
        pygame.draw.circle(surf, WHITE, (cx - s(16), top_y + s(2)), max(2, s(3)))
        pygame.draw.circle(surf, WHITE, (cx + s(17), top_y + s(6)), max(2, s(2.5)))
    elif skin_id == "diament":
        gem = [(cx, top_y - s(13)), (cx + s(7), top_y - s(5)), (cx, top_y + s(2)), (cx - s(7), top_y - s(5))]
        pygame.draw.polygon(surf, (140, 255, 255), gem)
        pygame.draw.polygon(surf, WHITE, gem, 2)
        pygame.draw.line(surf, WHITE, (cx - s(17), top_y + s(2)), (cx - s(13), top_y + s(2)), 2)
        pygame.draw.line(surf, WHITE, (cx - s(15), top_y), (cx - s(15), top_y + s(4)), 2)
        pygame.draw.line(surf, WHITE, (cx + s(14), top_y), (cx + s(18), top_y), 2)
        pygame.draw.line(surf, WHITE, (cx + s(16), top_y - s(2)), (cx + s(16), top_y + s(2)), 2)
    # --- 28 nowych czapek i dodatków (łącznie 50 skórek!) ---
    elif skin_id == "policjant":
        cap = [(cx - s(15), top_y + s(4)), (cx + s(15), top_y + s(4)), (cx + s(17), top_y - s(5)), (cx - s(17), top_y - s(5))]
        pygame.draw.polygon(surf, (32, 52, 108), cap)
        pygame.draw.rect(surf, (20, 25, 42), (cx - s(17), top_y + s(2), s(34), s(4)), border_radius=2)
        pygame.draw.circle(surf, GOLD, (cx, top_y - s(1)), max(2, s(3.2)))
    elif skin_id == "budowlaniec":
        helmet = [(cx - s(17), top_y + s(4)), (cx - s(13), top_y - s(6)), (cx, top_y - s(9)), (cx + s(13), top_y - s(6)), (cx + s(17), top_y + s(4))]
        pygame.draw.polygon(surf, (250, 210, 40), helmet)
        pygame.draw.polygon(surf, (175, 138, 18), helmet, 2)
        pygame.draw.rect(surf, (235, 190, 28), (cx - s(19), top_y + s(2), s(38), s(4)), border_radius=2)
    elif skin_id == "strazak":
        helmet = [(cx - s(18), top_y + s(5)), (cx - s(13), top_y - s(6)), (cx, top_y - s(10)), (cx + s(13), top_y - s(6)), (cx + s(18), top_y + s(5))]
        pygame.draw.polygon(surf, (218, 38, 38), helmet)
        pygame.draw.polygon(surf, (130, 20, 20), helmet, 2)
        pygame.draw.rect(surf, GOLD, (cx - s(4), top_y - s(4), s(8), s(7)), border_radius=2)
    elif skin_id == "lekarz":
        pygame.draw.rect(surf, WHITE, (cx - s(15), top_y + s(1), s(30), s(5)), border_radius=2)
        pygame.draw.circle(surf, WHITE, (cx, top_y - s(2)), max(4, s(6)))
        pygame.draw.circle(surf, (180, 190, 205), (cx, top_y - s(2)), max(4, s(6)), 1)
        pygame.draw.line(surf, (230, 42, 52), (cx - s(3), top_y - s(2)), (cx + s(3), top_y - s(2)), 2)
        pygame.draw.line(surf, (230, 42, 52), (cx, top_y - s(5)), (cx, top_y + s(1)), 2)
    elif skin_id == "pilkarz":
        pygame.draw.rect(surf, WHITE, (cx - r + 1, cy - s(11), r * 2 - 2, s(5)), border_radius=2)
        pygame.draw.rect(surf, accent, (cx - r + 1, cy - s(8), r * 2 - 2, s(2)))
    elif skin_id == "klaun":
        for side, col in ((-1, (245, 75, 75)), (1, (65, 175, 250))):
            pygame.draw.circle(surf, col, (cx + side * s(15), top_y + s(4)), max(3, s(5.5)))
            pygame.draw.circle(surf, (255, 215, 55), (cx + side * s(12), top_y - s(1)), max(2, s(4)))
        pygame.draw.polygon(surf, (165, 72, 235), [(cx - s(8), top_y + s(3)), (cx + s(8), top_y + s(3)), (cx, top_y - s(10))])
    elif skin_id == "detektyw":
        pygame.draw.ellipse(surf, (125, 86, 50), (cx - s(17), top_y - s(6), s(34), s(12)))
        pygame.draw.ellipse(surf, (78, 52, 28), (cx - s(17), top_y - s(6), s(34), s(12)), 2)
        pygame.draw.rect(surf, (105, 68, 38), (cx - s(20), top_y + s(1), s(40), s(4)), border_radius=2)
    elif skin_id == "magik":
        pygame.draw.rect(surf, (28, 28, 36), (cx - s(11), top_y - s(13), s(22), s(16)), border_radius=2)
        pygame.draw.rect(surf, accent, (cx - s(11), top_y - s(2), s(22), s(4)))
        pygame.draw.rect(surf, (22, 22, 30), (cx - s(17), top_y + s(1), s(34), s(4)), border_radius=2)
    elif skin_id == "balwan":
        pygame.draw.rect(surf, (32, 34, 42), (cx - s(10), top_y - s(11), s(20), s(13)), border_radius=2)
        pygame.draw.rect(surf, (22, 24, 30), (cx - s(16), top_y + s(1), s(32), s(4)), border_radius=2)
    elif skin_id == "mikolaj":
        pts = [(cx - s(15), top_y + s(4)), (cx + s(15), top_y + s(4)), (cx + d * s(12), top_y - s(12))]
        pygame.draw.polygon(surf, (220, 35, 45), pts)
        pygame.draw.rect(surf, WHITE, (cx - s(16), top_y + s(1), s(32), s(5)), border_radius=3)
        pygame.draw.circle(surf, WHITE, (cx + d * s(12), top_y - s(11)), max(3, s(4.5)))
    elif skin_id in ("pszczolka", "biedronka"):
        for side in (-1, 1):
            ax = cx + side * s(8)
            ay = top_y - s(9)
            pygame.draw.line(surf, (35, 32, 30), (cx + side * s(4), top_y + s(2)), (ax, ay), 2)
            pygame.draw.circle(surf, (35, 32, 30), (ax, ay), max(2, s(3)))
    elif skin_id == "dynia":
        pygame.draw.rect(surf, (68, 165, 58), (cx - s(3), top_y - s(9), s(6), s(11)), border_radius=2)
        pygame.draw.ellipse(surf, (88, 195, 72), (cx + s(1), top_y - s(7), s(9), s(5)))
    elif skin_id == "kaktus":
        # Różowy kwiatek na czubku kaktusa
        for ang_deg in range(0, 360, 72):
            fx = cx + int(math.cos(math.radians(ang_deg)) * s(5))
            fy = top_y - s(4) + int(math.sin(math.radians(ang_deg)) * s(5))
            pygame.draw.circle(surf, accent, (fx, fy), max(2, s(3.2)))
        pygame.draw.circle(surf, GOLD, (cx, top_y - s(4)), max(2, s(2.5)))
    elif skin_id == "rekin":
        # Płetwa rekina na głowie
        fin = [(cx - s(7), top_y + s(4)), (cx + d * s(2), top_y - s(13)), (cx + s(7), top_y + s(4))]
        pygame.draw.polygon(surf, (82, 118, 150), fin)
        pygame.draw.polygon(surf, (42, 68, 92), fin, 2)
    elif skin_id == "gladiator":
        dome = [(cx - s(16), top_y + s(5)), (cx - s(12), top_y - s(4)), (cx, top_y - s(6)), (cx + s(12), top_y - s(4)), (cx + s(16), top_y + s(5))]
        pygame.draw.polygon(surf, (195, 148, 52), dome)
        pygame.draw.polygon(surf, (112, 82, 24), dome, 2)
        pygame.draw.ellipse(surf, (220, 42, 48), (cx - s(9), top_y - s(13), s(18), s(9)))
    elif skin_id in ("gamer", "dj"):
        # Słuchawki nauszne z pałąkiem (RGB dla Gamera, neonowe dla DJ-a)
        pygame.draw.arc(surf, (38, 42, 56), (cx - r - s(2), cy - r - s(5), (r + s(2)) * 2, (r + s(2)) * 2), 0.1, math.pi - 0.1, max(3, s(4)))
        for side in (-1, 1):
            pygame.draw.rect(surf, (32, 36, 48), (cx + side * r - s(3), cy - s(7), s(6), s(13)), border_radius=3)
            pygame.draw.rect(surf, accent, (cx + side * r - s(2), cy - s(5), s(4), s(9)), border_radius=2)
        if skin_id == "gamer":
            pygame.draw.line(surf, accent, (cx - d * r, cy + s(4)), (cx - d * s(4), cy + s(7)), 2)
    elif skin_id == "jednorozec":
        # Złoty spiralny róg jednorożca + tęczowa grzywka
        horn = [(cx - s(4), top_y + s(3)), (cx + s(4), top_y + s(3)), (cx + d * s(2), top_y - s(14))]
        pygame.draw.polygon(surf, GOLD, horn)
        pygame.draw.polygon(surf, (185, 138, 25), horn, 1)
        pygame.draw.circle(surf, (255, 110, 195), (cx - s(6), top_y + s(2)), max(2, s(3.5)))
        pygame.draw.circle(surf, (110, 215, 255), (cx + s(6), top_y + s(2)), max(2, s(3.5)))
    elif skin_id == "faraon":
        # Egipskie nakrycie Nemes (złoto-niebieskie paski) + złota kobra
        nemes = [(cx - s(20), cy + s(4)), (cx - s(15), top_y - s(5)), (cx + s(15), top_y - s(5)), (cx + s(20), cy + s(4)), (cx + s(13), top_y + s(5)), (cx - s(13), top_y + s(5))]
        pygame.draw.polygon(surf, GOLD, nemes)
        pygame.draw.line(surf, accent, (cx - s(14), top_y - s(1)), (cx + s(14), top_y - s(1)), max(2, s(3)))
        pygame.draw.line(surf, accent, (cx - s(16), top_y + s(3)), (cx + s(16), top_y + s(3)), max(2, s(2)))
        pygame.draw.circle(surf, (235, 55, 45), (cx, top_y - s(6)), max(2, s(3.5)))
    elif skin_id == "smok":
        # Dwa smocze rogi + czerwone kolce na czubku
        pygame.draw.polygon(surf, (235, 205, 105), [(cx - s(11), top_y + s(3)), (cx - s(16), top_y - s(11)), (cx - s(5), top_y)])
        pygame.draw.polygon(surf, (235, 205, 105), [(cx + s(11), top_y + s(3)), (cx + s(16), top_y - s(11)), (cx + s(5), top_y)])
        pygame.draw.polygon(surf, accent, [(cx - s(4), top_y + s(2)), (cx, top_y - s(9)), (cx + s(4), top_y + s(2))])
    elif skin_id == "zloty":
        # Lśniąca złota aureola nad głową!
        pygame.draw.ellipse(surf, (255, 245, 150), (cx - s(13), top_y - s(10), s(26), s(7)), max(2, s(3)))
    elif skin_id == "galaktyka":
        # Pierścień Saturna wokół głowy + świecąca gwiazdka!
        pygame.draw.ellipse(surf, accent, (cx - s(24), top_y - s(3), s(48), s(10)), max(2, s(2.5)))
        pygame.draw.circle(surf, GOLD, (cx, top_y - s(9)), max(2, s(3.5)))


class Hamster:
    """Klasa reprezentująca chomika — zarówno gracza, jak i każdego z 7 atakujących botów."""

    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        is_player: bool = False,
        skin_id: str = "klasyczny",
        weapon_id: str = "ziarna",
        body_override=None,
        difficulty_id: str = "normalny",
    ):
        self.name = name
        self.is_player = is_player
        self.difficulty = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normalny"])
        self.spawn_x = x
        self.spawn_y = y
        self.rect = pygame.Rect(int(x - 16), int(y - 17), 32, 34)
        self.vx = 0.0
        self.vy = 0.0

        # Skoki (podwójny skok + krótkie okienko na skok przy krawędzi platformy)
        self.on_ground = False
        self.coyote_timer = 0.0
        self.jumps_left = 2

        # Statystyki i ekwipunek
        self.max_hp = 100 if is_player else self.difficulty["bot_hp"]
        self.hp = self.max_hp
        self.alive = True
        self.respawn_timer = 0.0
        self.invuln_timer = 1.2
        self.hurt_flash = 0.0

        self.skin_id = skin_id
        self.body_override = body_override
        self.owned_skins = {skin_id}
        self.owned_weapons = {weapon_id}
        self.weapon_id = weapon_id
        self.shoot_cooldown = 0.0
        self.aim_angle = 0.0
        self.facing_right = True

        # Ziarna słonecznika i postęp
        self.seeds = 0              # Ziarna w portfelu (do wydania w sklepie)
        self.total_seeds = 0        # Łącznie zebrane ziarna (do rankingu i zwycięstwa)
        self.kills = 0
        self.upgrade_levels = {"max_hp": 0, "speed": 0}

        # Aktywne power-upy (czas pozostały w sekundach)
        self.speed_timer = 0.0
        self.shield_timer = 0.0
        self.damage_timer = 0.0

        # Animacja biegu i sprężysty squash-and-stretch przy skoku/lądowaniu
        self.walk_phase = random.uniform(0, 6.28)
        self.squash_timer = 0.0
        self.sparkle_timer = random.uniform(0.1, 0.3)

        # Pamięć AI dla 7 atakujących botów
        self.ai_dir = random.choice([-1, 1])
        self.ai_change_timer = random.uniform(0.6, 2.0)
        self.ai_jump_cooldown = 0.0
        self.ai_shoot_delay = random.uniform(0.25, 0.75)

    def apply_difficulty(self, difficulty_id: str):
        """Aktualizuje statystyki bota po zmianie poziomu trudności."""
        self.difficulty = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normalny"])
        if not self.is_player:
            self.max_hp = self.difficulty["bot_hp"]
            self.hp = min(self.hp, self.max_hp) if self.alive else self.max_hp

    def get_move_speed(self) -> float:
        base = PLAYER_SPEED if self.is_player else PLAYER_SPEED * self.difficulty["bot_speed_mult"]
        base *= 1.0 + 0.12 * self.upgrade_levels.get("speed", 0)
        if self.speed_timer > 0:
            base *= 1.38
        return base

    def try_jump(self, particles: list[Particle], sounds) -> bool:
        """Obsługuje skok z ziemi oraz PODWÓJNY SKOK w powietrzu!"""
        if not self.alive:
            return False

        if self.on_ground or self.coyote_timer > 0:
            self.vy = -JUMP_SPEED * (1.12 if self.speed_timer > 0 else 1.0)
            self.on_ground = False
            self.coyote_timer = 0.0
            self.jumps_left = 1
            self.squash_timer = 0.14
            if self.is_player:
                sounds.play("jump")
            spawn_burst(particles, self.rect.centerx, self.rect.bottom, (235, 235, 240), count=5, speed=90)
            return True
        elif self.jumps_left > 0:
            # PODWÓJNY SKOK w powietrzu + pierścień powietrza pod łapkami!
            self.vy = -DOUBLE_JUMP_SPEED * (1.1 if self.speed_timer > 0 else 1.0)
            self.jumps_left -= 1
            self.squash_timer = 0.16
            if self.is_player:
                sounds.play("double_jump")
            particles.append(ShockwaveRing(self.rect.centerx, self.rect.bottom, (240, 248, 255), max_radius=30, life=0.25, width=3))
            spawn_burst(particles, self.rect.centerx, self.rect.bottom, WHITE, count=10, speed=150)
            return True
        return False

    def try_shoot(self, bullets: list[Bullet], particles: list[Particle], sounds) -> float:
        """Strzela aktualną bronią w kierunku aim_angle. Zwraca siłę wstrząsu kamery."""
        if not self.alive or self.shoot_cooldown > 0:
            return 0.0

        spec = WEAPONS[self.weapon_id]
        cd = spec["cooldown"]
        if self.damage_timer > 0:
            cd *= 0.75  # Mega-strzał przyspiesza też ogień!
        if not self.is_player:
            cd *= self.difficulty["bot_cooldown_mult"]

        self.shoot_cooldown = cd

        damage_mult = 1.0
        if self.damage_timer > 0:
            damage_mult *= 2.0
        if not self.is_player:
            damage_mult *= self.difficulty["bot_damage_mult"]

        # Punkt wylotu pocisku przy końcu lufy
        muzzle_dist = 24 if self.weapon_id != "awp" else 36
        mx = self.rect.centerx + math.cos(self.aim_angle) * muzzle_dist
        my = self.rect.centery + math.sin(self.aim_angle) * muzzle_dist

        spread_rad = math.radians(spec["spread_deg"])
        bot_extra_spread = math.radians(self.difficulty["bot_spread_deg"]) if not self.is_player else 0.0

        for _ in range(spec["pellets"]):
            ang = self.aim_angle + random.uniform(-spread_rad, spread_rad) + random.uniform(-bot_extra_spread, bot_extra_spread)
            bullets.append(Bullet(mx, my, ang, self.weapon_id, self, damage_mult=damage_mult))

        # Lekki odrzut broni (świetnie czuć przy shotgunie i AWP!)
        recoil = spec["recoil"] * (0.55 if not self.is_player else 1.0)
        self.vx -= math.cos(self.aim_angle) * recoil * 0.45
        self.vy -= math.sin(self.aim_angle) * recoil * 0.2

        # Błysk z lufy (Muzzle Flash), wyrzucana łuska (Shell Casing) i iskierki!
        flash_size = 18.0 if self.weapon_id == "awp" else (16.0 if self.weapon_id == "shotgun" else 11.0)
        particles.append(MuzzleFlash(mx, my, self.aim_angle, spec["color"], size=flash_size))
        particles.append(ShellCasing(self.rect.centerx, self.rect.centery - 2, self.facing_right, self.weapon_id))
        spawn_burst(particles, mx, my, spec["color"], count=4 if self.weapon_id != "shotgun" else 8, speed=130)

        if self.is_player:
            sounds.play(f"shoot_{self.weapon_id}")
            return 7.0 if self.weapon_id == "awp" else (5.0 if self.weapon_id == "shotgun" else 1.5)
        return 0.0

    def take_damage(self, amount: int, attacker, particles: list[Particle], texts: list[FloatingText], sounds, seeds_list: list[SunflowerSeed]) -> bool:
        """Zadaje obrażenia chomikowi. Zwraca True, jeśli chomik został pokonany."""
        if not self.alive or self.invuln_timer > 0:
            return False

        # Tarcza pochłania 70% obrażeń!
        if self.shield_timer > 0:
            amount = max(2, int(amount * 0.3))
            texts.append(FloatingText(self.rect.centerx, self.rect.top - 10, f"-{amount} (Tarcza)", BLUE, 0.7))
        else:
            texts.append(FloatingText(self.rect.centerx, self.rect.top - 10, f"-{amount}", RED, 0.75))

        self.hp -= amount
        self.hurt_flash = 0.14
        spawn_burst(particles, self.rect.centerx, self.rect.centery, RED, count=6, speed=140)

        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.respawn_timer = 2.6 if self.is_player else 3.4
            particles.append(ShockwaveRing(self.rect.centerx, self.rect.centery, GOLD, max_radius=54, life=0.35, width=4))
            spawn_burst(particles, self.rect.centerx, self.rect.centery, GOLD, count=18, speed=260)

            if attacker is not None and attacker is not self:
                attacker.kills += 1

            # Z pokonanego chomika wysypują się ziarna słonecznika!
            drop_count = 4 if not self.is_player else min(3, self.seeds)
            if self.is_player:
                self.seeds = max(0, self.seeds - drop_count)
                texts.append(FloatingText(self.rect.centerx, self.rect.top - 22, "Pokonany! Odradzanie...", RED, 1.4))
            else:
                texts.append(FloatingText(self.rect.centerx, self.rect.top - 22, f"{self.name} pokonany!", GOLD, 1.1))

            for _ in range(max(2, drop_count)):
                seeds_list.append(
                    SunflowerSeed(
                        self.rect.centerx,
                        self.rect.centery - 6,
                        vx=random.uniform(-190, 190),
                        vy=random.uniform(-340, -180),
                    )
                )

            if self.is_player or (attacker is not None and attacker.is_player):
                sounds.play("kill")
            return True

        if self.is_player or (attacker is not None and attacker.is_player):
            sounds.play("hit")
        return False

    def respawn(self, spawns: list[tuple[int, int]]):
        if not self.is_player and spawns:
            sx, sy = random.choice(spawns)
        else:
            sx, sy = self.spawn_x, self.spawn_y
        self.rect.center = (int(sx), int(sy))
        self.vx = 0.0
        self.vy = 0.0
        self.hp = self.max_hp
        self.alive = True
        self.invuln_timer = 1.6
        self.jumps_left = 2

    def apply_powerup(self, kind: str, texts: list[FloatingText], sounds):
        info = POWERUP_TYPES[kind]
        if kind == "speed":
            self.speed_timer = info["duration"]
        elif kind == "shield":
            self.shield_timer = info["duration"]
        elif kind == "damage":
            self.damage_timer = info["duration"]
        elif kind == "heal":
            self.hp = min(self.max_hp, self.hp + 50)

        if self.is_player:
            sounds.play("powerup")
            texts.append(FloatingText(self.rect.centerx, self.rect.top - 16, f"{info['name']}!", info["color"], 1.1))

    def update_timers(self, dt: float):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown = max(0.0, self.shoot_cooldown - dt)
        if self.invuln_timer > 0:
            self.invuln_timer = max(0.0, self.invuln_timer - dt)
        if self.hurt_flash > 0:
            self.hurt_flash = max(0.0, self.hurt_flash - dt)
        if self.speed_timer > 0:
            self.speed_timer = max(0.0, self.speed_timer - dt)
        if self.shield_timer > 0:
            self.shield_timer = max(0.0, self.shield_timer - dt)
        if self.damage_timer > 0:
            self.damage_timer = max(0.0, self.damage_timer - dt)
        if self.coyote_timer > 0:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)
        if self.squash_timer > 0:
            self.squash_timer = max(0.0, self.squash_timer - dt)

    def move_and_collide(self, dt: float, level, seeds_list, powerups_list, particles, texts, sounds):
        """Fizyka platformówki 2D z kolizjami i uderzaniem w bloki '?' od dołu!"""
        self.vy = min(MAX_FALL_SPEED, self.vy + GRAVITY * dt)

        # 1. Ruch w poziomie (oś X)
        self.rect.x += int(round(self.vx * dt))
        hit_wall = False
        for solid in level.solids:
            if self.rect.colliderect(solid):
                hit_wall = True
                if self.vx > 0:
                    self.rect.right = solid.left
                elif self.vx < 0:
                    self.rect.left = solid.right
                self.vx = 0.0

        # 2. Ruch w pionie (oś Y)
        was_on_ground = self.on_ground
        self.on_ground = False
        self.rect.y += int(round(self.vy * dt))

        for solid in level.solids:
            if self.rect.colliderect(solid):
                if self.vy > 0:
                    # Lądowanie na podłodze lub platformie
                    self.rect.bottom = solid.top
                    self.vy = 0.0
                    self.on_ground = True
                    self.jumps_left = 2
                elif self.vy < 0:
                    # Uderzenie głową w sufit lub blok '?'!
                    self.rect.top = solid.bottom
                    self.vy = 40.0
                    for qb in level.question_blocks:
                        if qb.rect == solid and qb.trigger():
                            self._spawn_question_reward(qb.rect, seeds_list, powerups_list, particles, texts, sounds)

        if was_on_ground and not self.on_ground and self.vy >= 0:
            self.coyote_timer = 0.11

        # 3. Sprężyste grzybki-trampoliny + fala uderzeniowa!
        for sp in level.springs:
            if self.rect.colliderect(sp) and self.vy >= -40:
                self.vy = -SPRING_JUMP_SPEED
                self.on_ground = False
                self.jumps_left = 1
                self.squash_timer = 0.18
                particles.append(ShockwaveRing(sp.centerx, sp.top, (255, 110, 115), max_radius=36, life=0.28, width=3))
                spawn_burst(particles, sp.centerx, sp.top, (255, 120, 120), count=10, speed=180)
                if self.is_player:
                    sounds.play("spring")

        # Animacja biegania + iskierki wokół legendarnych skórek!
        if self.on_ground and abs(self.vx) > 25:
            self.walk_phase += dt * 14.0
        else:
            self.walk_phase = 0.0

        if self.skin_id in ("ogien", "lod", "zloty", "diament", "galaktyka"):
            self.sparkle_timer -= dt
            if self.sparkle_timer <= 0:
                self.sparkle_timer = 0.22
                scol = {
                    "ogien": (255, 145, 45),
                    "lod": (165, 240, 255),
                    "zloty": (255, 232, 95),
                    "diament": (150, 255, 255),
                    "galaktyka": (185, 145, 255),
                }[self.skin_id]
                particles.append(
                    Particle(
                        self.rect.centerx + random.uniform(-14, 14),
                        self.rect.centery + random.uniform(-14, 12),
                        random.uniform(-18, 18),
                        random.uniform(-45, -18),
                        scol,
                        random.uniform(2.2, 3.8),
                        0.45,
                        gravity=-20.0,
                    )
                )

        return hit_wall

    def _spawn_question_reward(self, block_rect: pygame.Rect, seeds_list, powerups_list, particles, texts, sounds):
        """Nagroda wyskakująca z bloku '?' w stylu Mario!"""
        bx = block_rect.centerx
        by = block_rect.top - 12
        spawn_burst(particles, bx, by, GOLD, count=12, speed=190)
        if self.is_player:
            sounds.play("block_hit")

        # 35% szans na power-up, 65% szans na fontannę ziaren słonecznika!
        if random.random() < 0.35:
            kind = random.choice(list(POWERUP_TYPES.keys()))
            powerups_list.append(PowerUp(bx, by, kind))
            if self.is_player:
                texts.append(FloatingText(bx, by - 12, "POWER-UP!", GOLD, 1.0))
        else:
            count = random.randint(2, 4)
            for _ in range(count):
                seeds_list.append(
                    SunflowerSeed(bx, by, vx=random.uniform(-140, 140), vy=random.uniform(-320, -210))
                )
            if self.is_player:
                texts.append(FloatingText(bx, by - 12, f"+{count} Ziarna!", GOLD, 0.9))

    def update_ai(
        self,
        dt: float,
        level,
        all_fighters: list["Hamster"],
        seeds_list: list[SunflowerSeed],
        powerups_list: list[PowerUp],
        bullets: list[Bullet],
        particles: list[Particle],
        texts: list[FloatingText],
        sounds,
    ):
        """Sztuczna inteligencja dla 7 atakujących botów."""
        self.update_timers(dt)
        if not self.alive:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.respawn(level.bot_spawns)
            return

        self.ai_change_timer -= dt
        self.ai_jump_cooldown = max(0.0, self.ai_jump_cooldown - dt)
        self.ai_shoot_delay = max(0.0, self.ai_shoot_delay - dt)

        # 1. Szukaj najbliższego przeciwnika (gracza lub innego bota!)
        target_enemy = None
        best_dist = 99999.0
        for other in all_fighters:
            if other is self or not other.alive:
                continue
            d = math.hypot(other.rect.centerx - self.rect.centerx, other.rect.centery - self.rect.centery)
            # Preferencja na gracza zależy od wybranego poziomu trudności
            score = d * (self.difficulty["bot_player_focus"] if other.is_player else 1.0)
            if score < best_dist:
                best_dist = score
                target_enemy = other

        # 2. Szukaj pobliskiego ziarna słonecznika do zebrania
        nearest_seed = None
        seed_dist = 240.0
        for s in seeds_list:
            if not s.alive:
                continue
            d = math.hypot(s.x - self.rect.centerx, s.y - self.rect.centery)
            if d < seed_dist:
                seed_dist = d
                nearest_seed = s

        # 3. Decyzja o kierunku ruchu
        speed = self.get_move_speed()
        desired_dir = self.ai_dir

        if nearest_seed is not None and (target_enemy is None or best_dist > 170):
            desired_dir = 1 if nearest_seed.x > self.rect.centerx else -1
            if nearest_seed.y < self.rect.centery - 45 and self.ai_jump_cooldown <= 0:
                self.try_jump(particles, sounds)
                self.ai_jump_cooldown = 0.55
        elif target_enemy is not None:
            dx = target_enemy.rect.centerx - self.rect.centerx
            dy = target_enemy.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            # Snajper AWP trzyma większy dystans, Shotgun podchodzi bliżej!
            pref_dist = 360 if self.weapon_id == "awp" else (110 if self.weapon_id == "shotgun" else 220)
            if dist > pref_dist + 40:
                desired_dir = 1 if dx > 0 else -1
            elif dist < pref_dist - 50:
                desired_dir = -1 if dx > 0 else 1
            elif self.ai_change_timer <= 0:
                desired_dir = random.choice([-1, 1])
                self.ai_change_timer = random.uniform(0.6, 1.5)

            # Skacz, jeśli przeciwnik jest na wyższej platformie
            if dy < -60 and self.ai_jump_cooldown <= 0 and random.random() < 0.08:
                self.try_jump(particles, sounds)
                self.ai_jump_cooldown = 0.65
        else:
            if self.ai_change_timer <= 0:
                desired_dir = random.choice([-1, 1])
                self.ai_change_timer = random.uniform(1.0, 2.5)

        self.ai_dir = desired_dir
        target_vx = desired_dir * speed
        self.vx += (target_vx - self.vx) * min(1.0, 9.0 * dt)

        hit_wall = self.move_and_collide(dt, level, seeds_list, powerups_list, particles, texts, sounds)
        if hit_wall:
            if self.ai_jump_cooldown <= 0:
                self.try_jump(particles, sounds)
                self.ai_jump_cooldown = 0.45
            else:
                self.ai_dir *= -1

        # Losowy skok po platformach, żeby boty zwiedzały całą mapę
        if self.on_ground and self.ai_jump_cooldown <= 0 and random.random() < 0.008:
            self.try_jump(particles, sounds)
            self.ai_jump_cooldown = 0.8

        # 4. Celowanie i strzelanie do przeciwnika
        if target_enemy is not None:
            dx = target_enemy.rect.centerx - self.rect.centerx
            dy = target_enemy.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            self.aim_angle = math.atan2(dy, dx)
            self.facing_right = dx >= 0

            max_range = 620 if self.weapon_id == "awp" else (270 if self.weapon_id == "shotgun" else 460)
            if dist < max_range and self.ai_shoot_delay <= 0:
                # Proste sprawdzenie, czy między botem a celem nie ma grubego muru
                mid_x = (self.rect.centerx + target_enemy.rect.centerx) * 0.5
                mid_y = (self.rect.centery + target_enemy.rect.centery) * 0.5
                if not level.point_hits_solid(mid_x, mid_y):
                    self.try_shoot(bullets, particles, sounds)
                    self.ai_shoot_delay = random.uniform(0.18, 0.55)
        else:
            self.facing_right = self.vx >= 0
            self.aim_angle = 0.0 if self.facing_right else math.pi

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, level, name_font: pygame.font.Font):
        if not self.alive:
            return

        cx = int(self.rect.centerx - cam_x)
        cy = int(self.rect.centery - cam_y)

        # Czerwony laser celowniczy dla snajperki AWP!
        if self.weapon_id == "awp" and self.is_player:
            ex, ey = level.raycast_wall(self.rect.centerx, self.rect.centery, self.aim_angle)
            pygame.draw.line(surf, (255, 60, 60), (cx, cy), (int(ex - cam_x), int(ey - cam_y)), 1)

        # Efekt migania podczas nietykalności po odrodzeniu
        if self.invuln_timer > 0 and int(self.invuln_timer * 14) % 2 == 0:
            return

        # Dynamiczny cień 3D rzucany na platformę pod chomikiem (nawet w trakcie skoku — jak w Super Mario 3D World!)
        ground_y = level.find_ground_y(self.rect.centerx, self.rect.bottom - 2)
        if ground_y is not None:
            height_above = max(0.0, ground_y - self.rect.bottom)
            if height_above < 260.0:
                factor = 1.0 - (height_above / 260.0)
                sh_w = max(12, int(38 * (0.45 + 0.55 * factor)))
                sh_h = max(4, int(11 * (0.45 + 0.55 * factor)))
                sh_alpha = int(115 * factor)
                sh = pygame.Surface((sh_w, sh_h), pygame.SRCALPHA)
                pygame.draw.ellipse(sh, (14, 24, 38, sh_alpha), (0, 0, sh_w, sh_h))
                surf.blit(sh, (cx - sh_w // 2, int(ground_y - cam_y) - sh_h // 2 - 2))

        bob = abs(math.sin(self.walk_phase)) * -3.5 if self.on_ground else 0.0
        jump_lift = -3.0 * (self.squash_timer / 0.16) if self.squash_timer > 0 else 0.0
        body_col = WHITE if self.hurt_flash > 0 else self.body_override

        draw_hamster_avatar(
            surf,
            cx,
            cy,
            self.skin_id,
            self.facing_right,
            self.aim_angle,
            body_override=body_col,
            bob_y=bob + jump_lift,
            walk_phase=self.walk_phase,
        )

        # Rysuj broń obracającą się w stronę kursora
        draw_weapon_on_hamster(surf, cx, cy + int(bob), self.aim_angle, self.weapon_id)

        # Bańka tarczy (power-up)
        if self.shield_timer > 0:
            pygame.draw.circle(surf, (90, 210, 255), (cx, cy), 25, 3)

        # Fioletowa aura Mega-Strzału (2x obrażenia)
        if self.damage_timer > 0:
            pygame.draw.circle(surf, (215, 110, 255), (cx, cy), 22, 2)

        # Imię i pasek HP nad głową (wyżej, żeby nigdy nie zasłaniały czapek ze skinów!)
        bar_w = 38
        bar_h = 5
        bx = cx - bar_w // 2
        by = cy - 41
        pygame.draw.rect(surf, (30, 30, 35), (bx - 1, by - 1, bar_w + 2, bar_h + 2))
        hp_ratio = max(0.0, self.hp / max(1, self.max_hp))
        hp_col = GREEN if self.is_player else (RED if hp_ratio < 0.4 else (245, 155, 55))
        pygame.draw.rect(surf, hp_col, (bx, by, int(bar_w * hp_ratio), bar_h))

        label_col = GOLD if self.is_player else WHITE
        lbl = name_font.render(self.name, True, label_col)
        lbl_shadow = name_font.render(self.name, True, (20, 20, 25))
        surf.blit(lbl_shadow, (cx - lbl.get_width() // 2 + 1, by - 16))
        surf.blit(lbl, (cx - lbl.get_width() // 2, by - 17))


class StoryBot:
    """Bot fabularny (NPC) stojący na mapie — daje zadania, opowiada historię lub otwiera sklep!"""

    def __init__(self, npc_id: str, name: str, role: str, x: float, y: float, hat: str, skin_id: str, lines: list[str]):
        self.npc_id = npc_id
        self.name = name
        self.role = role
        self.x = x
        self.y = y
        self.hat = hat
        self.skin_id = skin_id
        self.lines = lines
        self.age = random.uniform(0, 6.28)
        self.rect = pygame.Rect(int(x - 20), int(y - 20), 40, 40)

    def update(self, dt: float):
        self.age += dt

    def is_near(self, player: Hamster) -> bool:
        if not player.alive:
            return False
        return math.hypot(player.rect.centerx - self.x, player.rect.centery - self.y) < 78

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, player: Hamster, font: pygame.font.Font, quest_ready: bool = False):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        bob = math.sin(self.age * 3.2) * 2.5
        facing = player.rect.centerx >= self.x

        # Złota podświetlona strefa bezpieczna pod NPC
        pygame.draw.ellipse(surf, (255, 240, 140), (sx - 24, sy + 12, 48, 10), 2)

        draw_hamster_avatar(
            surf,
            sx,
            sy,
            self.skin_id,
            facing,
            0.0 if facing else math.pi,
            bob_y=bob,
            hat_override=self.hat,
        )

        # Wykrzyknik '!' lub dymek nad głową bota fabularnego
        badge_y = sy - 44 + int(math.sin(self.age * 5.0) * 3)
        if self.is_near(player):
            prompt = font.render(f"[E] {self.name}", True, (25, 25, 35))
            box = pygame.Rect(sx - prompt.get_width() // 2 - 8, badge_y - 10, prompt.get_width() + 16, 22)
            pygame.draw.rect(surf, GOLD, box, border_radius=6)
            pygame.draw.rect(surf, (40, 30, 15), box, 2, border_radius=6)
            surf.blit(prompt, (box.x + 8, box.y + 2))
        else:
            tag = font.render(self.name, True, (255, 245, 190))
            shadow = font.render(self.name, True, (25, 25, 30))
            surf.blit(shadow, (sx - tag.get_width() // 2 + 1, badge_y - 4))
            surf.blit(tag, (sx - tag.get_width() // 2, badge_y - 5))

            if self.npc_id == "mistrz":
                mark = "!" if quest_ready else "?"
                m_col = GREEN if quest_ready else GOLD
                m_surf = font.render(mark, True, (25, 25, 30))
                pygame.draw.circle(surf, m_col, (sx, badge_y - 16), 10)
                pygame.draw.circle(surf, (30, 30, 35), (sx, badge_y - 16), 10, 2)
                surf.blit(m_surf, (sx - m_surf.get_width() // 2, badge_y - 16 - m_surf.get_height() // 2))
