// Optional cover over the nice!nano; holds on with two 6x2 mm magnets,
// glued into the cover and the top case (mind the polarity).
step = 0.04;
$fn = $preview ? 10 : 50;
include <modules.scad>

// Printed upside down, top face on the bed
translate([0,0,hump_top])
rotate([0,180,0])
cover();
