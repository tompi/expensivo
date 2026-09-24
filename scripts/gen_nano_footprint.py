#!/usr/bin/env python3
"""Generate the reversible nice!nano footprint used by expensivo.

Pads are named by physical position, not by MCU pin, because the MCU pin
behind each hole depends on which side the nice!nano is mounted:

  L0..L11  left hole column  (x = -7.62), top (USB end) to bottom
  R0..R11  right hole column (x = +7.62)
  P101, P102, P107  nice!nano extra pins, placed where they land when the
           nano is mounted on the BACK side (right half only)

Front (left half): nano sits on F, components facing away from the PCB.
Back (right half): nano sits on B, components facing away from the PCB.
"""
import os

# Pro Micro / nice!nano pinout, top view, USB up, components facing viewer
LEFT = ["P0.06", "P0.08", "GND", "GND", "P0.17", "P0.20",
        "P0.22", "P0.24", "P1.00", "P0.11", "P1.04", "P1.06"]
RIGHT = ["B+", "GND", "RST", "3V3", "P0.31", "P0.29",
         "P0.02", "P1.15", "P1.13", "P1.11", "P0.10", "P0.09"]

PITCH = 2.54
X = 7.62
Y0 = -12.7
EXTRA = [("P101", 5.08), ("P102", 2.54), ("P107", 0.0)]
EXTRA_Y = Y0 + 9 * PITCH  # 10.16


def pad(name, x, y, square=False):
    shape = "rect" if square else "circle"
    return (f'\t(pad "{name}" thru_hole {shape} (at {x:.3f} {y:.3f}) (size 1.7 1.7) '
            f'(drill 1) (layers "*.Cu" "*.Mask"))\n')


def text(s, x, y, layer, size=0.7):
    mirror = " (justify mirror)" if layer.startswith("B.") else ""
    return (f'\t(fp_text user "{s}" (at {x:.3f} {y:.3f}) (layer "{layer}")\n'
            f'\t\t(effects (font (size {size} {size}) (thickness 0.12)){mirror})\n\t)\n')


def line(x1, y1, x2, y2, layer, w=0.12):
    return (f'\t(fp_line (start {x1} {y1}) (end {x2} {y2}) '
            f'(stroke (width {w}) (type solid)) (layer "{layer}"))\n')


def rect(x1, y1, x2, y2, layer, w=0.12):
    return (line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) +
            line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w))


def main():
    out = []
    out.append('(footprint "nice_nano_reversible"\n\t(version 20240108)\n\t(generator "expensivo")\n'
               '\t(layer "F.Cu")\n'
               '\t(descr "Reversible nice!nano v2, jumper-selected power rows, extra pins P1.01/P1.02/P1.07 for back mount")\n'
               '\t(property "Reference" "U1" (at 0 -19.5 0) (layer "F.SilkS") (hide yes)\n'
               '\t\t(effects (font (size 1 1) (thickness 0.15))))\n'
               '\t(property "Value" "nice!nano" (at 0 18.5 0) (layer "F.Fab")\n'
               '\t\t(effects (font (size 1 1) (thickness 0.15))))\n'
               '\t(attr through_hole)\n')
    for i in range(12):
        y = Y0 + i * PITCH
        out.append(pad(f"L{i}", -X, y, square=(i == 0)))
        out.append(pad(f"R{i}", X, y))
    for name, x in EXTRA:
        out.append(pad(name, x, EXTRA_Y))

    # Pin labels for the firmware-reversible rows (4..11); rows 0..3 are
    # labelled by the jumpers next to them.
    for i in range(4, 12):
        y = Y0 + i * PITCH
        # Front view: left column is the nano's left column
        out.append(text(LEFT[i], -4.9, y, "F.SilkS", 0.6))
        if i != 9:
            out.append(text(RIGHT[i], 4.9, y, "F.SilkS", 0.6))
        # Back view: nano mirrored, so the left hole holds the nano's right pin
        out.append(text(RIGHT[i], -4.9, y, "B.SilkS", 0.6))
        if i != 9:
            out.append(text(LEFT[i], 4.9, y, "B.SilkS", 0.6))
    out.append(text("1.01 1.02 1.07", 2.54, EXTRA_Y + 1.6, "B.SilkS", 0.5))

    for layer in ("F.SilkS", "B.SilkS"):
        out.append(rect(-8.95, -16.51, 8.95, 16.57, layer))
    for layer in ("F.Fab", "B.Fab"):
        out.append(rect(-8.89, -16.51, 8.89, 16.57, layer, 0.1))
    out.append(rect(-3.81, -18.03, 3.81, -16.51, "Dwgs.User", 0.15))
    out.append(text("USB", 0, -17.3, "Dwgs.User", 0.8))
    out.append(')\n')

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "lib", "expensivo.pretty", "nice_nano_reversible.kicad_mod")
    with open(path, "w") as f:
        f.write("".join(out))
    print("wrote", os.path.normpath(path))


if __name__ == "__main__":
    main()
