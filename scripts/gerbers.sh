#!/bin/sh
# Export JLCPCB-ready Gerbers and drill files to build/gerbers and zip them.
set -e -o pipefail
cd "$(dirname "$0")/.."
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
PCB=pcb/expensivo.kicad_pcb
OUT=build/gerbers
ZIP=build/expensivo-jlcpcb.zip

# don't send a board with unrouted connections
drc=$($K pcb drc --schematic-parity -o build/drc.rpt $PCB)
grep -q "Found 0 unconnected pads" build/drc.rpt || { echo "DRC: unrouted connections, see build/drc.rpt"; exit 1; }
echo "$drc" | grep -q "Found 0 schematic parity issues" || { echo "DRC: board and schematic differ, see build/drc.rpt"; exit 1; }

rm -rf $OUT $ZIP
mkdir -p $OUT
# JLCPCB's KiCad settings: Protel extensions, no X2/netlist attributes,
# silkscreen clipped by the solder mask openings
$K pcb export gerbers -o $OUT/ --no-x2 --no-netlist --subtract-soldermask \
    -l F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts $PCB >/dev/null
$K pcb export drill -o $OUT/ --format excellon --excellon-units mm --excellon-zeros-format decimal \
    --excellon-oval-format alternate --excellon-separate-th --generate-map --map-format gerberx2 $PCB >/dev/null
(cd $OUT && zip -q ../expensivo-jlcpcb.zip *)
ls $OUT
echo "wrote $ZIP"
