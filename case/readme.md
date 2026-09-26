3D-printed case
===============

Adapted from the cheapino case (`../cheapino/case`). Parts:

- `expensivo-top-left.scad`, `expensivo-top-right.scad`: top frames, flat on top
  like the cheapino case and flipped for printing (top face on the bed). The
  nice!nano sits in an open well.
- `expensivo-cover-left.scad`, `expensivo-cover-right.scad`: optional covers over
  the nice!nano (on 4.9 mm sockets), also printed top face down. Under the
  cover everything is open from the pcb to its roof (10 mm), so the battery
  can stick out past the nano's end. Each cover holds on with two 6x2 mm
  magnets glued into matching pockets in cover and top frame (check the
  polarity before the glue sets) and is located by two pegs; magnets and pegs
  share a small solid block at the thumb end.
- `expensivo-assembly.scad`: both halves put together, for looking at (F5)
- `expensivo-bottom-left.scad`, `expensivo-bottom-right.scad`: bottom plates

All board geometry (outline, keys, holes, parts) comes from `expensivo-pcb.scad`,
which `scripts/gen_case.py` generates from the PCB (`scripts/build.sh` runs it),
so the case follows PCB changes. Positions typed in by hand (bumpers, magnets)
are in KiCad coordinates, see `at()` in `modules.scad`.

Compared to the cheapino case: no RJ45 or diode cutouts; both halves get a
nice!nano well, a notch for the USB plug, a slot for the power switch lever and
a hole to press reset (through the cover too). The battery sits under the nice!nano,
between the socket rows, and may stick out about 6 mm past its end. The nano's stack (socket height, parts, USB-C size,
clearances) is set in the "cover over the nice!nano" part of `modules.scad`.
To fit the encoder after all, pass `encoder=true` in `expensivo-top-right.scad`;
the cover's magnets use that spot, so that half then goes without a cover.

Render with a recent OpenSCAD snapshot with the manifold backend enabled, e.g.

    openscad --enable=manifold -o top-left.stl expensivo-top-left.scad
