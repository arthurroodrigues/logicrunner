"""
Cave corridor renderer — inspired by the dungeon reference art.

Visual targets (from mapa.png reference):
  • Wide, spacious corridor with large stone blocks on walls
  • Large floor tiles with clear perspective
  • Crystals placed on the FLOOR near walls (not on walls)
  • Torches mounted on WALLS at mid height
  • Blue ambient glow at vanishing point
  • Dark stone ceiling

Texture assignments
-------------------
Floor   : assets/tileavel3.png  (flat stone pavement)
Ceiling : assets/tileavel1.png  (dark rough stone)
Wall    : assets/parede.png     (3-D cubic blocks)
Sprites : assets/decorativos.png  3×3 sheet 418×418 px/cell
"""

import os
from collections import deque

import numpy as np
import pygame

from src import config

# ── paths ────────────────────────────────────────────────────────────────────
_ASSETS = "assets"
_CAVE   = os.path.join(_ASSETS, "cave")

# ── world constants ──────────────────────────────────────────────────────────
# Tuned to match the reference image's spacious dungeon feel
_CAM_Y    = 2.5     # camera height above floor (lower = more floor visible)
_FOCAL    = float(config.CAMERA_FOCAL_LENGTH)
_WALL_TOP = 5.2     # corridor ceiling height — tall for dungeon feel
_WALL_X   = 4.8     # half-width of corridor — wider than lanes
_MIN_Z    = 1.6
_FAR_Z    = 60.0

# Texture scale: samples per world unit (tune to match reference tile size)
_FS  = 55.0    # floor  — larger tiles, matches reference pavement
_CS  = 40.0    # ceiling — coarser dark blocks
_WS  = 42.0    # wall   — large stone blocks

# Decoratives
_CRYSTAL_SPACING = 10.0  # world units between crystal groups
_TORCH_SPACING   = 10.0  # world units between torches (offset from crystals)
_CRYSTAL_X       = 3.6   # world X of crystals (near walls, inside corridor)
_TORCH_Y         = 2.8   # world Y of torch centre (mid-wall height)
_CRYSTAL_H       = 1.4   # rendered world height of crystals
_TORCH_H         = 0.9   # rendered world height of torches


# ── background removal ────────────────────────────────────────────────────────

def _remove_bg(surf: pygame.Surface, threshold: int = 240) -> pygame.Surface:
    out = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    out.blit(surf, (0, 0))
    w, h = out.get_size()
    visited = bytearray(w * h)
    queue: deque = deque()

    def _seed(x: int, y: int) -> None:
        idx = y * w + x
        if not visited[idx]:
            r, g, b, _ = out.get_at((x, y))
            if r >= threshold and g >= threshold and b >= threshold:
                visited[idx] = 1
                queue.append((x, y))

    for x in range(w): _seed(x, 0); _seed(x, h - 1)
    for y in range(1, h - 1): _seed(0, y); _seed(w - 1, y)

    while queue:
        x, y = queue.popleft()
        out.set_at((x, y), (0, 0, 0, 0))
        for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0 <= nx < w and 0 <= ny < h:
                idx = ny * w + nx
                if not visited[idx]:
                    r, g, b, _ = out.get_at((nx, ny))
                    if r >= threshold and g >= threshold and b >= threshold:
                        visited[idx] = 1; queue.append((nx, ny))
    return out


# ── procedural fallback tiles ─────────────────────────────────────────────────

def _gen_floor_tile(size: int = 128) -> pygame.Surface:
    s = pygame.Surface((size, size)); s.fill((58,50,42)); b=size//4
    for row in range(size//b+2):
        for col in range(size//b+2):
            off=(b//2) if row%2 else 0; x=col*b+off-b; y=row*b
            v=(row*7+col*13)%18; r=pygame.Rect(x+1,y+1,b-2,b-2)
            pygame.draw.rect(s,(58+v,50+v//2,42+v//3),r)
    for i in range(0,size,b):
        pygame.draw.line(s,(28,23,18),(0,i),(size,i),1)
        pygame.draw.line(s,(28,23,18),(i,0),(i,size),1)
    return s

def _gen_ceil_tile(size: int = 128) -> pygame.Surface:
    s = pygame.Surface((size, size)); s.fill((14,12,10)); b=size//3
    for row in range(size//b+2):
        for col in range(size//b+2):
            v=(row*3+col*7)%8; r=pygame.Rect(col*b+1,row*b+1,b-2,b-2)
            pygame.draw.rect(s,(14+v,12+v//2,10+v//3),r)
    for i in range(0,size,b):
        pygame.draw.line(s,(9,7,6),(0,i),(size,i),1)
        pygame.draw.line(s,(9,7,6),(i,0),(i,size),1)
    return s

def _gen_wall_tile(size: int = 128) -> pygame.Surface:
    s = pygame.Surface((size, size)); s.fill((48,42,36)); bw,bh=size//3,size//5
    for row in range(size//bh+2):
        for col in range(size//bw+2):
            off=(bw//2) if row%2 else 0; x=col*bw+off-bw; y=row*bh
            v=(row*5+col*11)%14; r=pygame.Rect(x+1,y+1,bw-2,bh-2)
            pygame.draw.rect(s,(48+v,42+v//2,36+v//3),r)
        pygame.draw.line(s,(26,22,18),(0,(row*bh)%size),(size,(row*bh)%size),1)
    return s

def _ensure_fallback_tiles() -> None:
    os.makedirs(_CAVE, exist_ok=True)
    for fname, gen in [("floor_stone_tile.png",_gen_floor_tile),
                       ("ceiling_blocks_tile.png",_gen_ceil_tile),
                       ("wall_blocks_tile.png",_gen_wall_tile)]:
        p = os.path.join(_CAVE, fname)
        if not os.path.exists(p): pygame.image.save(gen(), p)


# ── texture loader ────────────────────────────────────────────────────────────

def _load_tex(real_path: str, fallback_path: str, work: int = 128,
              transpose: bool = False):
    path = real_path if os.path.exists(real_path) else fallback_path
    raw  = pygame.image.load(path).convert()
    arr  = pygame.surfarray.array3d(pygame.transform.smoothscale(raw, (work, work)))
    if transpose: arr = arr.transpose(1, 0, 2)
    return np.ascontiguousarray(arr), work, work


# ── decorative sprite extractor ───────────────────────────────────────────────

def _extract_decoratives(path: str, work: int = 128):
    """
    Returns (crystals, torches) — two lists of pygame.Surface.
    Grid 3×3 — cells used:
      crystals : [0,0] [0,1] [0,2] [1,0] [1,1]
      torches  : [2,0] [2,1]
    """
    raw = pygame.image.load(path).convert_alpha()
    W, H = raw.get_size()
    fw, fh = W // 3, H // 3

    def _cell(row, col):
        sub = raw.subsurface(col*fw, row*fh, fw, fh).copy()
        cleaned = _remove_bg(sub)
        return pygame.transform.smoothscale(cleaned, (work, work))

    crystals = [_cell(0,0), _cell(0,1), _cell(0,2), _cell(1,0), _cell(1,1)]
    torches  = [_cell(2,0), _cell(2,1)]
    return crystals, torches


# ── ambient glow surface (pre-rendered once) ──────────────────────────────────

def _make_glow(cx: int, horizon: int, screen_w: int) -> tuple[pygame.Surface, tuple]:
    """Soft blue elliptical glow at the vanishing point — subtle, deep-tunnel feel."""
    gw, gh = 220, 90
    surf = pygame.Surface((gw, gh), pygame.SRCALPHA)
    # Multiple soft rings — outer most transparent, inner brighter
    for rx, ry, a in [(110, 45, 18), (70, 28, 28), (38, 15, 40), (16, 6, 55)]:
        pygame.draw.ellipse(surf, (20, 110, 200, a),
                            (gw//2 - rx, gh//2 - ry, rx*2, ry*2))
    return surf, (cx - gw // 2, horizon - gh // 2 + 8)


# ── renderer ──────────────────────────────────────────────────────────────────

class ScanlineFloorRenderer:

    def __init__(self, screen_width: int, screen_height: int, horizon: int) -> None:
        self.W = screen_width
        self.H = screen_height
        self.horizon = horizon
        self._cx = screen_width // 2

        _ensure_fallback_tiles()

        # Floor  → (H,W,3) row-access
        self._ftex, self._ftw, self._fth = _load_tex(
            os.path.join(_ASSETS, "tileavel3.png"),
            os.path.join(_CAVE,   "floor_stone_tile.png"), transpose=True)
        # Ceiling → (H,W,3) row-access
        self._ctex, self._ctw, self._cth = _load_tex(
            os.path.join(_ASSETS, "tileavel1.png"),
            os.path.join(_CAVE,   "ceiling_blocks_tile.png"), transpose=True)
        # Wall   → (W,H,3) column-access
        self._wtex, self._wtw, self._wth = _load_tex(
            os.path.join(_ASSETS, "parede.png"),
            os.path.join(_CAVE,   "wall_blocks_tile.png"), transpose=False)

        # Decoratives
        decor_path = os.path.join(_ASSETS, "decorativos.png")
        if os.path.exists(decor_path):
            self._crystals, self._torches = _extract_decoratives(decor_path)
        else:
            self._crystals, self._torches = [], []

        # Pre-scaled sprite cache: {(sprite_id, h_px): Surface}
        self._sprite_cache: dict = {}

        # Column offset array
        self._xs = (np.arange(screen_width, dtype=np.float32) - screen_width / 2.0)

        # Wall geometry cache
        self._build_wall_cache()

        # Ambient glow
        self._glow_surf, self._glow_pos = _make_glow(self._cx, horizon, screen_width)

    # ── sprite scaling with cache ─────────────────────────────────────────────

    def _get_sprite(self, sprites: list, idx: int, h_px: int) -> pygame.Surface | None:
        if not sprites or h_px < 5:
            return None
        idx = idx % len(sprites)
        key = (id(sprites[idx]), h_px)
        if key not in self._sprite_cache:
            src = sprites[idx]
            w_px = max(1, int(src.get_width() * h_px / src.get_height()))
            self._sprite_cache[key] = pygame.transform.smoothscale(src, (w_px, h_px))
        return self._sprite_cache[key]

    # ── wall geometry cache ───────────────────────────────────────────────────

    def _build_wall_cache(self) -> None:
        cx   = self._cx
        cols = np.arange(self.W, dtype=np.float32)
        dx   = np.abs(cols - cx); dx[cx] = 1.0
        z_col = _WALL_X * _FOCAL / dx

        valid = (z_col >= _MIN_Z) & (z_col <= _FAR_Z)
        valid[cx] = False
        step = np.zeros(self.W, dtype=bool); step[::4] = True
        valid &= step

        safe_z = np.where(z_col > 0, z_col, 1.0)
        y_floor = np.clip(self.horizon + _CAM_Y * _FOCAL / safe_z,
                          0, self.H - 1).astype(np.int32)
        y_ceil  = np.clip(self.horizon - (_WALL_TOP - _CAM_Y) * _FOCAL / safe_z,
                          0, self.H - 1).astype(np.int32)
        h_full  = np.maximum(1, np.round(
            _FOCAL * _WALL_TOP / safe_z)).astype(np.int32)

        idx = np.where(valid)[0]
        self._wc_x     = idx.astype(np.int32)
        self._wc_z     = z_col[idx].astype(np.float32)
        self._wc_yc    = y_ceil[idx]
        self._wc_yf    = y_floor[idx]
        self._wc_hf    = h_full[idx]
        self._wc_shade = np.clip(1.15 - self._wc_z * 0.017, 0.12, 1.0
                                 ).astype(np.float32)

    # ── scanline floor & ceiling ──────────────────────────────────────────────

    def _draw_floor_ceiling(self, arr: np.ndarray, track_offset: float) -> None:
        xs  = self._xs
        foc = _FOCAL
        cy  = _CAM_Y
        ofs_f = int(track_offset * _FS) % self._fth
        ofs_c = int(track_offset * _CS) % self._cth

        # FLOOR — every 3rd row
        for py in range(self.horizon + 1, self.H, 3):
            dy    = py - self.horizon
            depth = cy * foc / dy
            tx    = (xs * (depth / foc) * _FS).astype(np.int32) % self._ftw
            tz    = int(depth * _FS + ofs_f) % self._fth
            shade = np.float32(max(0.20, min(1.0, 1.15 - depth * 0.036)))
            row   = (self._ftex[tz, tx, :] * shade).astype(np.uint8)
            arr[:, py, :] = row
            if py + 1 < self.H: arr[:, py + 1, :] = row
            if py + 2 < self.H: arr[:, py + 2, :] = row

        # CEILING — every 4th row (dark, low detail)
        ceil_cam = _WALL_TOP - cy
        for py in range(self.horizon - 1, -1, -4):
            dy    = self.horizon - py
            depth = ceil_cam * foc / dy
            tx    = (xs * (depth / foc) * _CS).astype(np.int32) % self._ctw
            tz    = int(depth * _CS + ofs_c) % self._cth
            shade = np.float32(max(0.04, min(0.32, 0.36 - depth * 0.040)))
            row   = (self._ctex[tz, tx, :] * shade).astype(np.uint8)
            arr[:, py, :] = row
            for k in range(1, 4):
                if py - k >= 0: arr[:, py - k, :] = row

    # ── textured wall columns ─────────────────────────────────────────────────

    def _draw_wall_columns(self, arr: np.ndarray, track_offset: float) -> None:
        tw = self._wtw; th = self._wth; tex = self._wtex

        for i in range(len(self._wc_x)):
            sx = self._wc_x[i]; yc = self._wc_yc[i]; yf = self._wc_yf[i]
            if yc >= yf: continue
            n = yf - yc; hf = self._wc_hf[i]
            u = int((self._wc_z[i] + track_offset) * _WS) % tw
            vs  = (np.arange(n, dtype=np.int32) * th // hf).clip(0, th - 1)
            row = (tex[u, vs, :] * self._wc_shade[i]).astype(np.uint8)
            arr[sx, yc:yf, :] = row
            for k in range(1, 4):
                if sx + k < self.W: arr[sx + k, yc:yf, :] = row

    # ── ambient glow at vanishing point ──────────────────────────────────────

    def _draw_glow(self, screen: pygame.Surface) -> None:
        screen.blit(self._glow_surf, self._glow_pos,
                    special_flags=pygame.BLEND_ADD)

    # ── lane dividers ─────────────────────────────────────────────────────────

    def _draw_lane_lines(self, screen: pygame.Surface) -> None:
        cx  = self._cx
        col = (40, 110, 140)
        for lx in (-1.17, 1.17):
            pts = []; z = 2.0
            while z < 60.0:
                sx = int(cx + lx * _FOCAL / z)
                sy = int(self.horizon + _CAM_Y * _FOCAL / z)
                if sy >= self.H: break
                if sy > self.horizon: pts.append((sx, sy))
                z += 0.4
            if len(pts) > 1:
                pygame.draw.lines(screen, col, False, pts, 1)

    # ── decoratives: crystals on floor, torches on walls ─────────────────────

    def _draw_decoratives(self, screen: pygame.Surface, track_offset: float) -> None:
        if not self._crystals and not self._torches:
            return

        cx  = self._cx
        foc = _FOCAL
        cy  = _CAM_Y

        n_cryst = len(self._crystals)
        n_torch = len(self._torches)

        # ── Crystals — placed on the FLOOR near walls ─────────────────────
        cycle_c = 12 * _CRYSTAL_SPACING
        ofs_c   = track_offset % cycle_c

        for i in range(12):
            z = i * _CRYSTAL_SPACING - ofs_c
            if z < 0: z += cycle_c
            if z < _MIN_Z or z > _FAR_Z: continue

            scale  = foc / z
            h_px   = int(_CRYSTAL_H * scale)
            if h_px < 6: continue

            y_floor = int(self.horizon + cy * foc / z)  # ground level

            for side in (-1, 1):
                wx = side * _CRYSTAL_X
                sx = int(cx + wx * scale)
                sp = self._get_sprite(self._crystals, (i * 2 + (0 if side < 0 else 1)) % n_cryst, h_px)
                if sp is None: continue
                alpha = int(max(30, min(240, 255 - (z - _MIN_Z) * 4.8)))
                sp.set_alpha(alpha)
                screen.blit(sp, (sx - sp.get_width() // 2, y_floor - sp.get_height()))

        # ── Torches — mounted on WALLS at mid height ──────────────────────
        if not self._torches:
            return

        cycle_t = 10 * _TORCH_SPACING
        ofs_t   = (track_offset + _TORCH_SPACING * 0.5) % cycle_t  # offset from crystals

        for i in range(10):
            z = i * _TORCH_SPACING - ofs_t
            if z < 0: z += cycle_t
            if z < _MIN_Z or z > _FAR_Z: continue

            scale = foc / z
            h_px  = int(_TORCH_H * scale)
            if h_px < 5: continue

            # Torch screen Y — mounted at _TORCH_Y world height
            sy_bot = int(self.horizon + (cy - _TORCH_Y) * foc / z)

            for side in (-1, 1):
                wx = side * (_WALL_X - 0.05)   # flush with wall
                sx = int(cx + wx * scale)
                sp = self._get_sprite(self._torches, i % n_torch, h_px)
                if sp is None: continue
                alpha = int(max(30, min(220, 220 - (z - _MIN_Z) * 4.2)))
                sp.set_alpha(alpha)
                screen.blit(sp, (sx - sp.get_width() // 2, sy_bot - sp.get_height()))

    # ── public draw ───────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface, track_offset: float) -> None:
        # Phase 1: surfarray (floor + ceiling + walls)
        arr = pygame.surfarray.pixels3d(screen)
        self._draw_floor_ceiling(arr, track_offset)
        self._draw_wall_columns(arr, track_offset)
        del arr

        # Phase 2: blit (glow + lane lines + decoratives)
        self._draw_glow(screen)
        self._draw_lane_lines(screen)
        self._draw_decoratives(screen, track_offset)
