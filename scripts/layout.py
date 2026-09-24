"""Hole-to-key assignment shared by the PCB and firmware generators."""

# Pro Micro / nice!nano pinout, top view, USB up, components facing viewer
NANO_LEFT = ["P0.06", "P0.08", "GND", "GND", "P0.17", "P0.20",
             "P0.22", "P0.24", "P1.00", "P0.11", "P1.04", "P1.06"]
NANO_RIGHT = ["B+", "GND", "RST", "3V3", "P0.31", "P0.29",
              "P0.02", "P1.15", "P1.13", "P1.11", "P0.10", "P0.09"]

# key references as they are on the cheapino PCB, pinky -> inner
KEY_ROWS = [
    ["K13", "K10", "K7", "K4", "K1"],   # top
    ["K14", "K11", "K8", "K5", "K2"],   # home
    ["K15", "K12", "K9", "K6", "K3"],   # bottom
]
THUMBS = ["K18", "K17", "K16"]          # nearest the keys -> furthest out

# nano hole -> key. KA/KB are rows 0/1, routed through jumpers because the
# power pins opposite them can't be swapped in firmware.
HOLE_TO_KEY = {
    "KA": "K1", "KB": "K4",
    "L4": "K7", "L5": "K10", "L6": "K13",
    "L7": "K2", "L8": "K5", "L9": "K8", "L10": "K11", "L11": "K14",
    "R4": "K3", "R5": "K6", "R6": "K9", "R7": "K12", "R8": "K15",
    "R9": "K18", "R10": "K17", "R11": "K16",
}


def key_pin(hole, back):
    """nice!nano pin behind a hole, for a nano mounted on front or back."""
    if hole == "KA":
        return NANO_LEFT[0]
    if hole == "KB":
        return NANO_LEFT[1]
    col, row = hole[0], int(hole[1:])
    if back:
        col = "R" if col == "L" else "L"
    return (NANO_LEFT if col == "L" else NANO_RIGHT)[row]


def key_pins(back):
    """key reference -> nice!nano pin for one half."""
    return {key: key_pin(hole, back) for hole, key in HOLE_TO_KEY.items()}
