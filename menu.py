"""
Dungeon Explorer — Menus
Title screen (with animated dungeon background) and Game Over screen.
"""
import math
import os
import pygame
from settings import (
    ASSETS_DIR, SCREEN_WIDTH, SCREEN_HEIGHT, HALF_WIDTH, HALF_HEIGHT,
    COLOR_WHITE, COLOR_SCORE, FPS,
)


class MenuBase:
    """Shared utilities for menu screens."""

    def __init__(self, screen):
        self.screen = screen

        font_path = os.path.join(ASSETS_DIR, 'ui', 'Font', 'Kenney Future.ttf')
        if os.path.exists(font_path):
            self.font_title = pygame.font.Font(font_path, 52)
            self.font_sub = pygame.font.Font(font_path, 24)
            self.font_body = pygame.font.Font(font_path, 18)
            self.font_small = pygame.font.Font(font_path, 14)
        else:
            self.font_title = pygame.font.SysFont('consolas', 52, bold=True)
            self.font_sub = pygame.font.SysFont('consolas', 24)
            self.font_body = pygame.font.SysFont('consolas', 18)
            self.font_small = pygame.font.SysFont('consolas', 14)

        # Load button image
        btn_path = os.path.join(ASSETS_DIR, 'ui', 'PNG', 'Blue', 'Default',
                                'button_rectangle_depth_flat.png')
        self.btn_img = None
        if os.path.exists(btn_path):
            self.btn_img = pygame.image.load(btn_path).convert_alpha()

        # Load click sound
        click_path = os.path.join(ASSETS_DIR, 'ui', 'Sounds', 'click-a.ogg')
        self.click_snd = None
        if os.path.exists(click_path):
            self.click_snd = pygame.mixer.Sound(click_path)
            self.click_snd.set_volume(0.5)

        self.particles = [self._random_particle() for _ in range(60)]

    @staticmethod
    def _random_particle():
        import random
        return {
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(0, SCREEN_HEIGHT),
            'r': random.uniform(1, 3),
            'speed': random.uniform(0.2, 0.8),
            'alpha': random.randint(30, 120),
            'color': random.choice([
                (100, 180, 255), (150, 120, 255), (255, 200, 100),
                (80, 220, 180), (200, 200, 255),
            ]),
        }

    def _draw_background(self, time_ms):
        """Animated dark dungeon background with floating particles."""
        self.screen.fill((8, 6, 14))

        # Subtle gradient
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(8 + t * 15)
            g = int(6 + t * 10)
            b = int(14 + t * 25)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Floating particles
        for p in self.particles:
            p['y'] -= p['speed']
            if p['y'] < -10:
                p['y'] = SCREEN_HEIGHT + 10
                p['x'] = __import__('random').randint(0, SCREEN_WIDTH)

            x_offset = math.sin(time_ms * 0.001 + p['x'] * 0.01) * 15
            surf = pygame.Surface((int(p['r'] * 4), int(p['r'] * 4)),
                                  pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p['color'], p['alpha']),
                               (int(p['r'] * 2), int(p['r'] * 2)),
                               int(p['r']))
            self.screen.blit(surf, (p['x'] + x_offset, p['y']))

    def _draw_button(self, text, cx, cy, width=280, height=56):
        """Draw a styled button and return its rect for click detection."""
        rect = pygame.Rect(cx - width // 2, cy - height // 2, width, height)

        mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos)

        if self.btn_img:
            scaled = pygame.transform.scale(self.btn_img, (width, height))
            if hovered:
                bright = pygame.Surface(scaled.get_size())
                bright.fill((30, 30, 30))
                scaled.blit(bright, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            self.screen.blit(scaled, rect.topleft)
        else:
            color = (60, 120, 200) if hovered else (40, 80, 160)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 160, 240), rect, 2,
                             border_radius=8)

        txt = self.font_sub.render(text, True, COLOR_WHITE)
        self.screen.blit(txt, (cx - txt.get_width() // 2,
                               cy - txt.get_height() // 2))
        return rect


class TitleMenu(MenuBase):
    """Main title screen shown at game start."""

    def __init__(self, screen):
        super().__init__(screen)
        self.difficulties = ['easy', 'normal', 'hard']
        self.diff_idx = 1
        self.play_btn = pygame.Rect(0, 0, 0, 0)
        self.diff_btn = pygame.Rect(0, 0, 0, 0)

    @property
    def difficulty(self):
        return self.difficulties[self.diff_idx]

    def render(self, time_ms):
        self._draw_background(time_ms)

        # Title with shadow
        title_y = SCREEN_HEIGHT // 4
        shadow = self.font_title.render('DUNGEON EXPLORER', True, (20, 15, 40))
        self.screen.blit(shadow, (HALF_WIDTH - shadow.get_width() // 2 + 3,
                                  title_y + 3))

        # Pulsing title color
        pulse = int(200 + 55 * math.sin(time_ms * 0.002))
        title = self.font_title.render('DUNGEON EXPLORER', True,
                                       (pulse, 180, 255))
        self.screen.blit(title, (HALF_WIDTH - title.get_width() // 2,
                                 title_y))

        # Subtitle
        sub = self.font_body.render('Explore the depths. Collect crystals. Survive.',
                                    True, (150, 140, 180))
        self.screen.blit(sub, (HALF_WIDTH - sub.get_width() // 2,
                               title_y + 70))

        # Play button
        self.play_btn = self._draw_button('PLAY', HALF_WIDTH,
                                          SCREEN_HEIGHT // 2 + 10)
                                          
        # Difficulty button
        diff_text = f'DIFFICULTY: {self.difficulty.upper()}'
        self.diff_btn = self._draw_button(diff_text, HALF_WIDTH,
                                          SCREEN_HEIGHT // 2 + 80)

        # Controls info
        controls = [
            'Z/Q/S/D or Arrows — Move    |    MOUSE — Look',
            'LMB/SPACE — Attack    |    F — Fireball    |    RMB — Dodge',
            'E — Interact    |    I — Inventory    |    M — Map    |    ESC — Quit',
        ]
        y = SCREEN_HEIGHT * 3 // 4 + 20
        for line in controls:
            txt = self.font_small.render(line, True, (100, 95, 130))
            self.screen.blit(txt, (HALF_WIDTH - txt.get_width() // 2, y))
            y += 24

        # Footer
        footer = self.font_small.render(
            'Assets by Kenney.nl  |  CC0 License', True, (60, 55, 80))
        self.screen.blit(footer,
                         (HALF_WIDTH - footer.get_width() // 2,
                          SCREEN_HEIGHT - 30))

    def handle_click(self, pos):
        if self.play_btn.collidepoint(pos):
            if self.click_snd:
                self.click_snd.play()
            return 'play'
        elif self.diff_btn.collidepoint(pos):
            if self.click_snd:
                self.click_snd.play()
            self.diff_idx = (self.diff_idx + 1) % len(self.difficulties)
            return 'diff'
        return None


class GameOverMenu(MenuBase):
    """Game-over screen showing final stats."""

    def __init__(self, screen):
        super().__init__(screen)
        self.play_btn = pygame.Rect(0, 0, 0, 0)

    def render(self, time_ms, score, crystals, enemies_killed, level):
        self._draw_background(time_ms)

        # Title
        title_y = SCREEN_HEIGHT // 5
        shadow = self.font_title.render('GAME OVER', True, (60, 10, 10))
        self.screen.blit(shadow,
                         (HALF_WIDTH - shadow.get_width() // 2 + 3,
                          title_y + 3))

        pulse = int(200 + 55 * math.sin(time_ms * 0.003))
        title = self.font_title.render('GAME OVER', True, (pulse, 50, 50))
        self.screen.blit(title,
                         (HALF_WIDTH - title.get_width() // 2, title_y))

        # Stats panel
        panel_y = SCREEN_HEIGHT // 3 + 10
        panel = pygame.Surface((400, 180), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        pygame.draw.rect(panel, (80, 60, 120, 180), panel.get_rect(), 2,
                         border_radius=10)
        panel_x = HALF_WIDTH - 200
        self.screen.blit(panel, (panel_x, panel_y))

        stats = [
            (f'Final Score:  {score}', COLOR_SCORE),
            (f'Crystals Collected:  {crystals}', (120, 220, 255)),
            (f'Enemies Defeated:  {enemies_killed}', (255, 120, 100)),
            (f'Dungeon Level:  {level}', (180, 160, 255)),
        ]
        sy = panel_y + 20
        for text, color in stats:
            txt = self.font_body.render(text, True, color)
            self.screen.blit(txt, (HALF_WIDTH - txt.get_width() // 2, sy))
            sy += 38

        # Retry button
        self.play_btn = self._draw_button('PLAY AGAIN', HALF_WIDTH,
                                          SCREEN_HEIGHT * 3 // 4)

    def handle_click(self, pos):
        if self.play_btn.collidepoint(pos):
            if self.click_snd:
                self.click_snd.play()
            return 'play'
        return None
