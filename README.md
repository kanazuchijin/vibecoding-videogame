# Vibe Coding A Video Game with AI

This is a first playable Python prototype for the block-based sandbox described
in `project-prd.md`.

## What Is Included

- A fixed-seed 200 x 200 block world.
- Minecraft-like first-person movement.
- Block mining and placement.
- A minimal inventory and hotbar.
- Hills, grass, dirt, stone, ore, trees, still water, and simple cave openings.
- Swim upward with `Space` and sink with `Shift` when in water.
- A visible day/night cycle.
- Passive blocky creatures: goats, monkeys, pineapple-headed beavers, and bears
  with `Go Griz!` on their backs.

## Linux Setup

Create a virtual environment and install the dependency:

```bash
python3 -m venv --clear .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Debian or Ubuntu, install the matching `python3-venv` package first if the
virtual environment or `pip` command is missing. For example, this machine's
Python asks for `python3.13-venv`.

Run the game:

```bash
python main.py
```

If the game window does not open, make sure the demonstration machine has
working OpenGL graphics drivers. Ursina uses Panda3D underneath.

## Controls

- `W`, `A`, `S`, `D`: move
- Mouse: look around
- `Space`: jump, or swim upward in water
- `Shift`: sink downward in water
- Left mouse button: mine the targeted block
- Right mouse button: place the selected block
- Number keys `1` through `6`: select a hotbar block
- Mouse wheel: change selected block
- `Esc`: pause or release mouse control

The player starts with an axe equipped and 25 dirt blocks for immediate
building.
