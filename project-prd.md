# Program Requirements Document (PRD)
## Python Block-Based Sandbox

## 1. Overview

This program is a single-player sandbox video game where the player explores, gathers resources, builds structures, and survives in a blocky, procedurally generated 3D world.

The first version should be a simple but playable Minecraft-like prototype built in Python. It should be useful both as a small game and as an example for middle school students learning how a clear PRD can guide vibe coding.

## 2. Purpose

The purpose of this project is to demonstrate that a well-written PRD can help a person create complex software even if they are not yet a programmer.

The PRD should clearly describe what the program should do, who it is for, what features it needs, how it should look and feel, and what technical preferences should guide implementation.

## 3. Target Users

- Casual sandbox game players.
- Students observing how a PRD can guide code generation.
- A single local player using the program on one computer.

No authentication, accounts, roles, or online services are required.

## 4. Core Gameplay Loop

The player should repeatedly move through this loop:

1. Explore the world.
2. Gather blocks and resources.
3. Build or improve a shelter.
4. Experience the day/night cycle.
5. Avoid or observe passive monsters.
6. Explore more of the world.

Crafting is part of the long-term fantasy of the game, but crafting recipes are not required in the first playable version.

## 5. First Playable Version Scope

The first version must include:

- Procedural 3D world generation.
- First-person player movement.
- WASD keyboard movement.
- Mouse-controlled camera look.
- Jumping and falling.
- Mining or removing blocks.
- Placing blocks.
- A basic inventory.
- A visible day/night cycle.
- Passive monsters or creatures that can appear in the world.
- Basic water movement.

The first version does not need combat, fall damage, multiplayer, saving/loading, hunger, weather, advanced crafting, or complex NPC behavior.

## 6. World and Environment

The world should be a block-based 3D environment inspired by Western Montana.

The first world should be medium-sized and explorable. It should be large enough for the player to walk around, find resources, see terrain variation, and discover passive creatures, but it does not need to be infinite.

World generation may use a fixed seed, a random seed, or no explicit seed. The implementer should choose whichever approach is simplest for the chosen Python 3D framework.

The first version should use one general biome rather than multiple biome types. The environment may include:

- Mountains or hills.
- Grass-covered terrain.
- Dirt and stone layers.
- Pine-like forests.
- Rivers, streams, or lakes.
- Caves or cave-like openings if feasible.
- Metal ore or other mineable resources.

The world should feel open enough for exploration, but it should stay small enough to run smoothly on a typical classroom computer.

## 7. Block Catalog

| Name | Description |
|:---|:---|
| Grass | Surface block used for natural ground. |
| Dirt | Common terrain block found below grass and near the surface. |
| Stone | Common underground and mountain block. |
| Metal Ore | Mineable resource block found inside stone or underground areas. |
| Water | Non-solid environmental block used for lakes, rivers, or streams. |
| Wood | Resource block from trees. |
| Leaves | Tree foliage block, mainly decorative in the first version. |

Additional block types may be added if they support exploration, mining, or building without making the first version too complex.

## 8. Player Controls

The game should use a first-person 3D perspective.

Expected controls:

- `W`, `A`, `S`, `D`: Move the player.
- Mouse movement: Look around.
- `Space`: Jump. When underwater, swim upward.
- `Shift`: Sink downward while underwater.
- Left mouse button: Mine or remove the targeted block.
- Right mouse button: Place the selected block.
- Number keys or scroll wheel: Select inventory item.
- `Esc`: Pause or release mouse control.

Exact key bindings may be adjusted by the implementer if the chosen Python 3D framework has common defaults.

## 9. Core Features

### 9.1 Procedural World Generation

The program should generate a 3D block world when the game starts.

The terrain should include height variation so the world feels natural rather than flat. The world should contain surface blocks, underground blocks, water areas, trees, and mineable resources.

### 9.2 Movement and Camera

The player should be able to walk through the world in first person using WASD and mouse look.

The player should not fall through the world or pass through solid terrain.

The player should be able to jump and fall. Fall damage is not required.

### 9.3 Mining Blocks

The player should be able to target nearby blocks and remove them from the world.

When a block is mined, it should be added to the player's inventory unless the block type is not collectible.

The player should start with an axe. The axe may be used as the default tool for mining or gathering in the first version.

### 9.4 Placing Blocks

The player should be able to select a block from the inventory and place it into the world.

Placed blocks should align to the world's block grid.

The player should not be able to place a block inside their own body or in another blocked space.

### 9.5 Basic Inventory

The inventory should track the quantity of collected block types.

The player should start with an axe in the inventory.

The interface should show the currently selected block or tool and the quantity available when relevant. The first version does not need a full inventory screen.

### 9.6 Day/Night Cycle

The game should transition visibly between day and night.

The cycle may affect lighting, sky color, and overall mood. Night should feel different from day, but it does not need to add combat danger in the first version.

### 9.7 Passive Monsters

Passive monsters or creatures should appear in the world.

They may wander, idle, or move simply. They should not attack the player in the first version.

Expected passive creature types:

- Goat.
- Monkey.
- Beaver with a pineapple for a head.
- Bear with "Go Griz!" on its back.

Creature models may be simple blocky approximations as long as each creature type is visually distinguishable.

### 9.8 Water Movement

Water should be enterable.

When the player enters water, they should be able to sink below the surface. The player can swim upward with `Space` and sink downward with `Shift`.

The player can breathe underwater in the first version. No drowning, oxygen meter, or underwater health system is required.

## 10. Out of Scope for First Version

The following features should not be required in the first playable version:

- Crafting recipes.
- Combat.
- Fall damage.
- Hostile monsters.
- Multiplayer.
- Saving and loading.
- Multiple biomes.
- Hunger.
- Weather.
- Complex NPC behavior.
- Drowning or oxygen management.
- User accounts or online services.

These features may be considered later after the first playable version works well.

## 11. Look and Feel

The game should have a familiar Minecraft-like blocky style.

Visual priorities:

- Clear block shapes.
- Bright, readable colors.
- Simple textures or colored materials.
- A friendly, classroom-appropriate tone.
- A world that is easy to understand at a glance.

The game should not aim for realistic graphics. Familiarity and clarity are more important than visual complexity.

## 12. Technical Preferences

- The program should be written in Python.
- The implementer may choose the Python 3D framework.
- The program should run locally on a computer.
- The user should not need to compile the code before running it.
- The implementation may use complex code if needed.
- The code should prioritize meeting the PRD requirements over being beginner-level code.

The PRD is intended to show that non-programmers can guide complex software development by clearly describing the desired result.

## 13. Interface Requirements

The first version should include a minimal in-game interface.

The interface should show:

- Current selected block.
- Quantity of selected block available.
- A simple crosshair or targeting indicator.
- Optional health or status display if useful.

Menus should be simple and should not distract from exploration and building.

## 14. Setup and Run Requirements

The project should include clear setup and run instructions.

Expected project files:

- `README.md` with installation and run instructions.
- `requirements.txt` listing Python package dependencies, if external packages are used.
- Main Python entry point, such as `main.py`, `game.py`, or another clearly named file.

The program should be runnable locally with a small number of commands. The user should not need to compile the program before running it.

## 15. State Management

The program should track:

- Player position.
- Camera direction.
- Existing world blocks.
- Blocks removed by the player.
- Blocks placed by the player.
- Inventory quantities.
- Current selected inventory item.
- Time of day.
- Passive monster positions.
- Whether the player is in water.

Persistent storage is not required for the first version.

## 16. Edge Cases

The program should handle common edge cases gracefully:

- Player tries to mine too far away.
- Player tries to place a block with none available.
- Player tries to place a block inside an occupied space.
- Player reaches the edge of the generated world.
- Player enters water.
- Player swims upward in water.
- Player sinks downward in water.
- Player mines a block below or beside themselves.
- Inventory reaches zero for the selected block.
- Passive monsters collide with terrain or obstacles.

## 17. Success Criteria

The first version is successful when:

- A block-based 3D world generates when the program starts.
- The world is medium-sized and explorable.
- The player can walk around in first person using WASD and mouse look.
- The player can jump and fall without fall damage.
- The player can mine blocks.
- Mined blocks are added to a basic inventory.
- The player can place collected blocks back into the world.
- The player starts with an axe.
- The world visibly changes between day and night.
- The player can enter water, sink, and swim upward.
- The player can breathe underwater without taking damage.
- Passive creatures appear and move or idle without attacking.
- The game runs locally without crashing during normal play.

## 18. Acceptance Checklist

Use this checklist to evaluate whether an implementation satisfies the first playable version:

- [ ] The game starts from a clearly documented Python command.
- [ ] Required dependencies are documented in `README.md` or `requirements.txt`.
- [ ] A medium-sized 3D block world generates.
- [ ] The world has a Western Montana-inspired feel.
- [ ] The player can move with `W`, `A`, `S`, and `D`.
- [ ] The player can look around with the mouse.
- [ ] The player can jump and fall.
- [ ] The player can mine blocks.
- [ ] Mined blocks appear in the inventory.
- [ ] The player can place available blocks.
- [ ] The player starts with an axe.
- [ ] The selected block or tool is visible in the interface.
- [ ] The day/night cycle is visible.
- [ ] Water can be entered.
- [ ] The player can swim upward with `Space`.
- [ ] The player can sink downward with `Shift`.
- [ ] The player can remain underwater without drowning.
- [ ] Passive goats, monkeys, pineapple-headed beavers, and bears with "Go Griz!" on their backs appear.
- [ ] Passive creatures do not attack the player.
- [ ] The game does not require accounts, internet access, compilation, or multiplayer services.
- [ ] The game avoids out-of-scope systems such as combat, hunger, weather, saving/loading, and crafting recipes.

## 19. Future Enhancements

Possible future features include:

- Crafting recipes.
- Tools such as pickaxes, axes, and shovels.
- Hostile monsters at night.
- Health and damage.
- Saving and loading worlds.
- Multiple biomes.
- More resources and block types.
- More advanced caves.
- Sound effects and music.
- Simple objectives or achievements.
