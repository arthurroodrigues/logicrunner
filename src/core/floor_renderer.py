"""
Cave corridor renderer — scanline floor/ceiling + textured wall columns + decoratives.

Texture assignments
-------------------
Floor   : assets/tileavel3.png  (flat stone pavement)
Ceiling : assets/tileavel1.png  (dark rough stone)
Wall    : assets/parede.png     (3-D cubic blocks)
Sprites : assets/decorativos.png  3×3 grid 418×418 px each
            [0,0..2] blue crystals   [1,0..1] purple crystals
            [2,0..1] wall torches
"""

import os
from collections import deque

import numpy as np
import pygame

from src import config

# ── paths ────────────────────────────────────────────────────────────────────
_ASSETS = "assets"
_CAVE   = os.path.join(_ASSETS, "cave")   # fallback procedural tiles

# ── world / projection constants (must match game projection) ────────────────
_CAM_Y    = 2.9     # camera world-Y above floor
_FOCAL    = float(config.CAMERA_FOCAL_LENGTH)
_WALL_TOP = 3.85    # corridor ceiling height (world units)
_WALL_X   = 4.05    # half-width of corridor walls (world units)
_MIN_Z    = 1.6     # nearest z rendered
_FAR_Z    = 52.0    # farthest z rendered

# Texture scale: samples per world unit (tune to taste)
_FS  = 110.0   # floor
_CS  = 90.0    # ceiling
_WS  = 95.0    # wall

# Decoratives
_DECOR_SPACING = 8.0   # world units between decorative groups
_DECOR_WORLD_H = 1.8   # sprite rendered height in world units


# ── background removal ────────────────────────────────────────────────────────

def _remove_bg(surf: pygame.Surface, threshold: int = 240) -> pygame.Surface:
    """Flood-fill from edges to erase white/near-white background."""
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

    for x in range(w):
        _seed(x, 0); _seed(x, h - 1)
    for y in range(1, h - 1):
        _seed(0, y); _seed(w - 1, y)

    while queue:
        x, y = queue.popleft()
        out.set_at((x, y), (0, 0, 0, 0))
        for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0 <= nx < w and 0 <= ny < h:
                idx = ny * w + nx
                if not visited[idx]:
                    r, g, b, _ = out.get_at((nx, ny))
                    if r >= threshold and g >= threshold and b >= threshold:
                        visited[idx] = 1
                        queue.append((nx, ny))
    return out


# ── procedural fallback tiles (used only if real textures missing) ────────────

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
    s = pygame.Surface((size, size)); s.fill((20,17,14)); b=size//3
    for row in range(size//b+2):
        for col in range(size//b+2):
            x,y=col*b,row*b; v=(row*3+col*7)%10; r=pygame.Rect(x+1,y+1,b-2,b-2)
            pygame.draw.rect(s,(20+v,17+v//2,14+v//3),r)
    for i in range(0,size,b):
        pygame.draw.line(s,(13,11,9),(0,i),(size,i),1)
        pygame.draw.line(s,(13,11,9),(i,0),(i,size),1)
    return s


def _gen_wall_tile(size: int = 128) -> pygame.Surface:
    s = pygame.Surface((size, size)); s.fill((48,42,36)); bw,bh=size//3,size//5
    for row in range(size//bh+2):
        for col in range(size//bw+2):
            off=(bw//2) if row%2 else 0; x=col*bw+off-bw; y=row*bh
            v=(row*5+col*11)%14; r=pygame.Rect(x+1,y+1,bw-2,bh-2)
            pygame.draw.rect(s,(48+v,42+v//2,36+v//3),r)
            pygame.draw.line(s,(66,58,50),(r.x,r.y),(r.right,r.y),1)
            pygame.draw.line(s,(34,29,24),(r.x,r.bottom),(r.right,r.bottom),1)
        pygame.draw.line(s,(26,22,18),(0,(row*bh)%size),(size,(row*bh)%size),1)
    return s


def _ensure_fallback_tiles() -> None:
    os.makedirs(_CAVE, exist_ok=True)
    for fname, gen in [("floor_stone_tile.png",_gen_floor_tile),
                       ("ceiling_blocks_tile.png",_gen_ceil_tile),
                       ("wall_blocks_tile.png",_gen_wall_tile)]:
        p = os.path.join(_CAVE, fname)
        if not os.path.exists(p):
            pygame.image.save(gen(), p)


# ── texture loader ────────────────────────────────────────────────────────────

def _load_tex(real_path: str, fallback_path: str, work: int = 128,
              transpose: bool = False):
    """
    Load texture → numpy uint8 array.
    transpose=False → (W,H,3): efficient for tex[u, vs, :] (wall column access)
    transpose=True  → (H,W,3): efficient for tex[tz, tx, :] (scanline row access)
    """
    path = real_path if os.path.exists(real_path) else fallback_path
    raw = pygame.image.load(path).convert()
    scaled = pygame.transform.smoothscale(raw, (work, work))
    arr = pygame.surfarray.array3d(scaled)   # (W, H, 3)
    if transpose:
        arr = arr.transpose(1, 0, 2)         # (H, W, 3)
    return np.ascontiguousarray(arr), work, work


# ── decorative sprite extractor ───────────────────────────────────────────────

def _extract_decoratives(path: str, work: int = 128) -> list[pygame.Surface]:
    """
    Extract sprites from the 3×3 decorativos sheet, remove white bg,
    return list of pygame.Surface with alpha.
    Cells used: [0,0] [0,1] [0,2] blue crystals
                [1,0] [1,1]       purple crystals
                [2,0] [2,1]       wall torches
    """
    raw = pygame.image.load(path).convert_alpha()
    W, H = raw.get_size()
    fw, fh = W // 3, H // 3

    cells = [(0,0),(0,1),(0,2),(1,0),(1,1),(2,0),(2,1)]
    sprites = []
    for row, col in cells:
        sub = raw.subsurface(col*fw, row*fh, fw, fh).copy()
        cleaned = _remove_bg(sub)
        scaled  = pygame.transform.smoothscale(cleaned, (work, work))
        sprites.append(scaled)
    return sprites


# ── renderer ──────────────────────────────────────────────────────────────────

class ScanlineFloorRenderer:

    def __init__(self, screen_width: int, screen_height: int, horizon: int) -> None:
        self.W       = screen_width
        self.H       = screen_height
        self.horizon = horizon

        _ensure_fallback_tiles()

        # Floor texture  → tileavel3  — (H,W,3) transposed for row-access
        self._ftex, self._ftw, self._fth = _load_tex(
            os.path.join(_ASSETS, "tileavel3.png"),
            os.path.join(_CAVE,   "floor_stone_tile.png"),
            transpose=True,
        )
        # Ceiling texture → tileavel1 — (H,W,3) transposed
        self._ctex, self._ctw, self._cth = _load_tex(
            os.path.join(_ASSETS, "tileavel1.png"),
            os.path.join(_CAVE,   "ceiling_blocks_tile.png"),
            transpose=True,
        )
        # Wall texture   → parede — (W,H,3) original for column-access
        self._wtex, self._wtw, self._wth = _load_tex(
            os.path.join(_ASSETS, "parede.png"),
            os.path.join(_CAVE,   "wall_blocks_tile.png"),
            transpose=False,
        )

        # Decorative sprites
        decor_path = os.path.join(_ASSETS, "decorativos.png")
        self._sprites: list[pygame.Surface] = (
            _extract_decoratives(decor_path)
            if os.path.exists(decor_path) else []
        )

        # Precomputed column offsets from screen centre
        self._xs = (np.arange(screen_width, dtype=np.float32) - screen_width / 2.0)

        # Build static wall geometry cache (expensive but one-time)
        self._build_wall_cache()

    # ── scanline floor & ceiling ──────────────────────────────────────────────

    def _draw_floor_ceiling(self, arr: np.ndarray, track_offset: float) -> None:
        """
        Scanline floor + ceiling.
        Textures stored as (H, W, 3) → tex[tz, tx, :] reads one row (384 B),
        all 1280 columns served from L1 cache.
        """
        xs  = self._xs          # (W,) float — column offsets from centre
        foc = _FOCAL
        cy  = _CAM_Y

        ofs_f = int(track_offset * _FS) % self._fth
        ofs_c = int(track_offset * _CS) % self._cth

        # ── FLOOR (every 3rd row, fill next 2 rows) ───────────────────────
        for py in range(self.horizon + 1, self.H, 3):
            dy    = py - self.horizon
            depth = cy * foc / dy
            tx    = (xs * (depth / foc) * _FS).astype(np.int32) % self._ftw
            tz    = int(depth * _FS + ofs_f) % self._fth
            shade = np.float32(max(0.22, min(1.0, 1.18 - depth * 0.040)))
            row   = (self._ftex[tz, tx, :] * shade).astype(np.uint8)
            arr[:, py, :] = row
            if py + 1 < self.H: arr[:, py + 1, :] = row
            if py + 2 < self.H: arr[:, py + 2, :] = row

        # ── CEILING (every 4th row — dark, low detail needed) ─────────────
        ceil_cam = _WALL_TOP - cy
        for py in range(self.horizon - 1, -1, -4):
            dy    = self.horizon - py
            depth = ceil_cam * foc / dy
            tx    = (xs * (depth / foc) * _CS).astype(np.int32) % self._ctw
            tz    = int(depth * _CS + ofs_c) % self._cth
            shade = np.float32(max(0.07, min(0.45, 0.50 - depth * 0.044)))
            row   = (self._ctex[tz, tx, :] * shade).astype(np.uint8)
            arr[:, py, :] = row
            for k in range(1, 4):
                if py - k >= 0: arr[:, py - k, :] = row

    # ── textured wall columns (fully vectorised) ──────────────────────────────

    def _build_wall_cache(self) -> None:
        """Pre-compute per valid-column geometry (every 2nd column for speed)."""
        cx   = self.W // 2
        cols = np.arange(self.W, dtype=np.float32)
        dx   = np.abs(cols - cx)
        dx[cx] = 1.0

        z_col = _WALL_X * _FOCAL / dx

        valid = (z_col >= _MIN_Z) & (z_col <= _FAR_Z)
        valid[cx] = False

        # Process every 4th column — write 4px wide slices (good quality/speed balance)
        step = np.zeros(self.W, dtype=bool)
        step[::4] = True
        valid &= step

        y_floor = np.clip(
            self.horizon + _CAM_Y * _FOCAL / np.where(z_col > 0, z_col, 1.0),
            0, self.H - 1).astype(np.int32)
        y_ceil  = np.clip(
            self.horizon - (_WALL_TOP - _CAM_Y) * _FOCAL / np.where(z_col > 0, z_col, 1.0),
            0, self.H - 1).astype(np.int32)

        # h_wall_full = unclipped wall height in pixels (for texture v mapping)
        h_wall_full = np.maximum(
            1,
            np.round(_FOCAL * (_CAM_Y + _WALL_TOP - _CAM_Y) / np.where(z_col > 0, z_col, 1.0))
        ).astype(np.int32)

        valid_idx = np.where(valid)[0]

        # Store per-column arrays (only valid cols)
        self._wc_x      = valid_idx.astype(np.int32)
        self._wc_z      = z_col[valid_idx].astype(np.float32)
        self._wc_yc     = y_ceil[valid_idx]
        self._wc_yf     = y_floor[valid_idx]
        self._wc_hf     = h_wall_full[valid_idx]
        self._wc_shade  = np.clip(1.15 - self._wc_z * 0.020, 0.14, 1.0).astype(np.float32)

    def _draw_wall_columns(self, arr: np.ndarray, track_offset: float) -> None:
        tw = self._wtw
        th = self._wth
        tex = self._wtex  # (tw, th, 3)
        H = self.H

        for i in range(len(self._wc_x)):
            sx = self._wc_x[i]
            yc = self._wc_yc[i]
            yf = self._wc_yf[i]
            if yc >= yf:
                continue

            hf    = self._wc_hf[i]
            u     = int((self._wc_z[i] + track_offset) * _WS) % tw
            shade = self._wc_shade[i]
            n     = yf - yc

            vs  = (np.arange(n, dtype=np.int32) * th // hf).clip(0, th - 1)
            row = (tex[u, vs, :] * shade).astype(np.uint8)  # (n, 3)

            # Write 4 contiguous columns
            arr[sx, yc:yf, :] = row
            for k in range(1, 4):
                if sx + k < self.W:
                    arr[sx + k, yc:yf, :] = row

    # ── lane dividers ─────────────────────────────────────────────────────────

    def _draw_lane_lines(self, screen: pygame.Surface) -> None:
        cx    = self.W // 2
        color = (50, 130, 160)
        for lx in (-1.17, 1.17):
            pts = []
            z = 2.0
            while z < 55.0:
                sx = int(cx + lx * _FOCAL / z)
                sy = int(self.horizon + _CAM_Y * _FOCAL / z)
                if sy >= self.H:
                    break
                if sy > self.horizon:
                    pts.append((sx, sy))
                z += 0.35
            if len(pts) > 1:
                pygame.draw.lines(screen, color, False, pts, 1)

    # ── decorative projection ─────────────────────────────────────────────────

    def _draw_decoratives(self, screen: pygame.Surface, track_offset: float) -> None:
        if not self._sprites:
            return

        cx       = self.W // 2
        n_types  = len(self._sprites)
        spacing  = _DECOR_SPACING
        cycle    = 14 * spacing          # 14 slots per cycle
        offset_in_cycle = track_offset % cycle

        for i in range(14):
            z_base = i * spacing
            z = z_base - offset_in_cycle
            if z < 0:
                z += cycle
            if z < _MIN_Z or z > _FAR_Z:
                continue

            scale  = _FOCAL / z
            h_px   = int(_DECOR_WORLD_H * scale)
            if h_px < 6:
                continue

            # Screen Y: bottom of sprite sits on floor
            y_floor = int(self.horizon + _CAM_Y * _FOCAL / z)
            sy_bot  = y_floor
            sy_top  = sy_bot - h_px

            for side in (-1, 1):
                # Sprite positioned just inside the wall
                wx = side * (_WALL_X - 0.5)
                sx = int(cx + wx * scale)

                type_idx  = (i * 2 + (0 if side == -1 else 1)) % n_types
                sprite    = self._sprites[type_idx]
                w_px      = int(sprite.get_width() * h_px / sprite.get_height())
                if w_px < 4:
                    continue

                scaled_sprite = pygame.transform.smoothscale(sprite, (w_px, h_px))

                # Depth-based brightness (darken distant decoratives)
                alpha = int(max(40, min(255, 255 - (z - _MIN_Z) * 5.5)))
                scaled_sprite.set_alpha(alpha)

                blit_x = sx - w_px // 2
                blit_y = sy_top
                screen.blit(scaled_sprite, (blit_x, blit_y))

    # ── public entry point ────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface, track_offset: float) -> None:
        # Phase 1 — scanline (surfarray lock covers floor + ceiling + walls)
        arr = pygame.surfarray.pixels3d(screen)
        self._draw_floor_ceiling(arr, track_offset)
        self._draw_wall_columns(arr, track_offset)
        del arr   # release lock before blit operations

        # Phase 2 — blit calls (lane lines + decoratives on top)
        self._draw_lane_lines(screen)
        self._draw_decoratives(screen, track_offset)
