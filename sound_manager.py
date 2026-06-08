"""
Dungeon Explorer — Sound Manager
Loads and plays all game audio using Kenney asset packs.
"""
import pygame
import os
import random
from settings import ASSETS_DIR


class SoundManager:
    """Manages all game audio: footsteps, combat, pickups, UI clicks, music."""

    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(16)

        self.sounds = {}
        self.footstep_sounds = []
        self.footstep_timer = 0
        self.footstep_interval = 350  # ms between footsteps

        self._load_sounds()
        self._start_music()

    # ── Loading ──────────────────────────────────────────────────────────
    def _load_sounds(self):
        sfx_dir = os.path.join(ASSETS_DIR, 'audio', 'sfx')
        ui_dir = os.path.join(ASSETS_DIR, 'ui', 'Sounds')

        # Footsteps (concrete surface for dungeon)
        for i in range(5):
            path = os.path.join(sfx_dir, f'footstep_concrete_{i:03d}.ogg')
            if os.path.exists(path):
                snd = pygame.mixer.Sound(path)
                snd.set_volume(0.25)
                self.footstep_sounds.append(snd)

        # Combat & interaction sounds (load multiple variants)
        sound_map = {
            'enemy_hit':      ('impactPunch_heavy', 0.5),
            'crystal_pickup': ('impactMetal_light',  0.45),
            'player_damage':  ('impactGlass_light',  0.4),
            'enemy_death':    ('impactGlass_heavy',  0.5),
            'attack_whoosh':  ('impactSoft_medium',  0.35),
        }
        for key, (prefix, vol) in sound_map.items():
            variants = []
            for i in range(5):
                path = os.path.join(sfx_dir, f'{prefix}_{i:03d}.ogg')
                if os.path.exists(path):
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(vol)
                    variants.append(snd)
            if variants:
                self.sounds[key] = variants

        # UI sounds
        for name in ('click-a', 'tap-a', 'switch-a'):
            path = os.path.join(ui_dir, f'{name}.ogg')
            if os.path.exists(path):
                snd = pygame.mixer.Sound(path)
                snd.set_volume(0.5)
                self.sounds[name] = [snd]

    def _start_music(self):
        music_dir = os.path.join(ASSETS_DIR, 'audio', 'music')
        if not os.path.isdir(music_dir):
            return
        files = [f for f in os.listdir(music_dir)
                 if f.endswith(('.ogg', '.mp3', '.wav'))]
        if files:
            pygame.mixer.music.load(os.path.join(music_dir, files[0]))
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)

    # ── Playback ─────────────────────────────────────────────────────────
    def play(self, sound_key):
        """Play a random variant of the named sound."""
        variants = self.sounds.get(sound_key)
        if variants:
            random.choice(variants).play()

    def play_footstep(self, current_time):
        """Play a footstep sound if enough time has elapsed."""
        if current_time - self.footstep_timer >= self.footstep_interval:
            if self.footstep_sounds:
                random.choice(self.footstep_sounds).play()
            self.footstep_timer = current_time
