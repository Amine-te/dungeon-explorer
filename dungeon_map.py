"""
Dungeon Explorer — Procedural Dungeon Map Generator
Creates randomised rooms connected by corridors, then places spawns.
"""
import math
import random
from settings import (
    WALL_STONE, WALL_BRICK, WALL_MOSSY, WALL_DARK, WALL_DOOR,
    MAP_WIDTH, MAP_HEIGHT, DOOR_INTERACT_RANGE,
    ENEMY_TYPE_CRAWLER, ENEMY_TYPE_SHADE, ENEMY_TYPE_BRUTE,
    ITEM_PICKUP_RANGE,
)


class Room:
    """Axis-aligned rectangular room."""

    def __init__(self, x, y, w, h):
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.cx = x + w // 2
        self.cy = y + h // 2

    def intersects(self, other, margin=2):
        return (self.x - margin < other.x + other.w and
                self.x + self.w + margin > other.x and
                self.y - margin < other.y + other.h and
                self.y + self.h + margin > other.y)


class DungeonMap:
    """
    Tile-grid dungeon with procedural generation.
    Grid values: 0 = floor, 1-5 = wall types (see settings.py).
    """

    def __init__(self, level=1):
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.level = level

        # Start fully walled
        self.grid = [[WALL_STONE] * self.width for _ in range(self.height)]
        self.rooms: list[Room] = []

        # Spawn data (filled by generate)
        self.player_spawn = (1.5, 1.5)
        self.crystal_positions: list[tuple[float, float]] = []
        self.enemy_spawns: list[tuple[float, float, str]] = []
        self.item_spawns: list[tuple[float, float, str]] = []
        self.door_positions: set[tuple[int, int]] = set()
        
        self.visited_cells: set[tuple[int, int]] = set()

        self._generate()

    # ── Public helpers ───────────────────────────────────────────────────
    def is_wall(self, x, y):
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= self.width or iy < 0 or iy >= self.height:
            return True
        return self.grid[iy][ix] != 0

    def get_wall_type(self, x, y):
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= self.width or iy < 0 or iy >= self.height:
            return WALL_STONE
        return self.grid[iy][ix]

    def is_door(self, x, y):
        return (int(x), int(y)) in self.door_positions

    def is_door_open(self, x, y):
        ix, iy = int(x), int(y)
        return (ix, iy) in self.door_positions and self.grid[iy][ix] == 0

    def find_nearby_door(self, px, py, max_dist=DOOR_INTERACT_RANGE):
        best = None
        best_dist = max_dist
        for dx, dy in self.door_positions:
            dist = math.hypot(px - (dx + 0.5), py - (dy + 0.5))
            if dist < best_dist:
                best_dist = dist
                best = (dx, dy)
        return best

    def get_door_prompt(self, door_pos):
        if door_pos is None:
            return None
        x, y = door_pos
        if self.grid[y][x] == 0:
            return 'Press E to close'
        return 'Press E to open'

    def toggle_door(self, x, y):
        if (x, y) not in self.door_positions:
            return False
        if self.grid[y][x] == 0:
            self.grid[y][x] = WALL_DOOR
        else:
            self.grid[y][x] = 0
        return True

    def find_nearby_item(self, px, py, world_items, max_dist=ITEM_PICKUP_RANGE):
        best = None
        best_dist = max_dist
        for wp in world_items:
            if wp.picked_up:
                continue
            dist = math.hypot(px - wp.x, py - wp.y)
            if dist < best_dist:
                best_dist = dist
                best = wp
        return best

    def get_interact_prompt(self, px, py, world_items):
        item = self.find_nearby_item(px, py, world_items)
        if item is not None:
            return f'Press E to pick up {item.item.label}'
        door = self.find_nearby_door(px, py)
        return self.get_door_prompt(door)
        
    def update_visited(self, px, py, radius=5):
        ix, iy = int(px), int(py)
        for y in range(iy - radius, iy + radius + 1):
            for x in range(ix - radius, ix + radius + 1):
                if 0 <= x < self.width and 0 <= y < self.height:
                    if (x - ix)**2 + (y - iy)**2 <= radius**2:
                        self.visited_cells.add((x, y))

    # ── Generation pipeline ──────────────────────────────────────────────
    def _generate(self):
        self._place_rooms()
        self._connect_rooms()
        self._add_wall_variety()
        self._place_doors()
        self._set_spawns()

    def _place_rooms(self):
        target = 6 + self.level * 2
        min_sz, max_sz = 4, 8
        attempts = 0
        while len(self.rooms) < target and attempts < 300:
            w = random.randint(min_sz, max_sz)
            h = random.randint(min_sz, max_sz)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            room = Room(x, y, w, h)
            if not any(room.intersects(r) for r in self.rooms):
                self.rooms.append(room)
                self._carve_room(room)
            attempts += 1

    def _carve_room(self, room):
        for ry in range(room.y, room.y + room.h):
            for rx in range(room.x, room.x + room.w):
                if 0 < rx < self.width - 1 and 0 < ry < self.height - 1:
                    self.grid[ry][rx] = 0

    def _connect_rooms(self):
        # Chain adjacent rooms
        for i in range(len(self.rooms) - 1):
            self._corridor(self.rooms[i], self.rooms[i + 1])
        # Extra loop connection for non-linear layout
        if len(self.rooms) > 3:
            self._corridor(self.rooms[-1], random.choice(self.rooms[:len(self.rooms) // 2]))

    def _corridor(self, a: Room, b: Room):
        x1, y1, x2, y2 = a.cx, a.cy, b.cx, b.cy
        if random.random() < 0.5:
            self._h_tunnel(x1, x2, y1)
            self._v_tunnel(y1, y2, x2)
        else:
            self._v_tunnel(y1, y2, x1)
            self._h_tunnel(x1, x2, y2)

    def _h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for dy in (0, -1):  # 2-wide corridor
                ny = y + dy
                if 0 < x < self.width - 1 and 0 < ny < self.height - 1:
                    self.grid[ny][x] = 0

    def _v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for dx in (0, -1):  # 2-wide corridor
                nx = x + dx
                if 0 < nx < self.width - 1 and 0 < y < self.height - 1:
                    self.grid[y][nx] = 0

    def _add_wall_variety(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 0:
                    continue
                r = random.random()
                if r < 0.15:
                    self.grid[y][x] = WALL_BRICK
                elif r < 0.25:
                    self.grid[y][x] = WALL_MOSSY
                elif r < 0.30:
                    self.grid[y][x] = WALL_DARK

    def _place_doors(self):
        """Place interactive doors on corridor wall tiles between floor cells."""
        candidates = []
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[y][x] == 0:
                    continue
                horizontal = self.grid[y][x - 1] == 0 and self.grid[y][x + 1] == 0
                vertical = self.grid[y - 1][x] == 0 and self.grid[y + 1][x] == 0
                if horizontal or vertical:
                    candidates.append((x, y))

        random.shuffle(candidates)
        count = min(len(candidates), max(3, self.level + 1))
        for x, y in candidates[:count]:
            self.grid[y][x] = WALL_DOOR
            self.door_positions.add((x, y))

    def _set_spawns(self):
        if not self.rooms:
            return

        # Player spawns in the centre of the first room
        first = self.rooms[0]
        self.player_spawn = (first.cx + 0.5, first.cy + 0.5)

        # Crystals — 1-3 per room (skip first room)
        self.crystal_positions = []
        for room in self.rooms[1:]:
            for _ in range(random.randint(1, 3)):
                cx = random.randint(room.x + 1, room.x + room.w - 2) + 0.5
                cy = random.randint(room.y + 1, room.y + room.h - 2) + 0.5
                self.crystal_positions.append((cx, cy))

        # Enemies — typed by room depth (skip first two rooms)
        self.enemy_spawns = []
        mid = max(3, len(self.rooms) // 2)
        for idx, room in enumerate(self.rooms[2:], start=2):
            count = random.randint(1, min(2, self.level))
            for _ in range(count):
                ex = random.randint(room.x + 1, room.x + room.w - 2) + 0.5
                ey = random.randint(room.y + 1, room.y + room.h - 2) + 0.5
                if idx < mid:
                    etype = ENEMY_TYPE_CRAWLER
                elif idx < mid + (len(self.rooms) - mid) // 2:
                    etype = random.choice([ENEMY_TYPE_CRAWLER, ENEMY_TYPE_SHADE])
                else:
                    weights = [ENEMY_TYPE_CRAWLER, ENEMY_TYPE_SHADE, ENEMY_TYPE_BRUTE]
                    if self.level >= 3:
                        etype = random.choice(weights)
                    else:
                        etype = random.choice(weights[:2])
                self.enemy_spawns.append((ex, ey, etype))

        # Items — 1-2 per room (skip first room)
        self.item_spawns = []
        for room in self.rooms[1:]:
            for _ in range(random.randint(1, 2)):
                ix = random.randint(room.x + 1, room.x + room.w - 2) + 0.5
                iy = random.randint(room.y + 1, room.y + room.h - 2) + 0.5
                itype = random.choice(['potion', 'torch'])
                self.item_spawns.append((ix, iy, itype))