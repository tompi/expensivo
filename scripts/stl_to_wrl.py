#!/usr/bin/env python3
"""Convert a binary STL to a coloured VRML 2.0 model for KiCad's 3D viewer.

  stl_to_wrl.py in.stl out.wrl --color 0.23 0.24 0.27 [--y-up]

KiCad reads VRML in units of 0.1 inch, so coordinates are divided by 2.54.
--y-up turns a model drawn with Y as its height into KiCad's Z-up. The model
is centred in X/Y and put with its lowest point at Z = 0.
"""
import argparse
import struct


def read_stl(path):
    data = open(path, "rb").read()
    (count,) = struct.unpack_from("<I", data, 80)
    tris = []
    for i in range(count):
        v = struct.unpack_from("<12f", data, 84 + i * 50)
        tris.append((v[3:6], v[6:9], v[9:12]))
    return tris


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl")
    ap.add_argument("wrl")
    ap.add_argument("--color", nargs=3, type=float, default=(0.8, 0.8, 0.8))
    ap.add_argument("--y-up", action="store_true")
    a = ap.parse_args()

    tris = read_stl(a.stl)
    if a.y_up:
        tris = [tuple((x, -z, y) for x, y, z in t) for t in tris]
    xs = [p[0] for t in tris for p in t]
    ys = [p[1] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    cx, cy, z0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)

    index, points, faces = {}, [], []
    for t in tris:
        f = []
        for x, y, z in t:
            key = (round((x - cx) / 2.54, 4), round((y - cy) / 2.54, 4), round((z - z0) / 2.54, 4))
            if key not in index:
                index[key] = len(points)
                points.append(key)
            f.append(index[key])
        if len(set(f)) == 3:
            faces.append(f)

    r, g, b = a.color
    with open(a.wrl, "w") as out:
        out.write("#VRML V2.0 utf8\n")
        out.write(f"# converted from {a.stl.split('/')[-1]} by scripts/stl_to_wrl.py\n")
        out.write("Shape {\n  appearance Appearance { material Material {\n")
        out.write(f"    diffuseColor {r} {g} {b} specularColor 0.2 0.2 0.2 shininess 0.3 }} }}\n")
        out.write("  geometry IndexedFaceSet {\n    creaseAngle 0.5\n    coord Coordinate { point [\n")
        out.write(",\n".join(f"{x:g} {y:g} {z:g}" for x, y, z in points))
        out.write("\n    ] }\n    coordIndex [\n")
        out.write(",\n".join(f"{f[0]},{f[1]},{f[2]},-1" for f in faces))
        out.write("\n    ]\n  }\n}\n")
    print(f"{a.wrl}: {len(points)} points, {len(faces)} faces")


if __name__ == "__main__":
    main()
