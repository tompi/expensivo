// Visual assembly of both halves: case, pcb, nice!nano, switches and keycaps.
// For looking at only (F5); the top case and cover are imported from the STLs
// in build/case (in print orientation), so render those parts to STL first.
// explode > 0 spreads the layers apart vertically to show what is inside.
$fn = 24;
step = 0.5;
include <modules.scad>

explode = 0;
show_top = true;      // false to see inside
show_cover = true;
cover_lift = 0;       // lift the cover off to show the magnets and pegs
show_caps = true;
show_right = true;
half_gap = 150;       // distance between the two halves' centres

pcb_color = "#2d6a4f";
copper_color = "#d4a84b";
case_color = "#e9e5dc";
cover_color = "#e9e5dc";
cap_color = "#3a3d44";
cap_accent = "#c8553d";

// height of each layer when exploded
function lift(layer) = explode * layer;
L_PCB = 1;      // pcb, sockets, nano
L_TOP = 2;      // top frame
L_SWITCH = 3;   // switches
L_COVER = 3;    // cover (beside the switches)
L_CAP = 4;      // keycaps

module pcb_pad_shape(p) {
    translate([p[0], p[1]]) rotate(p[4])
        if (p[5] == 1) resize([p[2], p[3]]) circle(d=1);
        else square([p[2], p[3]], center=true);
}

// board with its drill holes, and the copper pads on the top side
module pcb() {
    translate([0, 0, bottom_plate_thickness]) {
        color(pcb_color) linear_extrude(pcb_thickness) difference() {
            base();
            for (p = pads_front) if (p[6] > 0) translate([p[0], p[1]]) circle(d=p[6]);
        }
        color(copper_color) translate([0, 0, pcb_thickness]) linear_extrude(0.05)
            difference() {
                for (p = pads_front) pcb_pad_shape(p);
                for (p = pads_front) if (p[6] > 0) translate([p[0], p[1]]) circle(d=p[6]);
            }
    }
}

// hotswap sockets under the board (the left half has them on the back)
module sockets(bottom) {
    color("#1b1b1b")
    for (k = keys)
        translate([k[0], k[1], bottom_plate_thickness - 1.85]) rotate(k[2]) translate([0.57, 4.7, 0])
            translate([0, bottom ? -9.42 : 0, 0]) mirror([0, bottom ? 0 : 1, 0])
                linear_extrude(1.85) projection() hotswap_mx();
}

// Cherry MX style switch, its bottom resting on the pcb
module mx_switch() {
    color("#9aa0a6") for (p = [[-3.81, 2.54], [2.54, 5.08]]) translate([p[0], p[1], top_of_pcb - 3.3])
        cylinder(h=3.3, d=1);
    color("#1b1b1b") translate([0, 0, top_of_pcb - 3.3]) cylinder(h=3.3, d=3.8);
    color("#1b1b1b") translate([0, 0, top_of_pcb])
        linear_extrude(case_top - top_of_pcb) square(14, center=true);
    color("#1b1b1b") hull() {
        translate([0, 0, case_top]) linear_extrude(0.1) square(15.6, center=true);
        translate([0, 0, case_top + 5.2]) linear_extrude(0.1) square(11, center=true);
    }
    color("#b33a3a") translate([0, 0, case_top + 5.2]) linear_extrude(3.4) {
        square([4, 1.2], center=true);
        square([1.2, 4], center=true);
    }
}

// DSA-like keycap: straight tapered sides and a slightly dished top.
module keycap(accent=false) {
    color(accent ? cap_accent : cap_color) difference() {
        hull() {
            linear_extrude(0.1) offset(r=1) square(18.2 - 2, center=true);
            translate([0, 0, 7.4]) linear_extrude(0.1) offset(r=2) square(12.7 - 4, center=true);
        }
        translate([0, 0, 7.4 + 20 - 0.6]) sphere(r=20, $fn=64);
    }
}

// nice!nano on its sockets, with the battery between the socket rows
module mcu() {
    nano_w = nano[2] - nano[0];
    nano_l = nano[3] - nano[1];
    pin_x = [nano[0] + 1.62, nano[2] - 1.62];
    // sockets
    color("#111111") for (x = pin_x)
        translate([x - 1.27, nano[1] + 0.4, top_of_pcb]) cube([2.54, 30.5, socket_height]);
    // battery
    // sticking out past the nano's end, into the space under the cover
    color("#6c7a89") translate([nano_x - 6, nano[1] - 4, top_of_pcb]) cube([12, 30, 3]);
    translate([0, 0, top_of_pcb + socket_height]) {
        color("#2b2d42") translate([nano[0], nano[1], 0]) cube([nano_w, nano_l, nano_thickness]);
        // pins through the nano
        color(copper_color) for (x = pin_x, i = [0:11])
            translate([x, nano[3] - 3.2 - i * 2.54, 0]) cylinder(h=nano_thickness + 0.8, d=0.8);
        // controller
        color("#111111") translate([nano_x - 3.5, nano[1] + 12, nano_thickness]) cube([7, 7, 0.9]);
    }
    // mid-mount USB-C receptacle, through the nano's board
    color("#c0c0c0") difference() {
        translate([nano_x, usb_mouth - usb_depth, usb_zc]) rotate([-90, 0, 0]) linear_extrude(usb_depth)
            hull() for (dx = [-1, 1]) translate([dx * (usb_width - usb_height) / 2, 0]) circle(d=usb_height);
        translate([nano_x, usb_mouth - 6.5, usb_zc]) rotate([-90, 0, 0]) linear_extrude(7)
            hull() for (dx = [-1, 1]) translate([dx * (usb_width - usb_height) / 2, 0]) circle(d=usb_height - 0.6);
    }
}

// small parts on the pcb: power switch, reset button
module small_parts() {
    color("#c0c0c0") translate([0, 0, top_of_pcb]) box(power_switch, 1.4, -0.4);
    color("#c0c0c0") translate([0, 0, top_of_pcb]) box(reset_button, 1.5, -1.3);
    color("#1b1b1b") translate([(reset_button[0] + reset_button[2]) / 2,
                               (reset_button[1] + reset_button[3]) / 2, top_of_pcb + 1.5])
        cylinder(h=1, d=3);
}

module switches_and_caps() {
    for (k = keys) translate([k[0], k[1], 0]) rotate(k[2]) {
        translate([0, 0, lift(L_SWITCH) - lift(L_PCB)]) mx_switch();
        if (show_caps) translate([0, 0, case_top + 6.3 + lift(L_CAP) - lift(L_PCB)])
            keycap(accent = k[1] < -25);   // thumb keys in the accent colour
    }
}

// the insides of one half, in the front view frame
module insides(left) {
    color(case_color) bottom();
    translate([0, 0, lift(L_PCB)]) {
        pcb();
        sockets(left);
        mcu();
        small_parts();
        switches_and_caps();
    }
}

// top case and cover STLs, turned back from their print orientation
module top_parts(side) {
    if (show_top) color(case_color) translate([0, 0, lift(L_TOP)])
        rotate([0, 180, 0]) translate([0, 0, -case_top])
            import(str("../build/case/expensivo-top-", side, ".stl"));
    if (show_top && show_cover) color(cover_color) translate([0, 0, lift(L_COVER) + cover_lift])
        rotate([0, 180, 0]) translate([0, 0, -hump_top])
            import(str("../build/case/expensivo-cover-", side, ".stl"));
}

translate([-half_gap / 2, 0, 0]) {
    insides(true);
    top_parts("left");
}

// the right half is the same pcb flipped; its case STLs are already mirrored
if (show_right) translate([half_gap / 2, 0, 0]) {
    mirror([1, 0, 0]) insides(false);
    top_parts("right");
}
