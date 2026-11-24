"""
settings.py — Wszystkie najważniejsze ustawienia gry Hamster Shooter.
Możesz śmiało zmieniać tutaj liczby (np. grawitację, obrażenia broni albo ceny w sklepie),
żeby eksperymentować i uczyć się Pythona!
"""

import pygame

# --- Okno gry i świat (zamknięta mapa w stylu Mario) ---
SCREEN_W = 1200
SCREEN_H = 720
FPS = 60

TILE_SIZE = 40
MAP_COLS = 40  # 40 * 40 = 1600 px szerokości
MAP_ROWS = 22  # 22 * 40 = 880 px wysokości
WORLD_W = MAP_COLS * TILE_SIZE
WORLD_H = MAP_ROWS * TILE_SIZE

# --- Fizyka platformówki ---
GRAVITY = 1550.0        # Siła grawitacji (im większa, tym szybciej chomik spada)
MAX_FALL_SPEED = 900.0  # Maksymalna prędkość spadania
PLAYER_SPEED = 320.0    # Prędkość biegania gracza (piksele na sekundę)
JUMP_SPEED = 610.0      # Siła pierwszego skoku
DOUBLE_JUMP_SPEED = 560.0  # Siła podwójnego skoku w powietrzu
SPRING_JUMP_SPEED = 860.0  # Siła wybicia ze sprężyny/grzybka

# --- Zasady gry ---
WIN_SEEDS_GOAL = 50       # Ile ziaren trzeba zebrać, aby wygrać rundę
NUM_COMBAT_BOTS = 7       # Liczba atakujących botów na arenie
MAX_MAP_SEEDS = 18        # Maksymalna liczba luźnych ziaren leżących naraz na mapie
SEED_SPAWN_INTERVAL = 2.2 # Co ile sekund pojawia się nowe ziarno na mapie
BOT_DAMAGE_MULT = 0.65    # Domyślny mnożnik obrażeń botów

# --- Poziomy trudności ---
DIFFICULTIES = {
    "latwy": {
        "name": "Łatwy",
        "color": (70, 205, 95),
        "bot_hp": 75,
        "bot_speed_mult": 0.60,
        "bot_damage_mult": 0.40,
        "bot_cooldown_mult": 2.10,
        "bot_spread_deg": 12.0,
        "bot_player_focus": 0.95,
        "desc": "Boty są wolniejsze, mają mniej HP i częściej pudłują.",
    },
    "normalny": {
        "name": "Normalny",
        "color": (255, 212, 59),
        "bot_hp": 100,
        "bot_speed_mult": 0.72,
        "bot_damage_mult": 0.65,
        "bot_cooldown_mult": 1.55,
        "bot_spread_deg": 7.0,
        "bot_player_focus": 0.85,
        "desc": "Zbalansowana walka z 7 botami o ziarna słonecznika.",
    },
    "trudny": {
        "name": "Trudny",
        "color": (235, 70, 70),
        "bot_hp": 130,
        "bot_speed_mult": 0.88,
        "bot_damage_mult": 1.00,
        "bot_cooldown_mult": 1.12,
        "bot_spread_deg": 2.5,
        "bot_player_focus": 0.65,
        "desc": "Dla mistrzów! Szybkie, celne i wytrzymałe boty.",
    },
}

DIFFICULTY_ORDER = ["latwy", "normalny", "trudny"]

# --- Kolory (RGB) ---
SKY_TOP = (100, 185, 255)
SKY_BOTTOM = (180, 230, 255)
WHITE = (255, 255, 255)
BLACK = (20, 20, 25)
DARK_UI = (26, 30, 44)
GOLD = (255, 212, 59)
SUNFLOWER_DARK = (65, 55, 45)
SUNFLOWER_LIGHT = (240, 225, 190)
RED = (230, 65, 65)
GREEN = (70, 205, 95)
BLUE = (75, 165, 255)
PURPLE = (175, 95, 245)
ORANGE = (245, 145, 45)

# --- Definicje broni ---
# Kolejność klawiszy: 1 = ziarna, 2 = karabin, 3 = shotgun, 4 = awp
WEAPONS = {
    "ziarna": {
        "name": "Miotacz Ziaren",
        "key": "1",
        "cost": 0,
        "damage": 18,
        "cooldown": 0.24,
        "speed": 700,
        "pellets": 1,
        "spread_deg": 3.5,
        "recoil": 35,
        "color": (245, 215, 110),
        "desc": "Podstawowa broń strzelająca łupinkami słonecznika.",
    },
    "karabin": {
        "name": "Karabin Chomik-AR",
        "key": "2",
        "cost": 14,
        "damage": 14,
        "cooldown": 0.11,
        "speed": 860,
        "pellets": 1,
        "spread_deg": 5.5,
        "recoil": 45,
        "color": (255, 175, 60),
        "desc": "Szybkostrzelny karabin automatyczny na średni dystans.",
    },
    "shotgun": {
        "name": "Shotgun Orzechowy",
        "key": "3",
        "cost": 22,
        "damage": 13,
        "cooldown": 0.68,
        "speed": 740,
        "pellets": 6,
        "spread_deg": 22.0,
        "recoil": 170,
        "color": (255, 110, 50),
        "desc": "Wystrzeliwuje 6 śrucin naraz! Potężny z bliska.",
    },
    "awp": {
        "name": "Snajperka AWP",
        "key": "4",
        "cost": 35,
        "damage": 88,
        "cooldown": 1.15,
        "speed": 1500,
        "pellets": 1,
        "spread_deg": 0.0,
        "recoil": 220,
        "color": (255, 70, 70),
        "desc": "Celownik laserowy i potężny pocisk. Prawie jeden strzał!",
    },
}

WEAPON_ORDER = ["ziarna", "karabin", "shotgun", "awp"]

# --- Skórki chomików do odblokowania w sklepie ---
SKINS = {
    "klasyczny": {
        "name": "Klasyczny",
        "cost": 0,
        "body": (215, 150, 85),
        "belly": (250, 232, 200),
        "ear": (240, 170, 175),
        "accent": (180, 115, 55),
        "desc": "Złocisty chomik gotowy do walki o słonecznik.",
    },
    "ninja": {
        "name": "Chomik Ninja",
        "cost": 12,
        "body": (55, 58, 70),
        "belly": (95, 100, 115),
        "ear": (75, 78, 92),
        "accent": (225, 45, 55),
        "desc": "Czarne futerko i czerwona opaska mistrza cienia.",
    },
    "rycerz": {
        "name": "Rycerz",
        "cost": 18,
        "body": (185, 195, 210),
        "belly": (230, 235, 242),
        "ear": (150, 160, 175),
        "accent": (220, 50, 60),
        "desc": "Stalowy hełm i czerwony pióropusz odważnego chomika.",
    },
    "kosmita": {
        "name": "Kosmita",
        "cost": 22,
        "body": (105, 220, 110),
        "belly": (185, 250, 175),
        "ear": (75, 185, 85),
        "accent": (255, 240, 90),
        "desc": "Zielony przybysz z planety Wielkiego Słonecznika.",
    },
    "cyber": {
        "name": "Cyber-Chomik",
        "cost": 28,
        "body": (50, 75, 130),
        "belly": (105, 150, 215),
        "ear": (40, 60, 105),
        "accent": (50, 245, 255),
        "desc": "Futurystyczny pancerz i świecący neonowy wizjer.",
    },
    "krol": {
        "name": "Król Ziaren",
        "cost": 36,
        "body": (245, 200, 100),
        "belly": (255, 245, 210),
        "ear": (245, 180, 165),
        "accent": (210, 35, 65),
        "desc": "Złota korona i królewska peleryna władcy areny!",
    },
    # --- 16 dodatkowych skórek chomików ---
    "pirat": {
        "name": "Chomik Pirat",
        "cost": 14,
        "body": (185, 115, 65),
        "belly": (240, 215, 180),
        "ear": (220, 150, 145),
        "accent": (35, 35, 42),
        "desc": "Kapelusz pirata i opaska na oko postrachu mórz!",
    },
    "szef_kuchni": {
        "name": "Kucharz",
        "cost": 14,
        "body": (235, 195, 145),
        "belly": (255, 248, 235),
        "ear": (245, 185, 185),
        "accent": (250, 250, 255),
        "desc": "Mistrz prażonego słonecznika w wysokiej czapce!",
    },
    "kowboj": {
        "name": "Kowboj",
        "cost": 15,
        "body": (198, 132, 72),
        "belly": (245, 224, 190),
        "ear": (225, 155, 145),
        "accent": (215, 48, 48),
        "desc": "Dziki Zachód! Kapelusz i czerwona chustka szeryfa.",
    },
    "czarodziej": {
        "name": "Czarodziej",
        "cost": 16,
        "body": (125, 105, 195),
        "belly": (210, 200, 245),
        "ear": (165, 140, 220),
        "accent": (255, 215, 65),
        "desc": "Magiczna czapka z gwiazdkami i moc zaklęć!",
    },
    "panda": {
        "name": "Chomik Panda",
        "cost": 16,
        "body": (245, 245, 248),
        "belly": (255, 255, 255),
        "ear": (32, 34, 40),
        "accent": (32, 34, 40),
        "desc": "Biało-czarny słodziak z uroczymi łatkami wokół oczu.",
    },
    "zombie": {
        "name": "Zombie",
        "cost": 18,
        "body": (132, 168, 95),
        "belly": (175, 205, 135),
        "ear": (105, 138, 75),
        "accent": (185, 55, 75),
        "desc": "Powstał po jeszcze więcej chrupiących ziaren!",
    },
    "astronauta": {
        "name": "Astronauta",
        "cost": 20,
        "body": (235, 240, 248),
        "belly": (252, 254, 255),
        "ear": (210, 175, 185),
        "accent": (75, 185, 255),
        "desc": "Kosmiczny hełm gotowy na lot na księżyc!",
    },
    "wiking": {
        "name": "Wiking",
        "cost": 20,
        "body": (212, 128, 62),
        "belly": (248, 220, 185),
        "ear": (230, 155, 135),
        "accent": (165, 175, 190),
        "desc": "Rogaty hełm dzielnego wojownika z Północy!",
    },
    "duch": {
        "name": "Chomik Duch",
        "cost": 22,
        "body": (195, 232, 255),
        "belly": (235, 248, 255),
        "ear": (155, 210, 245),
        "accent": (255, 235, 95),
        "desc": "Upiornie szybki duszek ze świecącymi oczami!",
    },
    "samuraj": {
        "name": "Samuraj",
        "cost": 24,
        "body": (85, 88, 102),
        "belly": (155, 160, 175),
        "ear": (110, 112, 128),
        "accent": (215, 45, 50),
        "desc": "Honorowy wojownik w hełmie Kabuto ze złotym herbem.",
    },
    "wampir": {
        "name": "Wampir",
        "cost": 24,
        "body": (188, 188, 205),
        "belly": (230, 230, 242),
        "ear": (160, 150, 175),
        "accent": (185, 25, 45),
        "desc": "Mroczna peleryna, czerwone oczy i ostre kiełki!",
    },
    "robot": {
        "name": "Robo-Chomik",
        "cost": 26,
        "body": (145, 158, 175),
        "belly": (195, 208, 222),
        "ear": (110, 122, 138),
        "accent": (255, 75, 65),
        "desc": "Stalowy automat z antenką i cyfrowymi oczami.",
    },
    "ogien": {
        "name": "Chomik Ognia",
        "cost": 30,
        "body": (235, 95, 38),
        "belly": (255, 195, 75),
        "ear": (205, 55, 28),
        "accent": (255, 230, 65),
        "desc": "Płonąca grzywa ognia — gorący zawodnik areny!",
    },
    "lod": {
        "name": "Chomik Lodu",
        "cost": 30,
        "body": (115, 205, 245),
        "belly": (215, 248, 255),
        "ear": (85, 175, 225),
        "accent": (235, 252, 255),
        "desc": "Mroźna korona z kryształów lodu i zimna krew!",
    },
    "superbohater": {
        "name": "Super-Chomik",
        "cost": 32,
        "body": (65, 125, 225),
        "belly": (135, 185, 250),
        "ear": (50, 100, 195),
        "accent": (230, 45, 55),
        "desc": "Maska bohatera, czerwona peleryna i złota gwiazda!",
    },
    "diament": {
        "name": "Diamentowy",
        "cost": 45,
        "body": (65, 230, 225),
        "belly": (195, 255, 252),
        "ear": (45, 195, 200),
        "accent": (255, 255, 255),
        "desc": "Najrzadsza skórka! Lśniący kryształowy chomik!",
    },
    # --- 28 kolejnych skórek chomików (łącznie 50!) ---
    "policjant": {
        "name": "Policjant",
        "cost": 13,
        "body": (90, 120, 185),
        "belly": (175, 198, 238),
        "ear": (65, 90, 148),
        "accent": (255, 212, 59),
        "desc": "Czapka policyjna i złota odznaka stróża areny!",
    },
    "budowlaniec": {
        "name": "Budowlaniec",
        "cost": 13,
        "body": (210, 152, 92),
        "belly": (248, 226, 192),
        "ear": (235, 168, 165),
        "accent": (250, 210, 40),
        "desc": "Żółty kask ochronny — bloki '?' nie są mu straszne!",
    },
    "strazak": {
        "name": "Strażak",
        "cost": 14,
        "body": (205, 80, 62),
        "belly": (248, 208, 185),
        "ear": (175, 58, 45),
        "accent": (255, 215, 55),
        "desc": "Czerwony hełm strażacki gotowy na każdą akcję!",
    },
    "lekarz": {
        "name": "Lekarz",
        "cost": 14,
        "body": (238, 244, 250),
        "belly": (255, 255, 255),
        "ear": (242, 182, 190),
        "accent": (230, 48, 58),
        "desc": "Opaska z czerwonym krzyżykiem — zna każdą apteczkę!",
    },
    "pilkarz": {
        "name": "Piłkarz",
        "cost": 15,
        "body": (225, 168, 108),
        "belly": (252, 240, 222),
        "ear": (240, 172, 175),
        "accent": (225, 40, 50),
        "desc": "Biało-czerwona opaska mistrza boiska!",
    },
    "klaun": {
        "name": "Chomik Klaun",
        "cost": 15,
        "body": (248, 238, 225),
        "belly": (255, 250, 245),
        "ear": (245, 175, 190),
        "accent": (235, 45, 55),
        "desc": "Kolorowe loczki i wielki czerwony nos!",
    },
    "kotek": {
        "name": "Chomik Kot",
        "cost": 15,
        "body": (235, 148, 68),
        "belly": (255, 232, 198),
        "ear": (245, 172, 175),
        "accent": (175, 92, 32),
        "desc": "Spiczaste kocie uszka i urocze wąsiki!",
    },
    "piesek": {
        "name": "Chomik Pies",
        "cost": 15,
        "body": (218, 172, 118),
        "belly": (250, 235, 210),
        "ear": (145, 92, 52),
        "accent": (135, 82, 42),
        "desc": "Długie klapnięte uszka i brązowa łatka na oku!",
    },
    "detektyw": {
        "name": "Detektyw",
        "cost": 16,
        "body": (175, 132, 92),
        "belly": (235, 215, 188),
        "ear": (195, 145, 135),
        "accent": (118, 78, 45),
        "desc": "Czapka Sherlocka i złoty monokl tropiciela ziaren!",
    },
    "kroliczek": {
        "name": "Króliczek",
        "cost": 16,
        "body": (248, 238, 245),
        "belly": (255, 250, 255),
        "ear": (250, 172, 200),
        "accent": (250, 155, 195),
        "desc": "Bardzo długie uszy — skacze jeszcze chętniej!",
    },
    "magik": {
        "name": "Iluzjonista",
        "cost": 17,
        "body": (78, 72, 96),
        "belly": (235, 235, 245),
        "ear": (112, 102, 132),
        "accent": (220, 42, 62),
        "desc": "Elegancki czarny cylinder z czerwoną wstążką!",
    },
    "balwan": {
        "name": "Bałwanek",
        "cost": 17,
        "body": (242, 248, 255),
        "belly": (255, 255, 255),
        "ear": (205, 228, 245),
        "accent": (245, 130, 35),
        "desc": "Marchewkowy nosek, szalik i zimowy kapelusz!",
    },
    "mikolaj": {
        "name": "Mikołaj",
        "cost": 18,
        "body": (228, 175, 135),
        "belly": (255, 250, 245),
        "ear": (242, 178, 178),
        "accent": (220, 35, 45),
        "desc": "Czerwona czapka z pomponem i prezent pełen ziaren!",
    },
    "pszczolka": {
        "name": "Pszczółka",
        "cost": 18,
        "body": (248, 205, 48),
        "belly": (255, 235, 135),
        "ear": (50, 45, 38),
        "accent": (38, 34, 30),
        "desc": "Żółto-czarne paski, czułki i szybkie skrzydełka!",
    },
    "biedronka": {
        "name": "Biedronka",
        "cost": 18,
        "body": (228, 48, 52),
        "belly": (248, 175, 170),
        "ear": (38, 34, 36),
        "accent": (28, 28, 32),
        "desc": "Czerwona w czarne kropki — przynosi szczęście!",
    },
    "dynia": {
        "name": "Dynia",
        "cost": 19,
        "body": (238, 125, 32),
        "belly": (255, 175, 78),
        "ear": (195, 92, 22),
        "accent": (72, 178, 65),
        "desc": "Halloweenowa dynia z zieloną łodyżką i blaskiem!",
    },
    "kaktus": {
        "name": "Kaktus",
        "cost": 19,
        "body": (78, 172, 82),
        "belly": (142, 212, 132),
        "ear": (58, 138, 62),
        "accent": (250, 95, 165),
        "desc": "Kolczasty kaktus z różowym kwiatkiem na głowie!",
    },
    "mumia": {
        "name": "Mumia",
        "cost": 20,
        "body": (224, 214, 185),
        "belly": (242, 235, 212),
        "ear": (192, 182, 152),
        "accent": (255, 225, 70),
        "desc": "Starożytne bandaże i świecące złote oczy!",
    },
    "szkielet": {
        "name": "Szkielet",
        "cost": 21,
        "body": (235, 238, 242),
        "belly": (252, 252, 255),
        "ear": (195, 200, 210),
        "accent": (32, 34, 42),
        "desc": "Strasznie szybki kościotrup prosto z lochów!",
    },
    "rekin": {
        "name": "Chomik Rekin",
        "cost": 22,
        "body": (108, 148, 182),
        "belly": (225, 238, 248),
        "ear": (82, 118, 150),
        "accent": (72, 108, 140),
        "desc": "Wielka płetwa rekina na głowie i ostre ząbki!",
    },
    "gladiator": {
        "name": "Gladiator",
        "cost": 23,
        "body": (188, 138, 88),
        "belly": (238, 208, 170),
        "ear": (162, 115, 72),
        "accent": (218, 168, 52),
        "desc": "Brązowy hełm gladiatora z czerwonym grzebieniem!",
    },
    "gamer": {
        "name": "Pro-Gamer",
        "cost": 24,
        "body": (118, 72, 198),
        "belly": (185, 152, 242),
        "ear": (88, 52, 158),
        "accent": (65, 245, 195),
        "desc": "Neonowe słuchawki RGB z mikrofonem mistrza FPS!",
    },
    "jednorozec": {
        "name": "Jednorożec",
        "cost": 25,
        "body": (250, 188, 225),
        "belly": (255, 232, 248),
        "ear": (255, 150, 210),
        "accent": (255, 222, 85),
        "desc": "Magiczny pastelowy chomik ze złotym rogiem!",
    },
    "dj": {
        "name": "Chomik DJ",
        "cost": 25,
        "body": (72, 82, 115),
        "belly": (142, 158, 205),
        "ear": (55, 62, 88),
        "accent": (255, 95, 195),
        "desc": "Ciemne okulary i wielkie słuchawki króla imprezy!",
    },
    "faraon": {
        "name": "Faraon",
        "cost": 26,
        "body": (212, 165, 102),
        "belly": (248, 226, 182),
        "ear": (188, 142, 84),
        "accent": (42, 105, 215),
        "desc": "Królewskie nakrycie Nemes ze złotą kobrą!",
    },
    "smok": {
        "name": "Smoczy",
        "cost": 29,
        "body": (58, 165, 92),
        "belly": (235, 205, 105),
        "ear": (42, 128, 68),
        "accent": (235, 65, 45),
        "desc": "Smocze rogi i ogniste kolce legendarnej bestii!",
    },
    "zloty": {
        "name": "Złoty Chomik",
        "cost": 38,
        "body": (250, 202, 58),
        "belly": (255, 240, 155),
        "ear": (232, 175, 35),
        "accent": (255, 250, 190),
        "desc": "Cały ze szczerego złota ze świecącą aureolą!",
    },
    "galaktyka": {
        "name": "Galaktyczny",
        "cost": 50,
        "body": (34, 28, 72),
        "belly": (88, 62, 158),
        "ear": (55, 42, 112),
        "accent": (145, 232, 255),
        "desc": "Kosmiczny mistrz z pierścieniem Saturna i gwiazdami!",
    },
}

SKIN_ORDER = [
    "klasyczny",
    "ninja",
    "policjant",
    "budowlaniec",
    "pirat",
    "szef_kuchni",
    "strazak",
    "lekarz",
    "kowboj",
    "pilkarz",
    "klaun",
    "kotek",
    "piesek",
    "czarodziej",
    "panda",
    "detektyw",
    "kroliczek",
    "magik",
    "balwan",
    "rycerz",
    "zombie",
    "mikolaj",
    "pszczolka",
    "biedronka",
    "dynia",
    "kaktus",
    "astronauta",
    "wiking",
    "mumia",
    "szkielet",
    "kosmita",
    "duch",
    "rekin",
    "gladiator",
    "samuraj",
    "wampir",
    "gamer",
    "jednorozec",
    "dj",
    "robot",
    "faraon",
    "cyber",
    "smok",
    "ogien",
    "lod",
    "superbohater",
    "krol",
    "zloty",
    "diament",
    "galaktyka",
]

# --- Ulepszenia w sklepie ---
UPGRADES = {
    "max_hp": {
        "name": "Twarde Policzki (+25 HP)",
        "base_cost": 12,
        "max_level": 3,
        "desc": "Zwiększa Twoje maksymalne zdrowie o 25 i leczy do pełna.",
    },
    "speed": {
        "name": "Szybkie Łapki (+12% biegu)",
        "base_cost": 14,
        "max_level": 2,
        "desc": "Chomik biega i unika pocisków jeszcze szybciej!",
    },
}

# --- Power-upy na mapie ---
POWERUP_TYPES = {
    "speed": {"name": "Turbo Łapki", "color": (255, 220, 50), "duration": 8.0, "symbol": "S"},
    "shield": {"name": "Tarcza", "color": (70, 190, 255), "duration": 10.0, "symbol": "T"},
    "heal": {"name": "Apteczka", "color": (255, 85, 110), "duration": 0.0, "symbol": "+"},
    "damage": {"name": "Mega Strzał x2", "color": (200, 90, 255), "duration": 8.0, "symbol": "2x"},
}

# --- Imiona i konfiguracja 7 atakujących botów ---
COMBAT_BOT_PRESETS = [
    {"name": "Bąbel", "skin": "pirat", "weapon": "ziarna", "body_override": None},
    {"name": "Gryzek", "skin": "ninja", "weapon": "ziarna", "body_override": None},
    {"name": "Turbo", "skin": "kosmita", "weapon": "karabin", "body_override": None},
    {"name": "Pazur", "skin": "wiking", "weapon": "shotgun", "body_override": None},
    {"name": "Orzech", "skin": "panda", "weapon": "ziarna", "body_override": None},
    {"name": "Błysk", "skin": "cyber", "weapon": "karabin", "body_override": None},
    {"name": "Snajper", "skin": "samuraj", "weapon": "awp", "body_override": None},
]

# --- Zadania fabularne od Mistrza Ziarno ---
QUESTS = [
    {
        "id": "collect_10",
        "title": "Zbierz 10 ziaren słonecznika",
        "type": "seeds_collected",
        "target": 10,
        "reward": 10,
        "intro": "Witaj, młody chomiku! Naszą arenę opanowało 7 łakomych botów. Zbierz 10 ziaren słonecznika — bij w bloki '?' od dołu jak w Mario!",
        "done": "Świetna robota! Oto 10 bonusowych ziaren na start.",
    },
    {
        "id": "defeat_3",
        "title": "Pokonaj 3 wrogie boty",
        "type": "kills",
        "target": 3,
        "reward": 15,
        "intro": "Czas pokazać, kto tu rządzi! Celuj myszką i pokonaj 3 atakujące chomiki. Pamiętaj o podwójnym skoku!",
        "done": "Niesamowity cel! Łap 15 ziaren nagrody.",
    },
    {
        "id": "buy_weapon",
        "title": "Kup nową broń w Sklepie [B]",
        "type": "weapons_owned",
        "target": 2,
        "reward": 20,
        "intro": "Ziarna to dobry początek, ale potrzebujesz cięższego sprzętu! Wciśnij [B] lub pogadaj z Kupcem Pysiem i kup Karabin, Shotgun lub AWP.",
        "done": "Nowa broń wygląda groźnie! Trzymaj jeszcze 20 ziaren.",
    },
    {
        "id": "reach_goal",
        "title": f"Zbierz łącznie {WIN_SEEDS_GOAL} ziaren!",
        "type": "seeds_collected",
        "target": WIN_SEEDS_GOAL,
        "reward": 30,
        "intro": f"Ostatnia próba! Zbierz łącznie {WIN_SEEDS_GOAL} ziaren słonecznika i zostań legendarnym Królem Chomików!",
        "done": "Udało się! Jesteś prawdziwym Mistrzem Słonecznika!",
    },
]


# --- Pomocnik do czcionek obsługujących polskie znaki (ą, ć, ę, ł, ń, ó, ś, ź, ż) ---
_FONT_CACHE = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _FONT_CACHE:
        try:
            font = pygame.font.SysFont("segoeui,arial,dejavusans,liberation sans", size, bold=bold)
        except Exception:
            font = pygame.font.Font(None, size)
        _FONT_CACHE[key] = font
    return _FONT_CACHE[key]
