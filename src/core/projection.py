import pygame

from src import config


class Projection:
    def __init__(self, camera: object) -> None:
        self.camera = camera

    def scale_for_z(self, z: float) -> float:
        fov = getattr(self.camera, "fov_scale", 1.0)
        return (config.CAMERA_FOCAL_LENGTH * fov) / max(0.1, z + config.CAMERA_DEPTH_OFFSET)

    def project(self, x: float, y: float, z: float) -> tuple[int, int, float]:
        ox, oy = self.camera.render_offset
        cam_x = getattr(self.camera, "world_x", 0.0)
        cam_y = getattr(self.camera, "world_y", 2.9)
        scale = self.scale_for_z(z)
        screen_x = config.SCREEN_WIDTH / 2 + (x - cam_x) * scale + ox
        screen_y = config.HORIZON_Y + (cam_y - y) * scale + oy
        return int(screen_x), int(screen_y), scale

    def ground_point(self, x: float, z: float) -> tuple[int, int]:
        sx, sy, _ = self.project(x, 0.0, z)
        return sx, sy

    def world_rect(self, x: float, y: float, z: float, width: float, height: float) -> pygame.Rect:
        sx, sy, scale = self.project(x, y, z)
        pixel_w = max(3, int(width * scale))
        pixel_h = max(3, int(height * scale))
        return pygame.Rect(sx - pixel_w // 2, sy - pixel_h, pixel_w, pixel_h)

    def ground_quad(self, left: float, right: float, z_near: float, z_far: float) -> list[tuple[int, int]]:
        return [
            self.ground_point(left, z_near),
            self.ground_point(right, z_near),
            self.ground_point(right, z_far),
            self.ground_point(left, z_far),
        ]

    def vertical_quad(self, x: float, y_bottom: float, y_top: float, z_near: float, z_far: float) -> list[tuple[int, int]]:
        return [
            self.project(x, y_bottom, z_near)[0:2],
            self.project(x, y_bottom, z_far)[0:2],
            self.project(x, y_top, z_far)[0:2],
            self.project(x, y_top, z_near)[0:2],
        ]
