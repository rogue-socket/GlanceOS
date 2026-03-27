import random
from datetime import datetime

# ── Lofi ASCII Art Scenes ─────────────────────────────
# Each scene is a tuple: (art, label)

_SCENES = [
    (
r"""
     _._     _,-'""`-._
    (,-.`._,'(       |\`-/|
        `-.-' \ )-`( , o o)
              `-    \`_`"'-
""",
        "chill cat",
    ),
    (
r"""
        |\      _,,,---,,_
  ZZZzz /,`.-'`'    -.  ;-;;,_
       |,4-  ) )-,_. ,\ (  `'-'
      '---''(_/--'  `-'\_)
""",
        "sleepy cat",
    ),
    (
r"""
    .---.        .-.
   /  .  \      / | \
   |\_/|   |    /  |  \
   |   |   |   /   |   \
  _|   |_  |  / /| | |\ \
 | |   | |_|_/ / | | | \ \_
 |  \   \      / /  | |  \ \
  \  `.  `.   / /   `-'   ) )
   `.  `-. `-'  /        (_/
     `-.__`-' ,'
""",
        "mountains",
    ),
    (
r"""
         .         .
        .  *    . .   *
    .  *   .  .    .
   ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
  ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
 ________________________
 |  _  ___ ___  _  ___ |
 | |_| |_  |_| |_| |_  |
 | | | |__ | | | | |__ |
 |______________________|
""",
        "lofi radio",
    ),
    (
r"""
      *  .  *   .   *
   .    *    .   *   .
  .  *    .    .   *
 .-"""""""""""""""""""-.
 |  ~/music/lofi.mp3  |
 |  ▶ playing...      |
 |  ████████░░ 78%    |
 '-.....................'
""",
        "now playing",
    ),
    (
r"""
   _____
  |     |
  | | | |
  |_____|
  _|___|_
 |  ___  |
 | |   | |   ♪ ♫ ♪
 | |___| |
 |_______|
""",
        "radio vibes",
    ),
    (
r"""
  ╔═══════════════╗
  ║  ~~  LOFI  ~~ ║
  ║               ║
  ║  ♪ ♫  ♪ ♫  ♪ ║
  ║    beats to   ║
  ║   code to     ║
  ║               ║
  ╚═══════════════╝
""",
        "beats to code to",
    ),
    (
r"""
        *   .       .
     .    *      *
   .  .      .        *
  .       .      .
 _||__|  __   __|__
 |      |  | |     |
 |  ||  |__| |  |  |
 |__||__|    |__|__|
""",
        "night city",
    ),
    (
r"""
  .  *  .  . *  .  *
    .  *  . .  .   .
  ___________________
 /                   \
|   (  ) _   _  (  )  |
|    ||  |\ /|   ||    |
|    ||  | v |   ||    |
 \___________________/
  ---- === === ----
""",
        "window view",
    ),
    (
r"""
     .  *  . .  * .  .
   .  .  *  .  . . *
  ─────────────────────
  ╭─────────╮
  │  ✧ 3:AM │  ░░▒▒▓▓█
  │  coffee  │  ♪ ~ ♫ ~
  │  & code  │  v0.1.0
  ╰─────────╯
""",
        "3am vibes",
    ),
]

_ANIMATED_SCENES = [
        {
                "label": "spinning donut",
                "frame_ms": 120,
                "frames": [
                        r'''
            *
        .-"""-.
    .'  .-.  '.
 /  .'   '.  \
|  |  (_)  |  |
 \  '.   .'  /
    '.  '-'  .'
        '-...-'
''',
                        r'''
                            *
        .-"""-.
    .'  .-.  '.
 /  .'   '.  \
|  |  (_)  |  |
 \  '.   .'  /
    '.  '-'  .'
        '-...-'
''',
                        r'''
        .-"""-.
    .'  .-.  '.
 /  .'   '.  \
|  |  (_)  |  |
 \  '.   .'  /
    '.  '-'  .'
        '-...-'
            *
''',
                        r'''
        .-"""-.
    .'  .-.  '.
 /  .'   '.  \
|  |  (_)  |  |   *
 \  '.   .'  /
    '.  '-'  .'
        '-...-'
''',
                        r'''
        .-"""-.
    .'  .-.  '.
 /  .'   '.  \
|  |  (_)  |  |
 \  '.   .'  /
    '.  '-'  .'   *
        '-...-'
''',
                        r'''
        .-"""-.
    .'  .-.  '.
 /  .'   '.  \
|  |  (_)  |  |
 \  '.   .'  /
    '.  '-'  .'
*   '-...-'
''',
                        r'''
        .-"""-.
* .'  .-.  '.
 /  .'   '.  \
|  |  (_)  |  |
 \  '.   .'  /
    '.  '-'  .'
        '-...-'
''',
                        r'''
        .-"""-.
    .'  .-.  '.
* /  .'   '.  \
|  |  (_)  |  |
 \  '.   .'  /
    '.  '-'  .'
        '-...-'
''',
                ],
        },
]


def get_lofi_scene() -> dict:
    """Return a random lofi ASCII art scene."""
    if _ANIMATED_SCENES and random.random() < 0.35:
        animated_scene = random.choice(_ANIMATED_SCENES)
        return {
            "type": "lofi",
            "data": {
                "frames": animated_scene["frames"],
                "frame_ms": animated_scene["frame_ms"],
                "label": animated_scene["label"],
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    art, label = random.choice(_SCENES)
    return {
        "type": "lofi",
        "data": {
            "art": art,
            "label": label,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


def get_all_scenes() -> list[dict]:
    """Return all scenes for cycling."""
    scenes = [{"art": art, "label": label} for art, label in _SCENES]
    scenes.extend(
        {
            "art": scene["frames"][0],
            "label": scene["label"],
            "frames": scene["frames"],
            "frame_ms": scene["frame_ms"],
        }
        for scene in _ANIMATED_SCENES
    )
    return scenes
