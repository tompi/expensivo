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
// The nano's two pin rows, and its three middle pins, get one slot each;
// other pins their own pocket.
function pad_x(p) = (p[0] + p[2]) / 2;
function pad_y(p) = (p[1] + p[3]) / 2;
function under_nano(p) = pad_y(p) > nano[1] && pad_y(p) < nano[3];
function on_nano_row(p) = under_nano(p) && abs(abs(pad_x(p) - nano_x) - 7.62) < 0.3;
function nano_middle(p) = under_nano(p) && abs(pad_x(p) - nano_x) < 6;
module tht_pockets() {
    color("#7f7f7f") {
        for (side = [-1, 1])
            hull() for (p = tht_pads)
                if (on_nano_row(p) && sign(pad_x(p) - nano_x) == side) box(p, 1.5, 0.4);
        hull() for (p = tht_pads) if (nano_middle(p)) box(p, 1.5, 0.4);
        for (p = tht_pads)
            if (!on_nano_row(p) && !nano_middle(p)) box(p, 1.5, 0.4);
    }
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
    // the board has a small pocket between the inner thumb key (K18) and the
    // keys above it (K3, K6); the case fills it, so its wall runs straight up
    // from the thumb key to the main body. KiCad coordinates: K18 at
    // (140.34, 122.56), K3 at (145.01, 100.86), K6 at (126.01, 98.32).
    at([140.34 - 8.1, 122.56 - 8 + 1])    // case y points up, KiCad y down
        square([(145.01 - 8.1 + 1) - (140.34 - 8.1), (122.56 - 8 + 1) - (98.32 + 8 - 1)]);
    // out to the board's straight side edge, so that corner is one clean curve
    translate([nano[0] - fit, nano[1]]) square([max(nano[2] + fit, mcu_edge_x) - nano[0] + fit, nano[3] - nano[1] + fit]);
}

module case() {
    color("red")
    for (i = [0:step:case_top - 1])
        translate([0,0,i]) linear_extrude(height=1) difference() {
            offset(delta = wall_profile(i, case_top - 1) + 1) shell_outline();
            // under the skirt the case's own top rounding doesn't apply at this corner
            end_corner_mask(mcu_edge_x + 1 +
                (i >= skirt_bottom - seat_round_ledge ? edge_bulge : wall_profile(i, case_top - 1)));
        }
}

// The flat USB end cuts through the rounding of the corner where it meets the
// outer side; round that corner again, at the side wall's position xs.
end_corner_r = 3;
module end_corner_band(r_in, r_out) {
    intersection() {
        translate(end_c) square(50);
        translate(end_c) difference() { circle(r=r_out); circle(r=r_in); }
    }
}
module end_corner_mask(xs) {
    r = end_corner_r;
    translate([xs - r, usb_mouth - r]) difference() {
        square(r + 10);
        circle(r=r);
    }
}

// The cover over the nice!nano, sitting on the case top. Along the outer side
// a skirt reaches down over the case's top edge to where its rounding starts,
// so case and cover form one wall, rounded only at the bottom and the top.
module cover_shell() {
    color("red")
    for (i = [skirt_bottom:step:hump_top - 1])
        translate([0,0,i]) linear_extrude(height=1)
            difference() {
                intersection() {
                    hump_outer(i, hump_top - 1);
                    hump_slice(i + 1);
                    if (i < case_top) skirt_ring();
                }
                end_corner_mask(mcu_edge_x + wall_profile(i, hump_top - 1) + 1);
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
// USB-C receptacle: mid-mount, through the nano's board (measured on the
// nice!nano v2 model; the common 33 x 17.78 mm clones match)
usb_width = 8.94;
usb_height = 2.96;
usb_below = 1.38;        // shell bottom below the nano's underside
usb_protrude = 0.74;     // shell mouth past the nano's board edge
usb_depth = 7.3;         // shell length
usb_fit = 0.25;          // clearance around the shell
end_round = 1.5;         // radius of the flat USB end's outer edges
fit = 0.3;               // clearance around the nano
roof = 1.2;
keycap = 18.2;
keycap_clearance = 0.5;
hump_wall = 1.5;         // side wall between the nano and the keys next to it
hump_round = edge_radius;  // radius of the raised section's top edges, as on the case edge

nano_top = top_of_pcb + socket_height + nano_thickness;
cavity_top = nano_top + nano_parts + fit;
hump_top = cavity_top + roof;
nano_x = (nano[0] + nano[2]) / 2;
usb_zc = top_of_pcb + socket_height - usb_below + usb_height / 2;
// the case's USB end is a flat face flush with the receptacle's mouth, so the
// plug's body seats against it and only its metal tip goes in
usb_mouth = nano[3] + usb_protrude;
end_x0 = nano[0] - fit - hump_wall;   // the flat end spans the nano column
end_inset = 2.5;                      // above the nano, the inside stops this far from the end
// centre of that corner's rounding where the wall bulges out fully; the skirt and
// the step under it are rounded about the same centre, so they nest
end_c = [mcu_edge_x + edge_bulge + 1 - end_corner_r, usb_mouth - end_corner_r];

// The cover runs from above the thumb keys to the nano's USB end.
hump_bottom = encoder_pads[1] - 0.2;

// The cover's skirt over the case's top edge, on the outer side.
skirt_bottom = case_top - edge_radius;   // where the case's top rounding starts
skirt_t = 1.2;
skirt_clr = 0.15;

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
    offset(r = wall_profile(i, t) + 1) cover_edge();
}

// The outline the cover's outer walls follow: the case's own (board plus the
// nano's overhanging USB end), filled in towards the keys, so the cover's
// sides and corners line up with the case below.
module cover_edge() {
    shell_outline();
    translate([-500, -500]) square([mcu_edge_x - 2 + 500, nano[3] + 500]);
}

// The skirt's band, inside the full-bulge outer wall; the case steps in under it.
module skirt_ring() {
    difference() {
        offset(r = edge_bulge + 1) cover_edge();
        offset(r = edge_bulge + 1 - skirt_t) cover_edge();
    }
    end_corner_band(end_corner_r - skirt_t, end_corner_r);
}

// The case steps in under the skirt. With the cover off that step shows, so
// its edges are rounded: the stepped-in wall's top edge, and (smaller, as it is
// the parting line with the cover on) the ledge's outer edge.
seat_round_top = 1.0;
seat_round_ledge = 0.6;

module seat_band(o) {
    intersection() {
        hump_area();
        union() {
            difference() {
                offset(r = 50) cover_edge();
                offset(r = o) cover_edge();
            }
            // at the USB end corner, rounded about the outer corner's centre
            translate(end_c) difference() {
                square(50);
                circle(r = end_corner_r - (edge_bulge + 1 - o));
            }
        }
    }
}

function round_in(r, d) = r - sqrt(max(0, pow(r, 2) - pow(min(d, r), 2)));

module skirt_seat() {
    outer = edge_bulge + 1;
    wall = outer - skirt_t - skirt_clr;
    translate([0, 0, skirt_bottom]) linear_extrude(case_top - skirt_bottom + 1) seat_band(wall);
    r1 = seat_round_top;
    for (z = [case_top - r1 : 0.1 : case_top - 0.05])
        translate([0, 0, z]) linear_extrude(0.11) seat_band(wall - round_in(r1, z + 0.1 - (case_top - r1)));
    r2 = seat_round_ledge;
    for (z = [skirt_bottom - r2 : 0.1 : skirt_bottom - 0.05])
        translate([0, 0, z]) linear_extrude(0.11) seat_band(outer - round_in(r2, z - (skirt_bottom - r2)));
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
        translate([-500, nano[3] - end_inset]) square(1000);
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

// Snug room for the nano on its sockets, the battery under it and the USB-C port.
module mcu_cutout() {
    color("pink") {
        // sockets, nano and battery (between the socket rows, under the nano); at
        // the USB end the nano's board edge is only usb_protrude from the case's end
        // face, so no clearance there, and the parts above it stay further back
        translate([nano[0] - fit, nano[1] - fit, top_of_pcb])
            cube([nano[2] - nano[0] + 2 * fit, nano[3] - nano[1] + fit, nano_top + fit - top_of_pcb]);
        translate([nano[0] - fit, nano[1] - fit, top_of_pcb])
            cube([nano[2] - nano[0] + 2 * fit, nano[3] - end_inset - nano[1] + fit, cavity_top - top_of_pcb]);
        // battery pads just below the nano, with room to bend the wires
        translate([0, 0, top_of_pcb]) box(battery_pads, socket_height, fit);
        // the USB-C shell, through the end wall: a snug rounded slot
        translate([nano_x, usb_mouth - usb_depth, usb_zc]) rotate([-90, 0, 0])
            linear_extrude(usb_depth + 10) hull()
                for (dx = [-1, 1]) translate([dx * (usb_width - usb_height) / 2, 0])
                    circle(d=usb_height + 2 * usb_fit);
    }
}

// Everything past the flat USB end, with its bottom (top frame) or top (cover)
// edge rounded.
module usb_end_cut(round_bottom=undef, round_top=undef) {
    r = end_round;
    translate([end_x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(500) {
        translate([usb_mouth, -50]) square([500, 200]);
        if (!is_undef(round_bottom)) difference() {
            translate([usb_mouth - r, round_bottom - 1]) square([r + 1, r + 1]);
            translate([usb_mouth - r, round_bottom + r]) circle(r=r);
        }
        if (!is_undef(round_top)) difference() {
            translate([usb_mouth - r, round_top - r]) square([r + 1, r + 1]);
            translate([usb_mouth - r, round_top - r]) circle(r=r);
        }
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

// Room for the reset button; take the cover off to press it.
module reset_cutout() {
    color("orange") translate([0, 0, top_of_pcb]) box(reset_button, 2.6, 0.5);
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
    usb_end_cut(round_bottom=0);
    skirt_seat();
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
        translate([0, 0, case_top - 1]) linear_extrude(cavity_top - case_top + 1) cover_space();
        mcu_cutout();
        usb_end_cut(round_top=hump_top);
        reset_cutout();
        for (m = cover_magnets)
            translate([m[0], m[1], case_top - 1]) cylinder(h=magnet_depth + 1, d=magnet_d);
    }
}
