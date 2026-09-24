#!/usr/bin/env python3
"""Build the (unrouted) expensivo PCB from the cheapino outline.

Run with KiCad's bundled python:
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 scripts/build_pcb.py

Keeps from cheapino: board outline, switch footprints, mounting holes.
Removes: diodes, RJ45s, duplex jumpers, RP2040-Zero, all copper.
Adds: reversible nice!nano, battery pads, power switch, reset button,
optional EC11 encoder (right half), power-row jumpers.

The PCB is drawn as the LEFT half seen from the front (F). The right half
is the same PCB flipped, so everything for the right half lives on B.
"""
import json
import os
import pcbnew

from layout import HOLE_TO_KEY, KEY_ROWS, THUMBS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
CHEAPINO = os.path.normpath(os.path.join(ROOT, "..", "cheapino", "pcb", "cheapino.kicad_pcb"))
OUT = os.path.join(ROOT, "pcb", "expensivo.kicad_pcb")
LIB = os.path.join(ROOT, "lib", "expensivo.pretty")
KLIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/"

mm = pcbnew.FromMM

# --- placement ------------------------------------------------------------
NANO = (165.4, 74.3)            # footprint centre, USB towards the top edge
ROW_Y = [NANO[1] - 12.7 + 2.54 * i for i in range(12)]
XL, XR = NANO[0] - 7.62, NANO[0] + 7.62
JP_XL, JP_XR = XL + 3.0, XR - 3.0
ENC = (162.0, 104.0)            # encoder shaft, back side
PWR = (173.3, 95.5)             # side-actuated slide switch at the right edge
RST = (172.3, 106.0)            # reset button
BAT = [(158.8, 93.0), (156.26, 93.0)]  # battery + / -


def load(lib, name):
    fp = pcbnew.FootprintLoad(lib, name)
    assert fp, (lib, name)
    return fp


def place(board, fp, ref, xy, rot=0.0, back=False, value=None):
    fp.SetReference(ref)
    if value:
        fp.SetValue(value)
    board.Add(fp)
    pos = pcbnew.VECTOR2I(mm(xy[0]), mm(xy[1]))
    fp.SetPosition(pos)
    if back:
        fp.Flip(pos, True)
    fp.SetOrientationDegrees(rot)
    fp.Reference().SetVisible(False)  # no room; silkscreen labels are added separately
    return fp


def pad_xy(p):
    q = p.GetPosition()
    return (pcbnew.ToMM(q.x), pcbnew.ToMM(q.y))


def main():
    board = pcbnew.LoadBoard(CHEAPINO)

    # strip copper, zones and old parts
    # removed items are kept referenced: letting SWIG destroy them mid-run
    # corrupts the board's item lists
    removed = [board.GetArea(i) for i in range(board.GetAreaCount())]
    removed += list(board.GetTracks())
    removed += [d for d in board.GetDrawings() if d.GetLayerName() != "Edge.Cuts"]
    keep = ("Kailh_socket_MX_optional_reversible", "MountingHole")
    removed += [fp for fp in board.GetFootprints() if not any(k in fp.GetFPIDAsString() for k in keep)]
    for item in removed:
        board.Remove(item)

    nets = {}

    def net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    # drop every old net by clearing pads, then re-add our own
    for fp in board.GetFootprints():
        for p in fp.Pads():
            p.SetNetCode(0)

    key_net = {k: f"KEY_{k}" for k in HOLE_TO_KEY.values()}

    # switches: pad 1 -> GND, pad 2 -> key net
    hole_count = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith("K"):
            fp.SetValue("MX")
            fp.SetFPID(pcbnew.LIB_ID("expensivo", "Kailh_socket_MX_optional_reversible"))
            fp.SetAttributes(pcbnew.FP_THROUGH_HOLE)
            for p in fp.Pads():
                if p.GetNumber() == "1":
                    p.SetNet(net("GND"))
                elif p.GetNumber() == "2":
                    p.SetNet(net(key_net[ref]))
        if ref == "REF**":
            # unique refs are required for the Specctra export
            hole_count += 1
            fp.SetReference(f"H{hole_count}")

    # nice!nano
    nano = place(board, load(LIB, "nice_nano_reversible"), "U1", NANO, value="nice!nano v2")
    nano.SetFPID(pcbnew.LIB_ID("expensivo", "nice_nano_reversible"))
    holes = {}
    for i in range(12):
        holes[f"L{i}"] = f"NANO_L{i}" if i < 4 else key_net.get(HOLE_TO_KEY.get(f"L{i}"))
        holes[f"R{i}"] = f"NANO_R{i}" if i < 4 else key_net.get(HOLE_TO_KEY.get(f"R{i}"))
    holes["L2"], holes["R2"] = "RST_A", "RST_B"
    holes["P101"], holes["P102"], holes["P107"] = "ENC_A", "ENC_S", "ENC_B"
    for p in nano.Pads():
        p.SetNet(net(holes[p.GetNumber()]))

    # power-row jumpers: bridge the ones on the same side as the nano
    jlib, jname = KLIB + "Jumper.pretty", "SolderJumper-2_P1.3mm_Open_TrianglePad1.0x1.5mm"
    jumpers = [
        # ref, side, hole, x, row, other net
        ("JP1", "F", "L0", JP_XL, 0, key_net[HOLE_TO_KEY["KA"]]),
        ("JP2", "F", "R0", JP_XR, 0, "RAW"),
        ("JP3", "F", "L1", JP_XL, 1, key_net[HOLE_TO_KEY["KB"]]),
        ("JP4", "F", "L3", JP_XL, 3, "GND"),
        ("JP5", "B", "R0", JP_XR, 0, key_net[HOLE_TO_KEY["KA"]]),
        ("JP6", "B", "L0", JP_XL, 0, "RAW"),
        ("JP7", "B", "R1", JP_XR, 1, key_net[HOLE_TO_KEY["KB"]]),
        ("JP8", "B", "R3", JP_XR, 3, "GND"),
    ]
    for ref, side, hole, x, row, other in jumpers:
        fp = place(board, load(jlib, jname), ref, (x, ROW_Y[row]), back=(side == "B"))
        hx = XL if hole.startswith("L") else XR
        # pad nearest the hole gets the hole net; rotate so that pad faces the hole
        pads = sorted(fp.Pads(), key=lambda p: abs(pad_xy(p)[0] - hx))
        if pads[0].GetNumber() != "1":
            fp.SetOrientationDegrees(180)
            pads = sorted(fp.Pads(), key=lambda p: abs(pad_xy(p)[0] - hx))
        pads[0].SetNet(net(holes[hole]))
        pads[1].SetNet(net(other))

    # encoder, right half only (back side)
    enc = place(board, load(KLIB + "Rotary_Encoder.pretty", "RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm"),
                "ENC1", (0, 0), back=True, value="EC11 (optional)")
    enc.SetOrientationDegrees(90)
    # move so the shaft (pad-centroid of the MP tabs) sits at ENC
    mps = [pad_xy(p) for p in enc.Pads() if p.GetNumber() == "MP"]
    cx, cy = sum(p[0] for p in mps) / 2, sum(p[1] for p in mps) / 2
    enc.Move(pcbnew.VECTOR2I(mm(ENC[0] - cx), mm(ENC[1] - cy)))
    enc_nets = {"A": "ENC_A", "B": "ENC_B", "C": "GND", "S1": "ENC_S", "S2": "GND"}
    for p in enc.Pads():
        if p.GetNumber() in enc_nets:
            p.SetNet(net(enc_nets[p.GetNumber()]))

    # power switch on both sides, only one gets soldered
    for ref, back in (("SW1", False), ("SW2", True)):
        # actuator must point out of the right edge on both sides
        fp = place(board, load(KLIB + "Button_Switch_SMD.pretty", "SW_SPDT_PCM12"), ref, PWR,
                   rot=-90 if back else 90, back=back, value="PCM12SMTR")
        for p in fp.Pads():
            if p.GetNumber() == "1":
                p.SetNet(net("BAT_P"))
            elif p.GetNumber() == "2":
                p.SetNet(net("RAW"))

    # reset button on both sides
    for ref, back in (("SW3", False), ("SW4", True)):
        fp = place(board, load(KLIB + "Button_Switch_SMD.pretty", "SW_SPST_TL3342"), ref, RST,
                   rot=90, back=back, value="RESET")
        for p in fp.Pads():
            p.SetNet(net("RST_A" if p.GetNumber() == "1" else "RST_B"))

    # battery pads (THT, usable from either side)
    batlib = KLIB + "Connector_PinHeader_2.54mm.pretty"
    bat = place(board, load(batlib, "PinHeader_1x02_P2.54mm_Vertical"), "BT1", BAT[0], rot=-90,
                value="Battery")
    for p in bat.Pads():
        p.SetNet(net("BAT_P" if p.GetNumber() == "1" else "GND"))

    # silkscreen
    def text(s, xy, layer, size=1.0, rot=0):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(s)
        t.SetPosition(pcbnew.VECTOR2I(mm(xy[0]), mm(xy[1])))
        t.SetLayer(board.GetLayerID(layer))
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(size * 0.15))
        t.SetTextAngleDegrees(rot)
        if layer.startswith("B."):
            t.SetMirrored(True)
        board.Add(t)

    text("Expensivo", (137.2, 110.3), "F.SilkS", 1.2)
    text("by Tompi", (164.6, 115.8), "F.SilkS", 1.0)
    text("Expensivo", (137.2, 110.3), "B.SilkS", 1.2)
    text("LEFT", (NANO[0], 76.6), "F.SilkS", 0.8)
    text("JP side", (NANO[0], 78.0), "F.SilkS", 0.8)
    text("RIGHT", (NANO[0], 76.6), "B.SilkS", 0.8)
    text("JP side", (NANO[0], 78.0), "B.SilkS", 0.8)
    # - is left of + seen from the front, so the order flips on the back
    bat_label = ((BAT[0][0] + BAT[1][0]) / 2, BAT[0][1] + 1.9)
    text("-  +", bat_label, "F.SilkS", 0.8)
    text("+  -", bat_label, "B.SilkS", 0.8)
    for side in ("F.SilkS", "B.SilkS"):
        text("RST", (RST[0], RST[1] + 5.2), side, 0.8)
        text("PWR", (PWR[0] - 3.2, PWR[1]), side, 0.8, rot=90)

    # design rules
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.2)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.2)
    ds.m_MinResolvedSpokes = 1
    ds.m_MinSilkTextHeight = mm(0.5)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(mm(0.2))
    nc.SetTrackWidth(mm(0.25))
    nc.SetViaDiameter(mm(0.6))
    nc.SetViaDrill(mm(0.3))

    board.BuildListOfNets()
    board.SetFileName(OUT)
    pcbnew.SaveBoard(OUT, board)
    assert pcbnew.ExportSpecctraDSN(board, os.path.join(ROOT, "build", "expensivo.dsn")), "DSN export failed"

    # dump the pin mapping for the firmware generator
    mapping = {"holes": holes, "key_rows": KEY_ROWS, "thumbs": THUMBS, "hole_to_key": HOLE_TO_KEY}
    with open(os.path.join(ROOT, "build", "mapping.json"), "w") as f:
        json.dump(mapping, f, indent=2)

    for fp in board.GetFootprints():
        if fp.GetReference()[0] in "UJSEB":
            bb = fp.GetBoundingBox(False, False)
            print(fp.GetReference(), "B" if fp.IsFlipped() else "F",
                  [round(pcbnew.ToMM(v), 2) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())],
                  [(p.GetNumber(), p.GetNetname(), tuple(round(c, 2) for c in pad_xy(p))) for p in fp.Pads() if p.GetNumber()][:8])
    print("saved", OUT)


if __name__ == "__main__":
    main()
