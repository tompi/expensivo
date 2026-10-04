step = 0.04;
$fn = $preview ? 10 : 96;
include <modules.scad>

// Rotate so you dont need to do that in extruder
translate([0,0,case_top])
rotate([0,180,0])
difference() {
    case();
    top_cutouts(encoder=false);
}
