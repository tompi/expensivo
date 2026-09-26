#!/usr/bin/env python3
"""Write pcb/expensivo.kicad_sch from the PCB's parts and nets.

Run with KiCad's bundled python after build_pcb.py (see build.sh). Every part
on the board gets a symbol; every pin gets a short wire and a net label with
the PCB's net name, so the schematic and the board can't disagree
(build.sh checks that with DRC's schematic parity). Symbol uuids come from
layout.symbol_uuid, which is what the footprints link to.
"""
import os
import re
import uuid

import pcbnew

from layout import NANO_LEFT, NANO_RIGHT, symbol_uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PCB = os.path.join(ROOT, "pcb", "expensivo.kicad_pcb")
OUT = os.path.join(ROOT, "pcb", "expensivo.kicad_sch")
SYMLIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/"
G = 2.54
ROOT_UUID = str(uuid.uuid5(uuid.NAMESPACE_URL, "expensivo:schematic"))


def uid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "expensivo:" + ":".join(map(str, parts))))


# --- symbols ------------------------------------------------------------------
def lib_symbol(lib, name):
    """A symbol from KiCad's library, renamed lib:name for embedding."""
    s = open(os.path.join(SYMLIB, lib + ".kicad_sym")).read()
    i = s.index(f'\t(symbol "{name}"\n') + 1
    depth = 0
    for j in range(i, len(s)):
        depth += {"(": 1, ")": -1}.get(s[j], 0)
        if depth == 0:
            break
    return s[i:j + 1].replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)


def pins_of(text):
    """{number: (x, y, angle)} of a symbol's pins, library coordinates (y up)."""
    return {m[3]: (float(m[0]), float(m[1]), int(m[2])) for m in re.findall(
        r'\(pin \w+ \w+\s+\(at ([-\d.]+) ([-\d.]+) (\d+)\)[\s\S]*?\(number "([^"]*)"', text)}


def nano_symbol():
    """nice!nano on the reversible footprint: pins are the footprint's holes,
    named with the nano pin they carry from the front / from the back."""
    def pin(num, name, x, y, angle):
        return (f'\t\t\t(pin passive line (at {x} {y} {angle}) (length 2.54)\n'
                f'\t\t\t\t(name "{name}" (effects (font (size 1.27 1.27))))\n'
                f'\t\t\t\t(number "{num}" (effects (font (size 1.27 1.27))))\n\t\t\t)\n')
    pins = []
    for i in range(12):
        y = round(13.97 - i * G, 2)
        pins.append(pin(f"L{i}", f"{NANO_LEFT[i]}/{NANO_RIGHT[i]}", -25.4, y, 0))
        pins.append(pin(f"R{i}", f"{NANO_RIGHT[i]}/{NANO_LEFT[i]}", 25.4, y, 180))
    for num, name, x in (("P101", "P1.01", -7.62), ("P102", "P1.02", 0), ("P107", "P1.07", 7.62)):
        pins.append(pin(num, name, x, -19.05, 90))

    def prop(k, v, y, hide=False):
        h = " (hide yes)" if hide else ""
        return f'\t\t(property "{k}" "{v}" (at 0 {y} 0) (effects (font (size 1.27 1.27)){h}))\n'
    return ('\t(symbol "expensivo:nice_nano_reversible" (pin_names (offset 1.016)) '
            '(exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            + prop("Reference", "U", 19.05)
            + prop("Value", "nice!nano v2", 17.78)
            + prop("Footprint", "expensivo:nice_nano_reversible", -24.13, True)
            + prop("Datasheet", "https://nicekeyboards.com/docs/nice-nano/pinout-schematic", -26.67, True)
            + prop("Description", "nice!nano on a reversible footprint; pin names: front / back", -29.21, True)
            + '\t\t(symbol "nice_nano_reversible_0_1"\n'
              '\t\t\t(rectangle (start -22.86 16.51) (end 22.86 -16.51)\n'
              '\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))\n'
              '\t\t)\n'
            + '\t\t(symbol "nice_nano_reversible_1_1"\n' + "".join(pins) + '\t\t)\n\t)\n')


# per part: library symbol, rotation, reference/value text offsets (sch coords)
SYMBOLS = {
    "key": ("Switch", "SW_Push"),
    "spdt": ("Switch", "SW_SPDT"),
    "button": ("Switch", "SW_Push"),
    "battery": ("Device", "Battery_Cell"),
    "encoder": ("Device", "RotaryEncoder_Switch"),
    "jumper": ("Jumper", "SolderJumper_2_Open"),
    "hole": ("Mechanical", "MountingHole"),
}


# --- schematic items ----------------------------------------------------------
class Sheet:
    def __init__(self):
        self.items = []

    def text(self, s, x, y, size=1.27, bold=False):
        b = " (bold yes)" if bold else ""
        self.items.append(f'\t(text "{s}" (exclude_from_sim no) (at {x:.2f} {y:.2f} 0)\n'
                          f'\t\t(effects (font (size {size} {size}){b}) (justify left top))\n'
                          f'\t\t(uuid "{uid("text", s, x, y)}")\n\t)\n')

    def wire(self, a, b):
        self.items.append(f'\t(wire (pts (xy {a[0]:.2f} {a[1]:.2f}) (xy {b[0]:.2f} {b[1]:.2f}))\n'
                          f'\t\t(stroke (width 0) (type default))\n\t\t(uuid "{uid("wire", a, b)}")\n\t)\n')

    def label(self, net, p, angle):
        # global labels: their nets carry the plain names the PCB uses
        just = {0: "left", 90: "left", 180: "right", 270: "right"}[angle]
        self.items.append(f'\t(global_label "{net}" (shape passive) (at {p[0]:.2f} {p[1]:.2f} {angle})\n'
                          f'\t\t(fields_autoplaced yes)\n'
                          f'\t\t(effects (font (size 1.27 1.27)) (justify {just}))\n'
                          f'\t\t(uuid "{uid("label", net, p)}")\n'
                          f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {p[0]:.2f} {p[1]:.2f} 0)\n'
                          f'\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n\t)\n')

    def no_connect(self, p):
        self.items.append(f'\t(no_connect (at {p[0]:.2f} {p[1]:.2f}) (uuid "{uid("nc", p)}"))\n')

    def symbol(self, lib_id, fp, x, y, pins, rot=0, ref_at=(0, -5.08), val_at=(0, 2.54), stub=G):
        """Place a part; pins is the lib symbol's {number: (x, y, angle)}."""
        ref = fp.GetReference()
        props = [("Reference", ref, ref_at, False), ("Value", fp.GetValue(), val_at, False),
                 ("Footprint", fp.GetFPIDAsString(), (0, 0), True),
                 ("Datasheet", "~", (0, 0), True), ("Description", "", (0, 0), True)]
        in_bom = "no" if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM else "yes"
        out = [f'\t(symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} {rot}) (unit 1)\n'
               f'\t\t(exclude_from_sim no) (in_bom {in_bom}) (on_board yes) (dnp no)\n'
               f'\t\t(uuid "{symbol_uuid(ref)}")\n']
        for k, v, (dx, dy), hide in props:
            h = " (hide yes)" if hide else ""
            out.append(f'\t\t(property "{k}" "{v}" (at {x + dx:.2f} {y + dy:.2f} 0)\n'
                       f'\t\t\t(effects (font (size 1.27 1.27)){h})\n\t\t)\n')
        for n in pins:
            out.append(f'\t\t(pin "{n}" (uuid "{uid("pin", ref, n)}"))\n')
        out.append(f'\t\t(instances (project "expensivo" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))\n\t)\n')
        self.items.append("".join(out))

        # a stub and a net label on every pin, or a no-connect flag
        nets = {}
        for p in fp.Pads():
            if p.GetNumber():
                nets.setdefault(p.GetNumber(), p.GetNetname())
        for n, (px, py, pa) in pins.items():
            # library y is up; rotate by the symbol's rotation (counter-clockwise)
            a = (pa + rot) % 360
            c, s = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[rot]
            end = (x + px * c - py * s, y - (px * s + py * c))
            net = nets.get(n, "")
            if not net or net.startswith("unconnected-"):
                self.no_connect(end)
                continue
            # the pin points from its end into the body; the stub goes the other way
            out_dir = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[a]
            tip = (end[0] + out_dir[0] * stub, end[1] + out_dir[1] * stub)
            self.wire(end, tip)
            self.label(net, tip, {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[out_dir])


def on_grid(v):
    return round(v / G) * G


def main():
    board = pcbnew.LoadBoard(PCB)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    libs = {k: lib_symbol(*v) for k, v in SYMBOLS.items()}
    lib_pins = {k: pins_of(v) for k, v in libs.items()}
    nano = nano_symbol()
    sh = Sheet()

    sh.text("Expensivo: wireless split keyboard, one half (both halves use this PCB)", 20.32, 15.24, 2.54, True)
    sh.text("Every key has its own nice!nano pin and switches to GND: no diodes, no matrix.\\n"
            "The PCB is reversible: the left half is built on the front, the right half on the back.\\n"
            "Generated by scripts/gen_schematic.py from the PCB's parts and nets; edit the generators, not this file.",
            20.32, 21.59)

    # keys, laid out like the keyboard
    from layout import KEY_ROWS, THUMBS
    sh.text("Keys (Kailh MX hotswap sockets)", 20.32, 38.1, 1.778, True)
    x0, y0, dx, dy = on_grid(30), on_grid(50), 33.02, 17.78
    for r, row in enumerate(KEY_ROWS):
        for c, ref in enumerate(row):
            sh.symbol("Switch:SW_Push", fps[ref], x0 + c * dx, y0 + r * dy, lib_pins["key"])
    for i, ref in enumerate(THUMBS):
        sh.symbol("Switch:SW_Push", fps[ref], x0 + (i + 2) * dx, y0 + 3.5 * dy, lib_pins["key"])

    # controller
    ux, uy = on_grid(245), on_grid(100)
    sh.text("Controller", ux - 25.4, uy - 35.56, 1.778, True)
    sh.text("Pin names: nano pin with the nano on the front / on the back.\\n"
            "L2/R2 are GND and RST either way round, so the reset button\\n"
            "sits across them. Middle pins P1.01/02/07 go to the encoder.",
            ux - 25.4, uy + 38.1)
    sh.symbol("expensivo:nice_nano_reversible", fps["U1"], ux, uy, pins_of(nano),
              ref_at=(0, -20.32), val_at=(0, -17.78), stub=2 * G)

    # power, reset, encoder
    px = on_grid(320)
    sh.text("Power", px - 7.62, 38.1, 1.778, True)
    sh.symbol("Device:Battery_Cell", fps["BT1"], px, 55.88, lib_pins["battery"],
              ref_at=(2.54, -2.54), val_at=(2.54, 0))
    sh.text("SW1 on the front (left half), SW2 on the back (right half):\\nsolder only the one on top.",
            px + 15.24, 45.72)
    sh.symbol("Switch:SW_SPDT", fps["SW1"], px + 22.86, 60.96, lib_pins["spdt"], val_at=(0, 5.08))
    sh.symbol("Switch:SW_SPDT", fps["SW2"], px + 22.86, 78.74, lib_pins["spdt"], val_at=(0, 5.08))

    sh.text("Reset (SW3 front, SW4 back)", px - 7.62, 91.44, 1.778, True)
    sh.symbol("Switch:SW_Push", fps["SW3"], px, 104.14, lib_pins["button"])
    sh.symbol("Switch:SW_Push", fps["SW4"], px + 33.02, 104.14, lib_pins["button"])

    sh.text("Encoder (optional, right half)", px - 7.62, 116.84, 1.778, True)
    sh.symbol("Device:RotaryEncoder_Switch", fps["ENC1"], px + 5.08, 132.08, lib_pins["encoder"],
              ref_at=(0, -7.62), val_at=(0, 7.62))

    # power-row jumpers
    jy = on_grid(160)
    sh.text("Power-row jumpers: bridge the ones on the side the nano is on", px - 7.62, jy - 12.7, 1.778, True)
    sh.text("They route nano holes L0/R0/L1/R1/L3/R3 to keys, B+ or GND to suit the side.", px - 7.62, jy - 7.62)
    for i, ref in enumerate(["JP1", "JP2", "JP3", "JP4", "JP5", "JP6", "JP7", "JP8"]):
        sh.symbol("Jumper:SolderJumper_2_Open", fps[ref], px + (i // 4) * 45.72, jy + (i % 4) * 12.7,
                  lib_pins["jumper"], ref_at=(0, -3.81), val_at=(0, 3.81))

    # mounting holes
    holes = sorted((r for r in fps if r.startswith("H")), key=lambda r: int(r[1:]))
    sh.text("Mounting holes", 20.32, 213.36, 1.778, True)
    for i, ref in enumerate(holes):
        sh.symbol("Mechanical:MountingHole", fps[ref], 35.56 + i * 30.48, 228.6, {},
                  ref_at=(0, -5.08), val_at=(0, 5.08))

    embedded = "".join(libs[k] + "\n" for k in dict.fromkeys(["key", "spdt", "battery", "encoder", "jumper", "hole"]))
    with open(OUT, "w") as f:
        f.write(f'(kicad_sch (version 20231120) (generator "expensivo") (generator_version "8.0")\n'
                f'\t(uuid "{ROOT_UUID}")\n\t(paper "A3")\n'
                f'\t(title_block (title "Expensivo") (rev "1") '
                f'(comment 1 "Generated by scripts/gen_schematic.py from the PCB"))\n'
                f'\t(lib_symbols\n{embedded}{nano}\t)\n')
        f.write("".join(sh.items))
        f.write('\t(sheet_instances (path "/" (page "1")))\n)\n')
    print("wrote", os.path.relpath(OUT, ROOT))

    # the nano symbol also goes in the project's symbol library
    with open(os.path.join(ROOT, "lib", "expensivo.kicad_sym"), "w") as f:
        f.write('(kicad_symbol_lib (version 20231120) (generator "expensivo") (generator_version "8.0")\n'
                + nano.replace('(symbol "expensivo:nice_nano_reversible"', '(symbol "nice_nano_reversible"', 1)
                + ')\n')
    with open(os.path.join(ROOT, "pcb", "sym-lib-table"), "w") as f:
        f.write('(sym_lib_table\n  (version 7)\n'
                '  (lib (name "expensivo")(type "KiCad")(uri "${KIPRJMOD}/../lib/expensivo.kicad_sym")'
                '(options "")(descr "expensivo symbols"))\n)\n')


if __name__ == "__main__":
    main()
