#!/usr/bin/env python3
"""Import the Freerouting session and add GND pours on both layers."""
import os
import pcbnew

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PCB = os.path.join(ROOT, "pcb", "expensivo.kicad_pcb")
SES = os.path.join(ROOT, "build", "expensivo.ses")


def main():
    board = pcbnew.LoadBoard(PCB)
    assert pcbnew.ImportSpecctraSES(board, SES), "SES import failed"

    gnd = board.FindNet("GND")
    outline = pcbnew.SHAPE_POLY_SET()
    assert board.GetBoardPolygonOutlines(outline), "board outline not closed"
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.Outline().Append(outline)
        z.SetLocalClearance(pcbnew.FromMM(0.3))
        z.SetMinThickness(pcbnew.FromMM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        board.Add(z)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("saved", PCB, "tracks:", len(board.GetTracks()))


if __name__ == "__main__":
    main()
