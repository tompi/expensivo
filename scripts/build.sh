#!/bin/sh
# Regenerate, autoroute and check the expensivo PCB.
set -e
cd "$(dirname "$0")/.."
KICAD=/Applications/KiCad/KiCad.app/Contents
PY=$KICAD/Frameworks/Python.framework/Versions/3.9/bin/python3
FR=build/freerouting-1.5.0.jar
mkdir -p build
[ -f $FR ] || curl -sfL -o $FR https://github.com/freerouting/freerouting/releases/download/v1.5.0/freerouting-1.5.0.jar
python3 scripts/gen_nano_footprint.py
$PY scripts/build_pcb.py 2>&1 | grep -v -E "swig/python|assert \"\"traits"
(cd build && java -jar freerouting-1.5.0.jar -de expensivo.dsn -do expensivo.ses -mp 30 2>&1 | grep -E "completed|ERROR" | grep -v rules)
$PY scripts/finish_pcb.py 2>&1 | grep -v -E "swig/python|assert \"\"traits"
$KICAD/MacOS/kicad-cli pcb drc -o build/drc.rpt pcb/expensivo.kicad_pcb | tail -2
