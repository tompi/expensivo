// hotswap socket is ~1.75 high at the highest.
$fn = $preview ? 10 : 96;
include <modules.scad>

// silicone bumpers and magnets, in KiCad coordinates (front view). All clear the board
// edge and pin pockets; magnets also clear the socket pockets. Bumper recesses may
// touch socket pockets (as on the cheapino), the bumper pad covers that.
bumpers = [[164.86, 72.05], [164.61, 118.8], [176.41, 127.8], [138.11, 124.65],
           [102.61, 59.55], [100.61, 94.05], [66.86, 110.5], [66.86, 76.3]];
magnets = [[149.11, 67.55], [150.86, 111.3], [83.36, 65.3], [74.11, 94.3]];

// Rotate so you dont need to do that in extruder
translate([0,0,2.5])
rotate([0,180,0])
difference() {
    bottom();
    switches(false);
    tht_pockets();
    mounting_holes();
    for (b = bumpers) at(b) bumper();
    for (m = magnets) at(m) magnet();
}
