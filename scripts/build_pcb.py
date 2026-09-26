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
import math
import os
import pcbnew

from layout import HOLE_TO_KEY, KEY_ROWS, THUMBS, symbol_uuid

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
LOGO = (162.4, 108.1)           # between the encoder's mounting tabs and its A/B/C pins
LOGO_SIZE = 2.5
BYLINE = (164.6, 115.4)

# --- outline --------------------------------------------------------------
# board around each key centre (left, top, right, bottom); +x is the socket pad side
# just clears the hotswap socket bodies, so the edge hides ~1 mm under the keycaps
KEY_BOX = (-8.1, -8.0, 9.15, 8.0)
KEY_BOX_EXTRA = {}  # per-key (left, top, right, bottom) additions to KEY_BOX
# turned 180 degrees so the socket pads face inwards and the edge can hug the outer side
FLIPPED_KEYS = ("K16",)
BODY_MARGIN = 0.5  # board around part bodies
HOLE_R = 2.5      # board around each mounting hole
PAD_EDGE = 0.3    # minimum pad to board edge distance
FILL_R = 3.0      # gaps narrower than 2x this between keys/parts get filled
ROUND_R = 1.0     # outside corner radius


def load(lib, name):
    fp = pcbnew.FootprintLoad(lib, name)
    assert fp, (lib, name)
    # library nickname as in the global footprint table, so the schematic can name it
    fp.SetFPID(pcbnew.LIB_ID(os.path.basename(lib.rstrip("/")).replace(".pretty", ""), name))
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


def poly(points):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in points:
        s.Append(mm(x), mm(y))
    return s


def trim_outline(board):
    """Replace the cheapino outline with the smallest one covering the keycaps and parts."""
    shapes = pcbnew.SHAPE_POLY_SET()

    def add(s):
        shapes.BooleanAdd(s, pcbnew.SHAPE_POLY_SET.PM_FAST)

    pads = pcbnew.SHAPE_POLY_SET()
    boxes, holes = {}, []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        x, y = pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y)
        if ref.startswith("K"):
            l, t, r, b = (a + e for a, e in zip(KEY_BOX, KEY_BOX_EXTRA.get(ref, (0, 0, 0, 0))))
            s = poly([(x + l, y + t), (x + r, y + t), (x + r, y + b), (x + l, y + b)])
            s.Rotate(fp.GetOrientation(), fp.GetPosition())
            add(s)
        elif ref.startswith("H"):
            holes.append((x, y))
            add(poly([(x + HOLE_R * math.cos(a * math.pi / 16), y + HOLE_R * math.sin(a * math.pi / 16))
                      for a in range(32)]))
        else:
            bb = pcbnew.BOX2I()
            if ref in ("SW1", "SW2", "U1"):
                # the slide switch lever and the nano's USB end stick out past the edge,
                # so only cover their pads
                for p in fp.Pads():
                    bb.Merge(p.GetBoundingBox())
            else:
                # part body from its fab-layer drawing
                fab = pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab
                for g in fp.GraphicalItems():
                    if g.GetLayer() == fab and isinstance(g, pcbnew.PCB_SHAPE):  # not the ref text
                        bb.Merge(g.GetBoundingBox())
            bb.Inflate(mm(BODY_MARGIN))
            boxes[ref] = bb
            if bb.GetWidth():
                add(poly([(pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())),
                          (pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetTop())),
                          (pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())),
                          (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetBottom()))]))
        for p in fp.Pads():
            p.TransformShapeToPolygon(pads, p.GetPrincipalLayer(), mm(PAD_EDGE), mm(0.01))
    # straight right edge from the nano's top corner down to the rightmost mounting hole
    right = max(pcbnew.ToMM(boxes[r].GetRight()) for r in ("U1", "SW1", "SW3"))
    hole_y = max(holes)[1]
    add(poly([(NANO[0], pcbnew.ToMM(boxes["U1"].GetTop())), (right, pcbnew.ToMM(boxes["U1"].GetTop())),
              (right, hole_y), (NANO[0], hole_y)]))

    corner = pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS
    # close the gaps between keys and parts, then round the outside corners
    shapes.Inflate(mm(FILL_R), corner, mm(0.01))
    shapes.Deflate(mm(FILL_R), corner, mm(0.01))
    shapes.Deflate(mm(ROUND_R), corner, mm(0.01))
    shapes.Inflate(mm(ROUND_R), corner, mm(0.01))
    shapes.BooleanAdd(pads, pcbnew.SHAPE_POLY_SET.PM_FAST)
    assert shapes.OutlineCount() == 1, f"outline split into {shapes.OutlineCount()} pieces"

    outline = pcbnew.SHAPE_POLY_SET()
    outline.AddOutline(shapes.Outline(0))  # drop any enclosed holes
    old = [d for d in board.GetDrawings() if d.GetLayerName() == "Edge.Cuts"]
    for d in old:
        board.Remove(d)
    edge = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_POLY)
    edge.SetPolyShape(outline)
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(mm(0.1))
    edge.SetFilled(False)
    board.Add(edge)
    return old  # keep the removed items alive, see main()


def main():
    board = pcbnew.LoadBoard(CHEAPINO)

    # strip copper, zones and old parts
    # removed items are kept referenced: letting SWIG destroy them mid-run
    # corrupts the board's item lists
    removed = [board.GetArea(i) for i in range(board.GetAreaCount())]
    removed += list(board.GetTracks())
    # the logo and byline are solder mask openings showing the copper pour; keep them
    def is_logo(d):
        return isinstance(d, pcbnew.PCB_TEXT) and d.GetLayerName() in ("F.Mask", "B.Mask")
    removed += [d for d in board.GetDrawings() if d.GetLayerName() != "Edge.Cuts" and not is_logo(d)]
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
            if ref in FLIPPED_KEYS:
                fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 180)
            for p in fp.Pads():
                if p.GetNumber() == "1":
                    p.SetNet(net("GND"))
                elif p.GetNumber() == "2":
                    p.SetNet(net(key_net[ref]))
        if ref == "REF**":
            # unique refs are required for the Specctra export
            hole_count += 1
            fp.SetReference(f"H{hole_count}")

    # drop the bottom mounting hole between the thumbs so the outline can hug the keys there
    holes_fp = [fp for fp in board.GetFootprints() if fp.GetReference().startswith("H")]
    bottom = max(holes_fp, key=lambda fp: fp.GetPosition().y)
    board.Remove(bottom)
    removed.append(bottom)

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
        fp = place(board, load(jlib, jname), ref, (x, ROW_Y[row]), back=(side == "B"),
                   value="front" if side == "F" else "back")
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
    # its silkscreen outline would cross the copper logo; the pin layout already fixes the orientation
    for g in list(enc.GraphicalItems()):
        if g.GetLayer() == pcbnew.B_SilkS and isinstance(g, pcbnew.PCB_SHAPE):
            enc.Remove(g)
            removed.append(g)
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
            elif p.GetNumber() == "3":
                # unused throw; named the way KiCad names a no-connect pin's net
                p.SetNet(net(f"unconnected-({ref}-C-Pad3)"))

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

    removed += trim_outline(board)

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

    # logo in the cheapino style: Impact text as bare copper, between the encoder pad rows
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayerName() in ("F.Mask", "B.Mask"):
            if d.GetText().startswith("Cheapino"):
                d.SetText("Expensivo")
                d.SetTextSize(pcbnew.VECTOR2I(mm(LOGO_SIZE), mm(LOGO_SIZE)))
                xy = LOGO
            else:
                xy = BYLINE
            d.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
            d.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
            d.SetPosition(pcbnew.VECTOR2I(mm(xy[0]), mm(xy[1])))
            # keep tracks out from under the exposed copper so the pour shows solid
            bb = d.GetEffectiveTextShape().BBox()
            bb.Inflate(mm(0.5))
            keepout = pcbnew.ZONE(board)
            keepout.SetIsRuleArea(True)
            keepout.SetDoNotAllowTracks(True)
            keepout.SetDoNotAllowVias(True)
            keepout.SetDoNotAllowCopperPour(False)
            keepout.SetDoNotAllowPads(False)
            keepout.SetDoNotAllowFootprints(False)
            keepout.SetLayer(pcbnew.F_Cu if d.GetLayerName() == "F.Mask" else pcbnew.B_Cu)
            keepout.Outline().NewOutline()
            for x, y in ((bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()),
                         (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())):
                keepout.Outline().Append(x, y)
            board.Add(keepout)
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

    # link every footprint to its symbol in expensivo.kicad_sch (scripts/gen_schematic.py)
    for fp in board.GetFootprints():
        fp.SetPath(pcbnew.KIID_PATH("/" + symbol_uuid(fp.GetReference())))
        fp.SetSheetfile("expensivo.kicad_sch")
        fp.SetSheetname("")

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
