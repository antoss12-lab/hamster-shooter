"""
sounds.py — Generator retro efektów dźwiękowych w czystym Pythonie.
Nie potrzebuje żadnych zewnętrznych plików .wav ani dodatkowych bibliotek!
Tworzy fale dźwiękowe w pamięci, dzięki czemu gra działa od razu i łatwo ją uruchomić też w przeglądarce.
"""

import io
import math
import random
import struct
import wave
import pygame


SAMPLE_RATE = 22050


def _make_wav_bytes(samples: list[float]) -> bytes:
    """Zamienia listę próbek (-1.0..1.0) na plik WAV w pamięci."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for s in samples:
            val = max(-1.0, min(1.0, s))
            frames += struct.pack("<h", int(val * 32767))
        wf.writeframes(bytes(frames))
    return buf.getvalue()


def _synth_tone(
    duration: float,
    freq_start: float,
    freq_end: float | None = None,
    wave_type: str = "square",
    volume: float = 0.25,
    noise_mix: float = 0.0,
) -> list[float]:
    """Tworzy prosty dźwięk retro (fala prostokątna, sinusoidalna, trójkątna lub szum)."""
    if freq_end is None:
        freq_end = freq_start
    total = max(1, int(SAMPLE_RATE * duration))
    samples = []
    phase = 0.0
    for i in range(total):
        t = i / total
        freq = freq_start + (freq_end - freq_start) * t
        phase += 2.0 * math.pi * freq / SAMPLE_RATE

        if wave_type == "square":
            sig = 1.0 if math.sin(phase) >= 0 else -1.0
        elif wave_type == "triangle":
            sig = (2.0 / math.pi) * math.asin(math.sin(phase))
        elif wave_type == "noise":
            sig = random.uniform(-1.0, 1.0)
        else:
            sig = math.sin(phase)

        if noise_mix > 0.0:
            sig = sig * (1.0 - noise_mix) + random.uniform(-1.0, 1.0) * noise_mix

        # Łagodne wyciszenie na końcu (bez trzasków)
        env = (1.0 - t) ** 1.3
        if i < 60:
            env *= i / 60.0
        samples.append(sig * volume * env)
    return samples


class SoundManager:
    """Zarządza wszystkimi dźwiękami w grze (z bezpiecznym trybem cichym)."""

    def __init__(self):
        self.enabled = True
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self._build_sounds()
        except Exception:
            # Jeśli komputer nie ma karty dźwiękowej, gra nadal zadziała bez błędu
            self.enabled = False

    def _register(self, name: str, samples: list[float]):
        wav_bytes = _make_wav_bytes(samples)
        self.sounds[name] = pygame.mixer.Sound(file=io.BytesIO(wav_bytes))

    def _build_sounds(self):
        # Skoki w stylu Mario
        self._register("jump", _synth_tone(0.14, 280, 620, "square", 0.18))
        self._register("double_jump", _synth_tone(0.16, 440, 880, "triangle", 0.22))
        self._register("spring", _synth_tone(0.26, 220, 950, "square", 0.22))

        # Uderzenie w blok '?' i zbieranie ziaren
        self._register("block_hit", _synth_tone(0.12, 520, 260, "square", 0.22))
        seed_samples = (
            _synth_tone(0.06, 987, 987, "square", 0.16)
            + _synth_tone(0.12, 1318, 1318, "square", 0.16)
        )
        self._register("seed", seed_samples)

        # Strzały dla każdej broni
        self._register("shoot_ziarna", _synth_tone(0.08, 620, 280, "triangle", 0.20, noise_mix=0.25))
        self._register("shoot_karabin", _synth_tone(0.09, 340, 120, "square", 0.22, noise_mix=0.45))
        self._register("shoot_shotgun", _synth_tone(0.22, 180, 55, "noise", 0.32))
        self._register("shoot_awp", _synth_tone(0.32, 260, 45, "square", 0.34, noise_mix=0.6))

        # Trafienie, pokonanie bota, power-up, sklep, dialog
        self._register("hit", _synth_tone(0.08, 220, 90, "square", 0.18, noise_mix=0.3))
        self._register("kill", _synth_tone(0.28, 420, 90, "square", 0.25, noise_mix=0.35))
        powerup_samples = (
            _synth_tone(0.07, 523, 659, "triangle", 0.20)
            + _synth_tone(0.07, 659, 784, "triangle", 0.20)
            + _synth_tone(0.12, 784, 1046, "triangle", 0.22)
        )
        self._register("powerup", powerup_samples)
        shop_samples = (
            _synth_tone(0.07, 660, 660, "square", 0.18)
            + _synth_tone(0.14, 990, 1180, "square", 0.20)
        )
        self._register("buy", shop_samples)
        self._register("error", _synth_tone(0.16, 170, 120, "square", 0.18))
        self._register("talk", _synth_tone(0.06, 480, 580, "triangle", 0.14))

    def play(self, name: str):
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd is not None:
            try:
                snd.play()
            except Exception:
                pass

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled
