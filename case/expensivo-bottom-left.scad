// hotswap socket is ~1.75 high at the highest.
$fn = $preview ? 10 : 96;
include <modules.scad>

// silicone bumpers and magnets, in KiCad coordinates (front view). All clear the board
// edge and pin pockets; magnets also clear the socket pockets. Bumper recesses may
// touch socket pockets (as on the cheapino), the bumper pad covers that.
bumpers = [[164.86, 72.05], [164.61, 118.8], [179.11, 129.3], [140.61, 118.9],
           [104.31, 51.95], [102.36, 86.1], [66.86, 102.5], [66.86, 68.3]];
magnets = [[150.36, 76.55], [150.86, 112.05], [76.61, 66.25], [83.36, 93.5]];

// Rotate so you dont need to do that in extruder
translate([0,0,2.5])
rotate([0,180,0])
mirror([1,0,0])
difference() {
    bottom();
    switches(true);
    tht_pockets();
    mounting_holes();
    for (b = bumpers) at(b) bumper();
    for (m = magnets) at(m) magnet();
}
