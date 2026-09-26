// Shared case geometry, adapted from the cheapino case.
// All board positions come from expensivo-pcb.scad (generated from the PCB by
// scripts/gen_case.py), in front-view case coordinates.
include <expensivo-pcb.scad>

pcb_thickness = 1.6;
bottom_plate_thickness = 2.5;
top_of_pcb = bottom_plate_thickness + pcb_thickness;

// Place children at a KiCad coordinate (mm, y down) instead of case coordinates.
module at(p) {
    translate([p[0] - pcb_center[0], pcb_center[1] - p[1], 0]) children();
}

module box(b, h, margin = 0) {
    translate([b[0] - margin, b[1] - margin, 0])
        cube([b[2] - b[0] + 2 * margin, b[3] - b[1] + 2 * margin, h]);
}

module base() {
    polygon(outline);
}

// bottom plate
module bottom() {
    color("pink")
    linear_extrude(bottom_plate_thickness)
        base();
}

module hotswap_mx() {
    thickness=1.85;

    // Holes
    translate([3.175,2.2,0])
    linear_extrude(height=3.05)
        circle(d=3);

    translate([-3.175,-0.36,0])
    linear_extrude(height=3.05)
        circle(d=3);

    // Body
    linear_extrude(height=thickness)
    square([11.8,5.2], center=true);

    translate([0,2,0])
    linear_extrude(height=thickness)
    square([5.65, 2.39]);

    translate([-5.9,-3,0])
    linear_extrude(height=thickness)
    square([5.65, 2.39]);

    // Metal soldering parts
    translate([5.45,1.04,0])
    linear_extrude(height=thickness)
    square([2.5, 2.55]);

    translate([-7.95,-1.7,0])
    linear_extrude(height=thickness)
    square([2.5, 2.55]);
}

// Pockets under one key; the origin is 0.57 right of and 4.7 above the switch centre.
module switch(bottom) {
  // hotswap socket
  color("#ff7f0e")
  translate([0,bottom ? -9.42 : 0,1.85])
  rotate([180,0,0])
  mirror([0,bottom ? 1 : 0,0])
    hotswap_mx();

  // main pin of switch
  // 4mm d, 2.8mm high, 1.6mm pcb
  // means 1.2 of it sticks below, 1.3 for margin
  color("#2ca02c")
  translate([-0.57, -4.7, 0])
  linear_extrude(height=1)
  circle(d=4.2);

  // The two switch alignment pins
  // They will need to be snipped if too long
  color("#d62728")
  translate([-5.74, -4.7, 0])
  linear_extrude(height=1)
  circle(d=1.8);

  color("#d62728")
  translate([4.45, -4.7, 0])
  linear_extrude(height=1)
  circle(d=1.8);
}

// bottom: true for the left half, whose sockets sit on the back of the pcb
module switches(bottom) {
    for (k = keys)
        translate([k[0], k[1], 0]) rotate(k[2]) translate([0.57, 4.7, 0])
            switch(bottom);
}

// pins of the nano, encoder, power switch and battery wires poking through
module tht_pockets() {
    color("#7f7f7f")
    for (p = tht_pads)
        box(p, 1.5, 0.4);
}

module mounting_hole() {
    color("#bcbd22") {
      cylinder(h=1.5, r1=1, r2=2.2);

      translate([0,0,1.5])
      cylinder(h=4, r=2.2);
    }
}

module mounting_holes() {
    for (h = mounting_holes)
        translate([h[0], h[1], 0]) mounting_hole();
}

module bumper() {
    color("#17becf")
    translate([0, 0, 2.5])
      cylinder(h=2, r=5);
    color("#17becf")
    translate([0, 0, 1.3])
      cylinder(h=1.2, r1=4.5, r2=5);
}

module magnet() {
    color("#9467bd")
    cylinder(h=2.1, r=3.05);
}

// Height of case is:
//  5.0mm from pcb to switch inset
//  1.6mm pcb height
//  2.5mm bottom plate
//
//  for a total of 9.1mm. The optional cover over the nice!nano sits on top of
//  that and rises to hump_top.
case_top = 9.1;

// Edge profile of a wall whose last 1mm layer starts at t: bulges out to
// edge_bulge mid-height, rounded into the bottom and the top by a quarter circle.
// Layer i spans i..i+1, so the top rounding is evaluated at the layer's top.
edge_bulge = 2.5;
edge_radius = 2.5;
function quarter_round(d) = edge_bulge - edge_radius
    + sqrt(max(0, pow(edge_radius, 2) - pow(max(0, edge_radius - d), 2)));
function wall_profile(i, t) = min(quarter_round(i), quarter_round(t + 1 - (i + 1)));

// Board outline plus the nano's USB end, which overhangs the board edge.
module shell_outline() {
    base();
    translate([nano[0] - fit, nano[1]]) square([nano[2] - nano[0] + 2 * fit, nano[3] - nano[1] + fit]);
}

module case() {
    color("red")
    for (i = [0:step:case_top - 1])
        translate([0,0,i]) linear_extrude(height=1)
            offset(delta = wall_profile(i, case_top - 1) + 1) shell_outline();
}

// The cover over the nice!nano, sitting on the case top. Its outer walls are
// rounded top and bottom like the case, so a groove marks the joint.
module cover_shell() {
    color("red")
    for (i = [case_top:step:hump_top - 1])
        translate([0,0,i]) linear_extrude(height=1)
            intersection() {
                hump_outer(i - case_top, hump_top - 1 - case_top);
                hump_slice(i + 1);
            }
}

module switch_holes() {
    for (k = keys)
        translate([k[0], k[1], 0]) rotate(k[2]) translate([-18.64, -30.45, 0])
            switch_hole();
}

module switch_hole() {
  translate([11.64, 23.45, 0]){
    color("green") {
        linear_extrude(10) {
          square(14);
          translate([0.2,0.2,0]) circle(d=1);
          translate([13.8,0.2,0]) circle(d=1);
          translate([13.8,13.8,0]) circle(d=1);
          translate([0.2,13.8,0]) circle(d=1);
        }
      }
      linear_extrude(3.5) {
          translate([4.5, -1, 0])
          color("yellow") square([5, 1]);
          translate([4.5, 14, 0])
          color("yellow") square([5, 1]);
      }
    }
  }

module mounting_hole_inserts() {
    color("#bcbd22")
    for (h = mounting_holes)
        translate([h[0], h[1], top_of_pcb]) cylinder(h=4, r=1.4);
}

// --- cover over the nice!nano ------------------------------------------------
socket_height = 4.9;     // pcb top to the nano's underside
nano_thickness = 1.6;
nano_parts = 1.3;        // parts and trimmed pins on top of the nano
usb_height = 3.3;        // USB-C receptacle, above the nano's top face
usb_width = 9.0;
usb_depth = 7.5;         // from the nano's USB edge inwards
plug_width = 13;         // USB-C plug body, with clearance
plug_height = 7;
fit = 0.3;               // clearance around the nano
roof = 1.2;
keycap = 18.2;
keycap_clearance = 0.5;
hump_wall = 1.5;         // side wall between the nano and the keys next to it
hump_round = edge_radius;  // radius of the raised section's top edges, as on the case edge

nano_top = top_of_pcb + socket_height + nano_thickness;
usb_top = nano_top + usb_height + fit;
hump_top = usb_top + roof;
nano_x = (nano[0] + nano[2]) / 2;

// The cover runs from above the thumb keys to the nano's USB end.
hump_bottom = encoder_pads[1] - 0.2;

// Under the cover everything is open, from the pcb up to the roof, so the
// battery can stick out past the nano. Only a solid block at the thumb end,
// left of the reset button, holds the magnets (6x2 mm discs) and locating pegs,
// in two rows of a magnet and a peg each.
cover_wall = 1.2;
magnet_d = 6.2;
magnet_depth = 2.2;
peg_d = 3;
peg_h = 2;
peg_hole_d = 3.4;
block_x0 = nano[0] - fit - hump_wall + cover_wall;
block_x1 = reset_button[0] - 0.8;
row1_y = hump_bottom + cover_wall + 0.2 + magnet_d / 2;
row2_y = row1_y + 7;
block_y1 = row2_y + magnet_d / 2 + 0.8;
cover_magnets = [[block_x0 + 0.7 + magnet_d / 2, row1_y], [block_x1 - 0.7 - magnet_d / 2, row2_y]];
cover_pegs = [[block_x1 - 0.8 - peg_hole_d / 2, row1_y], [block_x0 + 0.8 + peg_hole_d / 2, row2_y]];

// Outer sides of the cover (the board's right edge and the nano's USB end),
// layer i of a wall whose last layer starts at t.
module hump_outer(i, t) {
    offset(r = wall_profile(i, t) + 1)
        translate([-500, -500]) square([mcu_edge_x + 500, nano[3] + fit + 500]);
}

// Inner sides: next to the keys, clear of every keycap, corners rounded.
module hump_area() {
    offset(r=hump_round) offset(delta=-hump_round)
    difference() {
        translate([nano[0] - fit - hump_wall, hump_bottom]) square(1000);
        for (k = keys)
            translate([k[0], k[1]]) rotate(k[2])
                square(keycap + 2 * keycap_clearance, center=true);
    }
}

// Footprint of the cover where it sits on the case, and the open space inside:
// everything within its walls except the magnet block, kept clear of the
// mounting inserts.
module cover_footprint() {
    intersection() {
        hump_outer(0, 1);
        hump_area();
    }
}

module cover_space() {
    difference() {
        offset(delta=-cover_wall) cover_footprint();
        translate([-500, -500]) square([block_x1 + 500, block_y1 + 500]);
        for (h = mounting_holes) translate([h[0], h[1]]) circle(r=1.4 + 1);
    }
}

// One layer of the raised section, ending at height z: rounded near the top.
module hump_slice(z) {
    d = z > hump_top - hump_round
        ? -(hump_round - sqrt(pow(hump_round, 2) - pow(z - (hump_top - hump_round), 2)))
        : 0;
    offset(delta=d) hump_area();
}

// Snug room for the nano on its sockets, the battery under it and the USB plug.
module mcu_cutout() {
    color("pink") {
        // sockets, nano and battery (between the socket rows, under the nano)
        translate([0, 0, top_of_pcb])
            box(nano, nano_top + nano_parts + fit - top_of_pcb, fit);
        // battery pads just below the nano, with room to bend the wires
        translate([0, 0, top_of_pcb]) box(battery_pads, socket_height, 1);
        // USB-C receptacle
        translate([nano_x - usb_width / 2 - fit, nano[3] - usb_depth, nano_top - fit])
            cube([usb_width + 2 * fit, usb_depth + 10, usb_top - nano_top + fit]);
        // U-shaped notch in the end wall, so the plug's body can reach the receptacle
        plug_bottom = nano_top + usb_height / 2 - plug_height / 2;
        translate([nano_x, nano[3] - 0.5, 0]) rotate([-90, 0, 0]) linear_extrude(20)
            translate([0, -(plug_bottom + 15)])
                offset(r=1) offset(delta=-1) square([plug_width, 30], center=true);
    }
}

// The slide switch lever sticks out of the right edge: slot the wall for it.
module power_switch_cutout() {
    color("orange") translate([0, 0, top_of_pcb]) {
        box(power_switch, 2, 0.5);
        cy = (power_switch[1] + power_switch[3]) / 2;
        translate([power_switch[0], cy - 2.5, 0]) cube([20, 5, 2.5]);
    }
}

// Room for the reset button, and a hole above it to press it with a pin.
module reset_cutout() {
    color("orange") translate([0, 0, top_of_pcb]) {
        box(reset_button, 2.6, 0.5);
        translate([(reset_button[0] + reset_button[2]) / 2, (reset_button[1] + reset_button[3]) / 2, 0])
            cylinder(h=20, d=3.5);
    }
}

// Only when an encoder is fitted; otherwise the raised section covers its spot.
module encoder_cutout() {
    color("pink") translate([0, 0, top_of_pcb]) {
        box(encoder_body, 20, 0.6);
        box(encoder_pads, 3, 0.5);
    }
}

// Everything cut out of a top case half, in front view; the right half is
// the same shape mirrored. With the encoder fitted there is no room for the
// cover's magnets.
module top_cutouts(encoder=false) {
    linear_extrude(top_of_pcb) offset(delta=0.45) base();
    translate([0,0,top_of_pcb]) switch_holes();
    mcu_cutout();
    power_switch_cutout();
    reset_cutout();
    // open up to the cover, so the battery has room past the nano
    translate([0, 0, top_of_pcb]) linear_extrude(case_top - top_of_pcb + 1) cover_space();
    if (encoder) encoder_cutout();
    else {
        for (m = cover_magnets)
            translate([m[0], m[1], case_top - magnet_depth]) cylinder(h=magnet_depth + 1, d=magnet_d);
        for (p = cover_pegs)
            translate([p[0], p[1], case_top - peg_h - 0.5]) cylinder(h=peg_h + 1.5, d=peg_hole_d);
    }
    mounting_hole_inserts();
}

// The cover, in front view, sitting on the case top.
module cover() {
    difference() {
        union() {
            cover_shell();
            // locating pegs, chamfered at the tip
            for (p = cover_pegs) translate([p[0], p[1], case_top - peg_h]) {
                translate([0, 0, 0.5]) cylinder(h=peg_h, d=peg_d);
                cylinder(h=0.5, d1=peg_d - 1, d2=peg_d);
            }
        }
        translate([0, 0, case_top - 1]) linear_extrude(usb_top - case_top + 1) cover_space();
        mcu_cutout();
        reset_cutout();
        for (m = cover_magnets)
            translate([m[0], m[1], case_top - 1]) cylinder(h=magnet_depth + 1, d=magnet_d);
    }
}
