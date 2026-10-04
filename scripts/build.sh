#!/bin/sh
# Regenerate, autoroute and check the expensivo PCB.
set -e -o pipefail
cd "$(dirname "$0")/.."
KICAD=/Applications/KiCad/KiCad.app/Contents
PY=$KICAD/Frameworks/Python.framework/Versions/3.9/bin/python3
FR=build/freerouting-1.5.0.jar
mkdir -p build
[ -f $FR ] || curl -sfL -o $FR https://github.com/freerouting/freerouting/releases/download/v1.5.0/freerouting-1.5.0.jar
# nice!nano 3D model: CC BY-NC-SA, so fetched rather than kept in the repo
mkdir -p build/3d
[ -f build/3d/Nice_Nano_V2.step ] || curl -sfL -o build/3d/Nice_Nano_V2.step \
    https://raw.githubusercontent.com/infused-kim/kb_ergogen_fp/main/3d_models/Nice_Nano_V2.step
python3 scripts/gen_nano_footprint.py
$PY scripts/build_pcb.py 2>&1 | grep -v -E "swig/python|assert \"\"traits"
(cd build && java -jar freerouting-1.5.0.jar -de expensivo.dsn -do expensivo.ses -mp 30 2>&1 | grep -E "completed|ERROR" | grep -v rules)
$PY scripts/finish_pcb.py 2>&1 | grep -v -E "swig/python|assert \"\"traits"
$PY scripts/gen_schematic.py 2>&1 | grep -v -E "swig/python|traits"
$KICAD/MacOS/kicad-cli sch erc -o build/erc.rpt pcb/expensivo.kicad_sch | tail -1
$KICAD/MacOS/kicad-cli pcb drc --schematic-parity -o build/drc.rpt pcb/expensivo.kicad_pcb | tail -2
$PY scripts/gen_case.py 2>&1 | grep -v -E "swig/python|traits"
