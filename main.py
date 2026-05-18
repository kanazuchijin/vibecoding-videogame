from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from panda3d.core import loadPrcFileData
from PIL import Image, ImageDraw

loadPrcFileData("", "audio-library-name null")

from ursina import (
    AmbientLight,
    DirectionalLight,
    Entity,
    Mesh,
    Text,
    Texture,
    Ursina,
    Vec3,
    camera,
    color,
    destroy,
    held_keys,
    lerp,
    mouse,
    raycast,
    scene,
    time,
    window,
)
from ursina.prefabs.first_person_controller import FirstPersonController


WORLD_SIZE = 200
HALF_WORLD = WORLD_SIZE // 2
CHUNK_SIZE = 16
SEA_LEVEL = 8
MAX_INTERACT_DISTANCE = 7
FIXED_SEED = 20240518
DAY_LENGTH_SECONDS = 160


BlockCoord = Tuple[int, int, int]
ChunkKey = Tuple[int, int]


@dataclass(frozen=True)
class BlockInfo:
    display_name: str
    tint: color.Color
    solid: bool
    collectible: bool
    hardness: float
    placeable: bool = True


BLOCKS: Dict[str, BlockInfo] = {
    "grass": BlockInfo("Grass", color.rgb32(88, 168, 74), True, True, 0.35),
    "dirt": BlockInfo("Dirt", color.rgb32(124, 82, 48), True, True, 0.35),
    "stone": BlockInfo("Stone", color.rgb32(118, 120, 124), True, True, 1.15),
    "metal_ore": BlockInfo("Metal Ore", color.rgb32(139, 142, 150), True, True, 1.7),
    "water": BlockInfo("Water", color.rgba32(58, 138, 216, 128), False, False, 0.0, False),
    "wood": BlockInfo("Wood", color.rgb32(116, 74, 38), True, True, 0.65),
    "leaves": BlockInfo("Leaves", color.rgb32(42, 116, 61), True, True, 0.45),
}

HOTBAR = ["dirt", "grass", "stone", "wood", "leaves", "metal_ore"]
TEXTURE_SIZE = 16
TEXTURE_TILES = (
    "grass_top",
    "grass_side",
    "dirt",
    "stone",
    "metal_ore",
    "water",
    "wood_side",
    "wood_top",
    "leaves",
)
TEXTURE_INDEX = {name: index for index, name in enumerate(TEXTURE_TILES)}

FACE_DATA = (
    ((0, 1, 0), [(-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5)], 1.15),
    ((0, -1, 0), [(-0.5, -0.5, 0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5)], 0.60),
    ((1, 0, 0), [(0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.5, -0.5, 0.5)], 0.92),
    ((-1, 0, 0), [(-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, -0.5)], 0.82),
    ((0, 0, 1), [(0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5)], 0.98),
    ((0, 0, -1), [(-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5)], 0.76),
)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def smoothstep(value: float) -> float:
    return value * value * (3 - 2 * value)


def deterministic_noise(ix: int, iz: int, seed: int) -> float:
    number = ix * 374761393 + iz * 668265263 + seed * 1442695040888963407
    number = (number ^ (number >> 13)) * 1274126177
    number = number ^ (number >> 16)
    return ((number & 0xFFFF) / 0xFFFF) * 2 - 1


def value_noise(x: float, z: float, scale: float, seed: int) -> float:
    x /= scale
    z /= scale
    x0 = math.floor(x)
    z0 = math.floor(z)
    x1 = x0 + 1
    z1 = z0 + 1
    sx = smoothstep(x - x0)
    sz = smoothstep(z - z0)

    n00 = deterministic_noise(x0, z0, seed)
    n10 = deterministic_noise(x1, z0, seed)
    n01 = deterministic_noise(x0, z1, seed)
    n11 = deterministic_noise(x1, z1, seed)

    ix0 = lerp(n00, n10, sx)
    ix1 = lerp(n01, n11, sx)
    return lerp(ix0, ix1, sz)


def block_from_world_point(point: Vec3) -> BlockCoord:
    return (
        math.floor(point.x + 0.5),
        math.floor(point.y + 0.5),
        math.floor(point.z + 0.5),
    )


def chunk_for(x: int, z: int) -> ChunkKey:
    return (math.floor((x + HALF_WORLD) / CHUNK_SIZE), math.floor((z + HALF_WORLD) / CHUNK_SIZE))


def face_shade(shade: float, alpha: float = 1) -> color.Color:
    shade = clamp(shade, 0, 1)
    return color.rgba(
        shade,
        shade,
        shade,
        clamp(alpha, 0, 1),
    )


def jittered(base: Tuple[int, int, int], amount: int, rng: random.Random) -> Tuple[int, int, int, int]:
    return (
        int(clamp(base[0] + rng.randint(-amount, amount), 0, 255)),
        int(clamp(base[1] + rng.randint(-amount, amount), 0, 255)),
        int(clamp(base[2] + rng.randint(-amount, amount), 0, 255)),
        255,
    )


def build_block_texture_atlas() -> Texture:
    rng = random.Random(FIXED_SEED + 313)
    width = TEXTURE_SIZE * len(TEXTURE_TILES)
    image = Image.new("RGBA", (width, TEXTURE_SIZE), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)

    def tile_origin(name: str) -> Tuple[int, int]:
        return TEXTURE_INDEX[name] * TEXTURE_SIZE, 0

    def fill_noise(name: str, base: Tuple[int, int, int], amount: int) -> None:
        ox, oy = tile_origin(name)
        for px in range(TEXTURE_SIZE):
            for py in range(TEXTURE_SIZE):
                image.putpixel((ox + px, oy + py), jittered(base, amount, rng))

    fill_noise("grass_top", (78, 156, 68), 24)
    for _ in range(18):
        ox, oy = tile_origin("grass_top")
        px = ox + rng.randrange(TEXTURE_SIZE)
        py = oy + rng.randrange(TEXTURE_SIZE)
        image.putpixel((px, py), (*jittered((116, 190, 72), 14, rng)[:3], 255))

    fill_noise("dirt", (120, 78, 45), 22)
    for _ in range(28):
        ox, oy = tile_origin("dirt")
        image.putpixel((ox + rng.randrange(TEXTURE_SIZE), oy + rng.randrange(TEXTURE_SIZE)), jittered((88, 55, 34), 10, rng))

    ox, oy = tile_origin("grass_side")
    for px in range(TEXTURE_SIZE):
        for py in range(TEXTURE_SIZE):
            if py < 4:
                image.putpixel((ox + px, oy + py), jittered((77, 156, 66), 18, rng))
            else:
                image.putpixel((ox + px, oy + py), jittered((118, 76, 45), 20, rng))
    for px in range(0, TEXTURE_SIZE, 3):
        draw.line((ox + px, oy + 3, ox + px + rng.randint(-1, 1), oy + rng.randint(5, 8)), fill=(69, 132, 58, 255))

    fill_noise("stone", (116, 119, 124), 18)
    ox, oy = tile_origin("stone")
    for _ in range(7):
        x = ox + rng.randrange(2, TEXTURE_SIZE - 2)
        y = oy + rng.randrange(2, TEXTURE_SIZE - 2)
        draw.line((x - 2, y, x + 2, y + rng.choice((-1, 1))), fill=(82, 85, 90, 255))

    fill_noise("metal_ore", (112, 115, 122), 16)
    ox, oy = tile_origin("metal_ore")
    for _ in range(9):
        x = ox + rng.randrange(1, TEXTURE_SIZE - 2)
        y = oy + rng.randrange(1, TEXTURE_SIZE - 2)
        draw.rectangle((x, y, x + 1, y + 1), fill=jittered((207, 168, 89), 18, rng))

    ox, oy = tile_origin("water")
    for px in range(TEXTURE_SIZE):
        for py in range(TEXTURE_SIZE):
            image.putpixel((ox + px, oy + py), jittered((55, 132, 213), 16, rng)[:3] + (170,))
    for py in (4, 10):
        draw.line((ox + 1, oy + py, ox + 14, oy + py + 1), fill=(116, 187, 238, 190))

    ox, oy = tile_origin("wood_side")
    for px in range(TEXTURE_SIZE):
        for py in range(TEXTURE_SIZE):
            shade = 18 if px % 5 == 0 else 9
            image.putpixel((ox + px, oy + py), jittered((116, 72, 36), shade, rng))
    for px in (3, 8, 13):
        draw.line((ox + px, oy, ox + px + rng.choice((-1, 0, 1)), oy + 15), fill=(75, 45, 25, 255))

    fill_noise("wood_top", (136, 92, 50), 12)
    ox, oy = tile_origin("wood_top")
    for inset in (2, 5):
        draw.ellipse((ox + inset, oy + inset, ox + 15 - inset, oy + 15 - inset), outline=(92, 56, 28, 255))

    fill_noise("leaves", (43, 118, 62), 28)
    ox, oy = tile_origin("leaves")
    for _ in range(22):
        x = ox + rng.randrange(TEXTURE_SIZE)
        y = oy + rng.randrange(TEXTURE_SIZE)
        image.putpixel((x, y), jittered((82, 155, 69), 18, rng))

    return Texture(image, filtering=None)


def texture_for_face(block_type: str, normal: Tuple[int, int, int]) -> str:
    if block_type == "grass":
        if normal == (0, 1, 0):
            return "grass_top"
        if normal == (0, -1, 0):
            return "dirt"
        return "grass_side"
    if block_type == "wood":
        return "wood_top" if normal[1] else "wood_side"
    return block_type


def atlas_uvs(tile_name: str) -> List[Tuple[float, float]]:
    tile_index = TEXTURE_INDEX[tile_name]
    inset = 0.04
    tile_width = 1 / len(TEXTURE_TILES)
    u0 = tile_index * tile_width + inset * tile_width
    u1 = (tile_index + 1) * tile_width - inset * tile_width
    v0 = inset
    v1 = 1 - inset
    return [(u0, v0), (u0, v1), (u1, v1), (u1, v0)]


class BlockWorld:
    def __init__(self, block_texture: Texture) -> None:
        self.block_texture = block_texture
        self.blocks: Dict[BlockCoord, str] = {}
        self.chunk_blocks: Dict[ChunkKey, set[BlockCoord]] = {}
        self.height_map: Dict[Tuple[int, int], int] = {}
        self.solid_chunk_entities: Dict[ChunkKey, Entity] = {}
        self.water_chunk_entities: Dict[ChunkKey, Entity] = {}
        self.rng = random.Random(FIXED_SEED)

    def generate(self) -> None:
        self._generate_terrain()
        self._carve_caves()
        self._place_ore()
        self._plant_trees()
        self._prepare_spawn_area()
        self.rebuild_all_chunks()

    def _terrain_height(self, x: int, z: int) -> int:
        broad = value_noise(x, z, 60, FIXED_SEED + 11)
        ridges = abs(value_noise(x, z, 34, FIXED_SEED + 37))
        detail = value_noise(x, z, 13, FIXED_SEED + 73)
        height = SEA_LEVEL + 5 + broad * 7 + ridges * 10 + detail * 2.5
        return int(clamp(round(height), 4, 30))

    def _generate_terrain(self) -> None:
        for x in range(-HALF_WORLD, HALF_WORLD):
            for z in range(-HALF_WORLD, HALF_WORLD):
                h = self._terrain_height(x, z)
                self.height_map[(x, z)] = h

                for y in range(0, h + 1):
                    if y == h and h >= SEA_LEVEL:
                        block_type = "grass"
                    elif y >= h - 3:
                        block_type = "dirt"
                    else:
                        block_type = "stone"
                    self._put_block((x, y, z), block_type)

                if h < SEA_LEVEL:
                    for y in range(h + 1, SEA_LEVEL + 1):
                        self._put_block((x, y, z), "water")

    def _carve_caves(self) -> None:
        cave_count = 24
        for _ in range(cave_count):
            x = self.rng.randint(-HALF_WORLD + 12, HALF_WORLD - 12)
            z = self.rng.randint(-HALF_WORLD + 12, HALF_WORLD - 12)
            surface_y = self.height_map.get((x, z), SEA_LEVEL)
            if surface_y < SEA_LEVEL + 3:
                continue

            angle = self.rng.random() * math.tau
            dx = math.cos(angle)
            dz = math.sin(angle)
            y = surface_y - self.rng.randint(1, 3)
            length = self.rng.randint(18, 36)

            for step in range(length):
                cx = round(x + dx * step + math.sin(step * 0.45) * 1.5)
                cz = round(z + dz * step + math.cos(step * 0.4) * 1.5)
                cy = round(y - step * 0.18 + math.sin(step * 0.33))
                radius = 1.6 + self.rng.random() * 0.7
                self._carve_sphere(cx, cy, cz, radius)

    def _carve_sphere(self, cx: int, cy: int, cz: int, radius: float) -> None:
        r = math.ceil(radius)
        for x in range(cx - r, cx + r + 1):
            for y in range(max(1, cy - r), cy + r + 1):
                for z in range(cz - r, cz + r + 1):
                    if not self.in_bounds(x, z):
                        continue
                    distance = math.sqrt((x - cx) ** 2 + ((y - cy) * 1.15) ** 2 + (z - cz) ** 2)
                    if distance <= radius and self.blocks.get((x, y, z)) != "water":
                        self._pop_block((x, y, z))

    def _place_ore(self) -> None:
        for _ in range(2400):
            x = self.rng.randint(-HALF_WORLD + 2, HALF_WORLD - 3)
            z = self.rng.randint(-HALF_WORLD + 2, HALF_WORLD - 3)
            surface_y = self.height_map.get((x, z), SEA_LEVEL)
            if surface_y < 5:
                continue
            y = self.rng.randint(2, max(3, min(surface_y - 3, 18)))
            if self.blocks.get((x, y, z)) == "stone":
                self.blocks[(x, y, z)] = "metal_ore"

    def _plant_trees(self) -> None:
        for x in range(-HALF_WORLD + 4, HALF_WORLD - 4):
            for z in range(-HALF_WORLD + 4, HALF_WORLD - 4):
                if abs(x) < 8 and abs(z) < 8:
                    continue
                if self.rng.random() > 0.018:
                    continue

                ground_y = self.height_map.get((x, z), 0)
                if ground_y <= SEA_LEVEL or self.blocks.get((x, ground_y, z)) != "grass":
                    continue
                if value_noise(x, z, 26, FIXED_SEED + 501) < -0.15:
                    continue
                self._make_pine_tree(x, ground_y + 1, z)

    def _make_pine_tree(self, x: int, y: int, z: int) -> None:
        trunk_height = self.rng.randint(4, 6)
        for offset in range(trunk_height):
            self.set_block((x, y + offset, z), "wood", rebuild=False)

        top = y + trunk_height
        layers = [(top, 1), (top - 1, 2), (top - 2, 2), (top - 3, 1)]
        for layer_y, radius in layers:
            for lx in range(x - radius, x + radius + 1):
                for lz in range(z - radius, z + radius + 1):
                    if abs(lx - x) + abs(lz - z) <= radius + 1 and self.blocks.get((lx, layer_y, lz)) is None:
                        self.set_block((lx, layer_y, lz), "leaves", rebuild=False)

    def _prepare_spawn_area(self) -> None:
        base_y = max(self.height_map.get((0, 0), SEA_LEVEL + 2), SEA_LEVEL + 2)
        for x in range(-5, 6):
            for z in range(-5, 6):
                distance = max(abs(x), abs(z))
                if distance <= 3:
                    target_y = base_y
                else:
                    target_y = max(base_y - 1, self.height_map.get((x, z), base_y))

                self.height_map[(x, z)] = target_y
                for y in range(0, target_y + 1):
                    if y == target_y:
                        block_type = "grass"
                    elif y >= target_y - 3:
                        block_type = "dirt"
                    else:
                        block_type = "stone"
                    self._put_block((x, y, z), block_type)
                for y in range(target_y + 1, target_y + 7):
                    self._pop_block((x, y, z))

    def in_bounds(self, x: int, z: int) -> bool:
        return -HALF_WORLD <= x < HALF_WORLD and -HALF_WORLD <= z < HALF_WORLD

    def _put_block(self, coord: BlockCoord, block_type: str) -> None:
        x, _, z = coord
        self.blocks[coord] = block_type
        self.chunk_blocks.setdefault(chunk_for(x, z), set()).add(coord)

    def _pop_block(self, coord: BlockCoord) -> Optional[str]:
        removed = self.blocks.pop(coord, None)
        if removed:
            x, _, z = coord
            chunk = self.chunk_blocks.get(chunk_for(x, z))
            if chunk is not None:
                chunk.discard(coord)
        return removed

    def get_block(self, coord: BlockCoord) -> Optional[str]:
        return self.blocks.get(coord)

    def is_solid(self, coord: BlockCoord) -> bool:
        block_type = self.blocks.get(coord)
        return bool(block_type and BLOCKS[block_type].solid)

    def is_water_at(self, coord: BlockCoord) -> bool:
        return self.blocks.get(coord) == "water"

    def set_block(self, coord: BlockCoord, block_type: str, rebuild: bool = True) -> None:
        x, _, z = coord
        if not self.in_bounds(x, z):
            return
        self._put_block(coord, block_type)
        if rebuild:
            self.rebuild_dirty_chunks_near(coord)

    def remove_block(self, coord: BlockCoord) -> Optional[str]:
        removed = self._pop_block(coord)
        if removed:
            self.rebuild_dirty_chunks_near(coord)
        return removed

    def rebuild_all_chunks(self) -> None:
        for key in set(self.chunk_blocks):
            self.rebuild_chunk(key)

    def rebuild_dirty_chunks_near(self, coord: BlockCoord) -> None:
        x, _, z = coord
        keys = {chunk_for(x, z)}
        if (x + HALF_WORLD) % CHUNK_SIZE == 0:
            keys.add(chunk_for(x - 1, z))
        if (x + HALF_WORLD + 1) % CHUNK_SIZE == 0:
            keys.add(chunk_for(x + 1, z))
        if (z + HALF_WORLD) % CHUNK_SIZE == 0:
            keys.add(chunk_for(x, z - 1))
        if (z + HALF_WORLD + 1) % CHUNK_SIZE == 0:
            keys.add(chunk_for(x, z + 1))
        for key in keys:
            self.rebuild_chunk(key)

    def rebuild_chunk(self, key: ChunkKey) -> None:
        old_solid = self.solid_chunk_entities.pop(key, None)
        old_water = self.water_chunk_entities.pop(key, None)
        if old_solid:
            destroy(old_solid)
        if old_water:
            destroy(old_water)

        solid_mesh = self._build_mesh_for_chunk(key, include_water=False)
        if solid_mesh:
            entity = Entity(model=solid_mesh, texture=self.block_texture, collider="mesh", double_sided=True)
            self.solid_chunk_entities[key] = entity

        water_mesh = self._build_mesh_for_chunk(key, include_water=True)
        if water_mesh:
            entity = Entity(model=water_mesh, texture=self.block_texture, double_sided=True)
            entity.alpha = 0.72
            self.water_chunk_entities[key] = entity

    def _build_mesh_for_chunk(self, key: ChunkKey, include_water: bool) -> Optional[Mesh]:
        vertices: List[Vec3] = []
        triangles: List[int] = []
        colors: List[color.Color] = []
        uvs: List[Tuple[float, float]] = []

        start_x = key[0] * CHUNK_SIZE - HALF_WORLD
        start_z = key[1] * CHUNK_SIZE - HALF_WORLD
        end_x = min(start_x + CHUNK_SIZE, HALF_WORLD)
        end_z = min(start_z + CHUNK_SIZE, HALF_WORLD)

        for coord in self.chunk_blocks.get(key, ()):
            x, y, z = coord
            if not (start_x <= x < end_x and start_z <= z < end_z):
                continue
            block_type = self.blocks.get(coord)
            if not block_type:
                continue
            is_water = block_type == "water"
            if include_water != is_water:
                continue
            info = BLOCKS[block_type]

            for normal, face_vertices, shade in FACE_DATA:
                neighbor = (x + normal[0], y + normal[1], z + normal[2])
                neighbor_type = self.blocks.get(neighbor)
                if is_water:
                    if neighbor_type == "water":
                        continue
                else:
                    if neighbor_type and BLOCKS[neighbor_type].solid:
                        continue

                start_index = len(vertices)
                vertices.extend(Vec3(x + vx, y + vy, z + vz) for vx, vy, vz in face_vertices)
                triangles.extend(
                    [
                        start_index,
                        start_index + 1,
                        start_index + 2,
                        start_index,
                        start_index + 2,
                        start_index + 3,
                    ]
                )
                colors.extend([face_shade(shade, info.tint.a)] * 4)
                uvs.extend(atlas_uvs(texture_for_face(block_type, normal)))

        if not vertices:
            return None

        mesh = Mesh(vertices=vertices, triangles=triangles, colors=colors, uvs=uvs, mode="triangle")
        mesh.generate()
        return mesh

    def surface_y(self, x: int, z: int) -> int:
        for y in range(48, -1, -1):
            block_type = self.blocks.get((x, y, z))
            if block_type and BLOCKS[block_type].solid and block_type not in {"wood", "leaves"}:
                return y
        return -1


class Inventory:
    def __init__(self) -> None:
        self.counts: Dict[str, int] = {block: 0 for block in HOTBAR}
        self.counts["dirt"] = 25
        self.selected_index = 0

    @property
    def selected_block(self) -> str:
        return HOTBAR[self.selected_index]

    def add(self, block_type: str) -> None:
        if block_type in self.counts:
            self.counts[block_type] += 1

    def can_place_selected(self) -> bool:
        return self.counts.get(self.selected_block, 0) > 0

    def consume_selected(self) -> bool:
        block_type = self.selected_block
        if self.counts.get(block_type, 0) <= 0:
            return False
        self.counts[block_type] -= 1
        return True

    def select_next(self) -> None:
        self.selected_index = (self.selected_index + 1) % len(HOTBAR)

    def select_previous(self) -> None:
        self.selected_index = (self.selected_index - 1) % len(HOTBAR)

    def select_slot(self, index: int) -> None:
        if 0 <= index < len(HOTBAR):
            self.selected_index = index


class Creature(Entity):
    def __init__(self, world: BlockWorld, creature_type: str, position: Vec3, rng: random.Random) -> None:
        super().__init__(position=position)
        self.world = world
        self.creature_type = creature_type
        self.rng = rng
        self.speed = rng.uniform(0.35, 0.75)
        self.wander_timer = rng.uniform(0.8, 2.5)
        self.direction = Vec3(rng.uniform(-1, 1), 0, rng.uniform(-1, 1)).normalized()
        self._build_model()

    def _cube(self, position: Tuple[float, float, float], scale: Tuple[float, float, float], tint: color.Color) -> Entity:
        return Entity(parent=self, model="cube", position=position, scale=scale, color=tint, collider=None)

    def _build_model(self) -> None:
        if self.creature_type == "goat":
            self._build_goat()
        elif self.creature_type == "monkey":
            self._build_monkey()
        elif self.creature_type == "beaver":
            self._build_beaver()
        elif self.creature_type == "bear":
            self._build_bear()

    def _build_goat(self) -> None:
        body = color.rgb32(218, 216, 201)
        dark = color.rgb32(64, 56, 49)
        horn = color.rgb32(238, 229, 188)
        self._cube((0, 0.7, 0), (1.2, 0.55, 0.5), body)
        self._cube((0.72, 0.86, 0), (0.42, 0.38, 0.38), body)
        self._cube((0.9, 1.12, -0.13), (0.12, 0.28, 0.08), horn)
        self._cube((0.9, 1.12, 0.13), (0.12, 0.28, 0.08), horn)
        for lx in (-0.35, 0.35):
            for lz in (-0.16, 0.16):
                self._cube((lx, 0.28, lz), (0.14, 0.55, 0.12), dark)

    def _build_monkey(self) -> None:
        body = color.rgb32(111, 68, 43)
        face = color.rgb32(184, 127, 83)
        self._cube((0, 0.62, 0), (0.72, 0.8, 0.45), body)
        self._cube((0.45, 1.08, 0), (0.5, 0.48, 0.42), body)
        self._cube((0.6, 1.05, 0), (0.2, 0.22, 0.24), face)
        self._cube((-0.48, 0.92, 0), (0.18, 0.18, 0.9), body)
        for lx in (-0.2, 0.2):
            self._cube((lx, 0.23, 0), (0.13, 0.45, 0.13), body)

    def _build_beaver(self) -> None:
        body = color.rgb32(116, 72, 45)
        tail = color.rgb32(82, 49, 30)
        pineapple = color.rgb32(226, 184, 54)
        leaves = color.rgb32(49, 147, 67)
        self._cube((0, 0.55, 0), (1.05, 0.62, 0.5), body)
        self._cube((0.65, 0.88, 0), (0.46, 0.46, 0.42), pineapple)
        self._cube((0.65, 1.2, 0), (0.42, 0.14, 0.42), leaves)
        self._cube((-0.67, 0.42, 0), (0.16, 0.45, 0.7), tail)
        for lx in (-0.3, 0.3):
            self._cube((lx, 0.18, 0), (0.16, 0.34, 0.16), body)

    def _build_bear(self) -> None:
        body = color.rgb32(76, 46, 31)
        muzzle = color.rgb32(150, 103, 68)
        orange = color.rgb32(245, 126, 37)
        self._cube((0, 0.76, 0), (1.45, 0.78, 0.68), body)
        self._cube((0.9, 1.08, 0), (0.58, 0.52, 0.5), body)
        self._cube((1.18, 1.0, 0), (0.18, 0.2, 0.28), muzzle)
        for lx in (-0.45, 0.45):
            for lz in (-0.22, 0.22):
                self._cube((lx, 0.26, lz), (0.18, 0.52, 0.16), body)
        Text(
            parent=self,
            text="Go Griz!",
            position=(-0.48, 1.17, -0.18),
            rotation=(90, 0, 0),
            scale=0.52,
            color=orange,
            origin=(0, 0),
        )

    def update(self) -> None:
        self.wander_timer -= time.dt
        if self.wander_timer <= 0:
            self.wander_timer = self.rng.uniform(1.0, 3.6)
            self.direction = Vec3(self.rng.uniform(-1, 1), 0, self.rng.uniform(-1, 1)).normalized()
            self.rotation_y = math.degrees(math.atan2(self.direction.x, self.direction.z)) + 90

        candidate = self.position + self.direction * self.speed * time.dt
        x = round(candidate.x)
        z = round(candidate.z)
        if not self.world.in_bounds(x, z):
            self.direction *= -1
            return

        ground_y = self.world.surface_y(x, z)
        if ground_y < SEA_LEVEL:
            self.direction *= -1
            return

        self.position = Vec3(candidate.x, ground_y + 0.05, candidate.z)


class Game:
    def __init__(self) -> None:
        self.app = Ursina()
        window.title = "Python Block-Based Sandbox"
        window.borderless = False
        window.exit_button.visible = False
        window.fps_counter.enabled = True
        camera.clip_plane_far = 260

        self.block_texture = build_block_texture_atlas()
        self.world = BlockWorld(self.block_texture)
        loading_text = Text(text="Generating 200 x 200 block world...", origin=(0, 0), scale=1.5)
        self.world.generate()
        destroy(loading_text)

        self.inventory = Inventory()
        self.player = FirstPersonController()
        self.player.speed = 6
        self.player.jump_height = 1.5
        self.player.mouse_sensitivity = Vec3(40, 40, 0)
        spawn_y = self.world.surface_y(0, 0) + 2
        self.player.position = Vec3(0, spawn_y, 0)

        self.paused = False
        self.time_of_day = 0.23
        self.mine_target: Optional[BlockCoord] = None
        self.mine_progress = 0.0
        self.current_hit = None

        self.sun = DirectionalLight(rotation=(45, -35, 35), shadows=False)
        self.ambient = AmbientLight(color=color.rgba32(110, 125, 145, 255))

        self.crosshair = Text(text="+", origin=(0, 0), scale=1.6, color=color.white)
        self.hud = Text(text="", position=(-0.865, 0.47), origin=(-0.5, 0.5), scale=0.95, color=color.white)
        self.status = Text(text="", position=(-0.865, 0.405), origin=(-0.5, 0.5), scale=0.75, color=color.azure)
        self.target_marker = Entity(model="cube", wireframe=True, color=color.rgba32(255, 255, 255, 128), scale=1.01, visible=False)

        self.creatures: List[Creature] = []
        self._spawn_creatures()
        self._update_light()
        self._update_hud()

    def _spawn_creatures(self) -> None:
        rng = random.Random(FIXED_SEED + 9001)
        roster = ["goat"] * 6 + ["monkey"] * 4 + ["beaver"] * 4 + ["bear"] * 3
        for creature_type in roster:
            for _ in range(100):
                x = rng.randint(-HALF_WORLD + 10, HALF_WORLD - 10)
                z = rng.randint(-HALF_WORLD + 10, HALF_WORLD - 10)
                if abs(x) < 12 and abs(z) < 12:
                    continue
                ground_y = self.world.surface_y(x, z)
                if ground_y > SEA_LEVEL and self.world.get_block((x, ground_y + 1, z)) is None:
                    self.creatures.append(Creature(self.world, creature_type, Vec3(x, ground_y + 0.05, z), rng))
                    break

    def _update_hud(self) -> None:
        block_type = self.inventory.selected_block
        block_name = BLOCKS[block_type].display_name
        count = self.inventory.counts.get(block_type, 0)
        slot_parts = []
        for index, item in enumerate(HOTBAR, start=1):
            label = BLOCKS[item].display_name.split()[0]
            if index - 1 == self.inventory.selected_index:
                slot_parts.append(f"[{index}:{label}]")
            else:
                slot_parts.append(f"{index}:{label}")
        self.hud.text = (
            f"Axe equipped | Selected: {block_name} x{count}\n"
            f"{'  '.join(slot_parts)}\n"
            "LMB mine | RMB place | Space jump/swim | Shift sink | Esc release mouse"
        )

    def _set_status(self, message: str) -> None:
        self.status.text = message

    def _update_light(self) -> None:
        phase = self.time_of_day % 1.0
        sun_height = math.sin(phase * math.tau)
        day_amount = clamp((sun_height + 0.2) / 1.2, 0, 1)
        sky_day = color.rgb32(102, 177, 232)
        sky_night = color.rgb32(14, 20, 43)
        ambient_day = color.rgba32(140, 145, 135, 255)
        ambient_night = color.rgba32(38, 45, 75, 255)

        scene.clear_color = color.rgba(
            lerp(sky_night.r, sky_day.r, day_amount),
            lerp(sky_night.g, sky_day.g, day_amount),
            lerp(sky_night.b, sky_day.b, day_amount),
            1,
        )
        scene.fog_color = scene.clear_color
        scene.fog_density = lerp(0.02, 0.007, day_amount)
        self.ambient.color = color.rgba(
            lerp(ambient_night.r, ambient_day.r, day_amount),
            lerp(ambient_night.g, ambient_day.g, day_amount),
            lerp(ambient_night.b, ambient_day.b, day_amount),
            1,
        )
        self.sun.rotation = (phase * 360 - 90, -35, 25)
        self.sun.color = color.rgb32(255, int(lerp(180, 245, day_amount)), int(lerp(140, 225, day_amount)))

    def _player_in_water(self) -> bool:
        head = block_from_world_point(self.player.position + Vec3(0, 1.0, 0))
        feet = block_from_world_point(self.player.position + Vec3(0, 0.2, 0))
        return self.world.is_water_at(head) or self.world.is_water_at(feet)

    def _update_water_movement(self) -> None:
        if self._player_in_water():
            self.player.gravity = 0
            self.player.speed = 3.2
            if held_keys["space"]:
                self.player.y += 2.4 * time.dt
            elif held_keys["shift"]:
                self.player.y -= 2.0 * time.dt
            else:
                self.player.y -= 0.35 * time.dt
            self._set_status("In water")
        else:
            self.player.gravity = 1
            self.player.speed = 6
            if not self.status.text.startswith("Mining"):
                self._set_status("")

    def _update_target(self) -> None:
        hit = raycast(camera.world_position, camera.forward, distance=MAX_INTERACT_DISTANCE, ignore=[self.player])
        self.current_hit = hit if hit.hit else None
        if hit.hit:
            coord = block_from_world_point(hit.world_point - hit.normal * 0.03)
            self.target_marker.position = Vec3(*coord)
            self.target_marker.visible = True
        else:
            self.target_marker.visible = False

    def _update_mining(self) -> None:
        if not held_keys["left mouse"] or not self.current_hit:
            self.mine_target = None
            self.mine_progress = 0.0
            if self.status.text.startswith("Mining"):
                self._set_status("")
            return

        coord = block_from_world_point(self.current_hit.world_point - self.current_hit.normal * 0.03)
        block_type = self.world.get_block(coord)
        if not block_type or block_type == "water":
            self.mine_target = None
            self.mine_progress = 0.0
            return

        if coord != self.mine_target:
            self.mine_target = coord
            self.mine_progress = 0.0

        hardness = BLOCKS[block_type].hardness
        self.mine_progress += time.dt
        percent = int(clamp(self.mine_progress / hardness, 0, 1) * 100)
        self._set_status(f"Mining {BLOCKS[block_type].display_name}: {percent}%")

        if self.mine_progress >= hardness:
            removed = self.world.remove_block(coord)
            if removed and BLOCKS[removed].collectible:
                self.inventory.add(removed)
            self.mine_target = None
            self.mine_progress = 0.0
            self._update_hud()

    def _block_would_hit_player(self, coord: BlockCoord) -> bool:
        x, y, z = coord
        return (
            abs(self.player.x - x) < 0.85
            and abs(self.player.z - z) < 0.85
            and self.player.y - 0.4 < y < self.player.y + 2.1
        )

    def place_selected_block(self) -> None:
        if not self.current_hit:
            return
        place_coord = block_from_world_point(self.current_hit.world_point + self.current_hit.normal * 0.55)
        if self._block_would_hit_player(place_coord):
            self._set_status("Cannot place inside yourself")
            return
        existing = self.world.get_block(place_coord)
        if existing and BLOCKS[existing].solid:
            self._set_status("That space is blocked")
            return
        if not self.inventory.can_place_selected():
            self._set_status("No blocks of that type")
            return
        block_type = self.inventory.selected_block
        if self.inventory.consume_selected():
            self.world.set_block(place_coord, block_type)
            self._update_hud()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        mouse.locked = not self.paused
        self.player.enabled = not self.paused
        self.crosshair.enabled = not self.paused
        self._set_status("Paused - click the game window to resume" if self.paused else "")

    def input(self, key: str) -> None:
        if key == "escape":
            self.toggle_pause()
        elif self.paused and key == "left mouse down":
            self.toggle_pause()
        elif key == "right mouse down" and not self.paused:
            self.place_selected_block()
        elif key == "scroll down":
            self.inventory.select_next()
            self._update_hud()
        elif key == "scroll up":
            self.inventory.select_previous()
            self._update_hud()
        elif key in {"1", "2", "3", "4", "5", "6"}:
            self.inventory.select_slot(int(key) - 1)
            self._update_hud()
        elif key == "left mouse up":
            self.mine_target = None
            self.mine_progress = 0.0

    def update(self) -> None:
        if self.paused:
            return

        self.time_of_day = (self.time_of_day + time.dt / DAY_LENGTH_SECONDS) % 1.0
        self._update_light()
        self._update_water_movement()
        self._update_target()
        self._update_mining()

    def run(self) -> None:
        self.app.run()


game: Optional[Game] = None


def update() -> None:
    if game:
        game.update()


def input(key: str) -> None:
    if game:
        game.input(key)


if __name__ == "__main__":
    game = Game()
    game.run()
