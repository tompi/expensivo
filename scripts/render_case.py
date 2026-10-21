#!/usr/bin/env python3
"""Render the printable case parts to clean, checked STLs.

    scripts/render_case.py [part ...] [-o build/case] [--openscad CMD]

OpenSCAD's manifold backend produces an exact manifold, but writing it as STL
rounds every vertex to float32, and features thinner than that rounding
(where two cuts nearly share a face) collapse into zero-area faces and
non-manifold edges, which slicers report as floating regions or errors. So
each part is exported as a full-precision 3MF instead, features below
TOLERANCE are collapsed with manifold3d's simplify(), which keeps the mesh
manifold, and only then written as binary STL. Each STL is read back and
checked: one watertight body, no degenerate faces, the same size and volume
as the exact model, and, sliced at the usual layer heights, no island that
starts in mid-air or rests only on material thinner than an extrusion line.
The script exits non-zero if any part fails.

Needs OpenSCAD with the manifold backend (a recent snapshot) and
    pip install numpy trimesh shapely manifold3d scipy networkx
--openscad (or $OPENSCAD) may be a whole command, e.g. a docker run; it is run
from the repository root with paths relative to it.
"""
import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor

import manifold3d
import numpy as np
import trimesh
from shapely.ops import unary_union

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PARTS = ["top-left", "top-right", "cover-left", "cover-right", "bottom-left", "bottom-right"]
TOLERANCE = 1e-4      # mm; features below this are collapsed
LAYERS = [0.2, 0.08]  # layer heights for the island check
LINE = 0.42           # extrusion line width
MIN_AREA = 0.005      # mm^2; smaller islands are ignored


def render_3mf(openscad, part, out):
    cmd = shlex.split(openscad) + [
        "--backend=manifold",
        "-O", "export-3mf/decimal-precision=16",
        "-O", "export-3mf/add-meta-data=false",
        "-o", os.path.relpath(out, ROOT),
        os.path.join("case", f"expensivo-{part}.scad"),
    ]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"openscad failed:\n{r.stdout}{r.stderr}")


def load_3mf(path):
    xml = zipfile.ZipFile(path).read("3D/3dmodel.model").decode()
    v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', xml), dtype=np.float64)
    t = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', xml), dtype=np.uint32)
    return v, t


def write_stl(path, v, t):
    tri = v[t].astype(np.float32)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-30)
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    with open(path, "wb") as f:
        f.write(b"\0" * 80 + np.uint32(len(t)).tobytes() + rec.tobytes())


def layer(mesh, z):
    s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return None
    polys = list(s.to_2D(to_2D=np.eye(4))[0].polygons_full)
    return unary_union(polys).buffer(0) if polys else None


def pieces(g):
    return [] if g is None or g.is_empty else list(getattr(g, "geoms", [g]))


def islands(mesh, h):
    """(z, x, y) of every island that starts in mid-air or rests only on
    material thinner than an extrusion line, slicing at layer height h."""
    found, prev = [], None
    for z in np.arange(h / 2, mesh.bounds[1][2], h):
        g = layer(mesh, z)
        if prev is not None:
            solid = prev.buffer(-LINE / 2, join_style=2).buffer(LINE / 2, join_style=2)
            for p in pieces(g):
                if p.area >= MIN_AREA and p.intersection(solid).area < MIN_AREA:
                    found.append((z, p.centroid.x, p.centroid.y))
        prev = g
    return found


def check(path, exact_volume, exact_extents, slice_check):
    m = trimesh.load(path)
    edges, counts = np.unique(m.edges_sorted, axis=0, return_counts=True)
    problems = []
    if not m.is_watertight or (counts != 2).any():
        problems.append(f"{int((counts != 2).sum())} non-manifold edges")
    if len(m.split(only_watertight=False)) != 1:
        problems.append(f"{len(m.split(only_watertight=False))} separate bodies")
    if (m.area_faces < 1e-12).any():
        problems.append(f"{int((m.area_faces < 1e-12).sum())} degenerate faces")
    if abs(m.volume - exact_volume) > 1e-4 * exact_volume:
        problems.append(f"volume {m.volume:.3f} vs exact {exact_volume:.3f}")
    if np.abs(m.extents - exact_extents).max() > 0.01:
        problems.append(f"extents {np.round(m.extents, 3)} vs exact {np.round(exact_extents, 3)}")
    if slice_check:
        c = (m.bounds[0] + m.bounds[1]) / 2
        for h in LAYERS:
            for z, x, y in islands(m, h):
                problems.append(f"island at ({x - c[0]:.1f}, {y - c[1]:.1f}), z={z:.2f}, {h} mm layers")
    return m, problems


def build(part, args, tmp):
    src = os.path.join(tmp, f"{part}.3mf")
    render_3mf(args.openscad, part, src)
    v, t = load_3mf(src)
    exact = manifold3d.Manifold(manifold3d.Mesh(vert_properties=v, tri_verts=t))
    if exact.status() != manifold3d.Error.NoError:
        raise RuntimeError(f"OpenSCAD's output is not a manifold: {exact.status()}")
    clean = exact.simplify(TOLERANCE)
    if len(clean.decompose()) != 1:
        raise RuntimeError(f"{len(clean.decompose())} separate bodies after cleaning")
    mesh = clean.to_mesh()
    out = os.path.join(args.out, f"expensivo-{part}.stl")
    write_stl(out, np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts))
    lo, hi = np.asarray(clean.bounding_box()[:3]), np.asarray(clean.bounding_box()[3:])
    m, problems = check(out, exact.volume(), hi - lo, not args.skip_slice_check)
    return out, m, problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("parts", nargs="*", default=PARTS, help="default: all of " + " ".join(PARTS))
    ap.add_argument("-o", "--out", default=os.path.join(ROOT, "build", "case"))
    ap.add_argument("--openscad", default=os.environ.get("OPENSCAD", "openscad"))
    ap.add_argument("--skip-slice-check", action="store_true", help="skip the (slow) island check")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    failed = False
    # OpenSCAD runs from the repository root (e.g. inside docker), so render inside it
    with tempfile.TemporaryDirectory(dir=os.path.join(ROOT, "build")) as tmp:
        with ThreadPoolExecutor() as pool:
            jobs = {p: pool.submit(build, p, args, tmp) for p in args.parts}
        for part, job in jobs.items():
            try:
                out, m, problems = job.result()
            except Exception as e:
                print(f"FAIL {part}: {e}")
                failed = True
                continue
            size = " x ".join(f"{x:.2f}" for x in m.extents)
            print(f"{'FAIL' if problems else 'ok  '} {os.path.relpath(out)}: {size} mm, "
                  f"{m.volume:.1f} mm3, {len(m.faces)} triangles")
            for p in problems:
                print(f"       {p}")
            failed |= bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
