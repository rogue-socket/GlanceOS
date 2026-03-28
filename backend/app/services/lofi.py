import random
from datetime import datetime

# ASCII-only lofi scenes. Each scene is a tuple: (art, label).

_SCENES = [
    (
                r"""
            _._     _,-'""`-._
         (,-.`._,'(       |\'-/|
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
        +---------------+
        |   ~~ LOFI ~~  |
        |               |
        |  beats to     |
        |  code to      |
        |               |
        +---------------+
""",
                "beats to code to",
    ),
    (
                r"""
         .  *  . .  * .  .
     .  .  *  .  . . *
    ---------------------
    /  3:AM      ######  \
 |  coffee      ~~~     |
 |  and code    v0.1.0  |
    \_____________________/
""",
                "3am vibes",
    ),
    (
                r"""
        _____
     |     |
     | | | |
     |_____|
     _|___|_
    |  ___  |
    | |   | |  ~~~
    | |___| |
    |_______|
""",
        "radio vibes",
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
]

_ANIMATED_SCENES = [
        {
                "label": "spinning donut",
                "frame_ms": 120,
                "frames": [
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
     /  .'   '.  \   *
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
        '.  '-'  .'  *
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
     /  .'   '.  \
    |  |  (_)  |  |  *
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
    *   '-...-'
''',
                        r'''
            .-"""-.
        .'  .-.  '.
     /  .'   '.  \
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
