#!/usr/bin/env python3
"""
Build the 3-blade variable-lead inducer as a solid and export STEP.

Units: mm. Axis = +Z, flow enters at z = 0 (inlet) and leaves at z = L.
Rotation is +Z right-hand (counter-clockwise looking down the inlet from -Z
toward +Z... i.e. blades advance in +theta as z increases).

Simplifications (finish in CAD/CAM):
  * constant blade thickness, square blade ends (bevel/sharpen LE in CAM)
  * blade-root fillets: optional radius FILLET_R (argv[8]); the blade thickness flares as a circular arc
    tangent to the blade face at height R above the hub and tangent to the hub at the root (v19)
  * shaft interface (v3): plain Ø3 H7 through-bore, 0.5 mm Ø-hub land at the inlet
    for the nose-cone nut; no threads in the inducer
"""
import math
import numpy as np
import cadquery as cq
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections

# ---------------- parameters ----------------
r_t = 7.0                      # tip radius
r_h_in, r_h_out = 2.5, 4.0     # hub radius at blade inlet / exit (exit matches impeller Ø8 boss)
beta_in, beta_out = 8.0, 16.0  # tip blade angle (deg from tangential)
wrap = np.radians(240.0)       # blade wrap
sweep = np.radians(60.0)       # LE sweep (tip LE trails hub LE by this angle)
n_blades = 3
t_blade = 0.6                  # blade thickness (normal to blade surface)
embed = 0.8                    # blade roots sink into the hub (0.8 gives robust booleans on all v7 geometries)
overshoot = 0.5                # radial overshoot past tip before trimming
nose_len = 0.5                 # short cylindrical land ahead of the LE: the nose-cone nut seats on it
aft_len = 1.0                  # aft spigot length (seats on impeller Ø9 boss)
nose_tip_r = 2.0               # blunt nose tip radius (nose is closed)
pilot_d, pilot_depth = 5.0, 1.5   # H6 pilot counterbore from aft face (centres on shaft)
tap_drill_d, tap_depth = 3.5, 4.0 # M4x0.5 tapped hole beyond the pilot (tap drill dia modeled)
n_u, n_v = 36, 12              # section count along blade, points per section

# ---- optional: take geometry from an SP-8052 design file:  inducer_cad.py designs.json HTP|IPA
import sys, json as _json
OUT_NAME = "inducer_14mm_3blade"
if len(sys.argv) >= 3:
    _d = {x["name"]: x for x in _json.load(open(sys.argv[1]))}[sys.argv[2]]
    r_t = _d["D_tip_mm"] / 2
    r_h_in, r_h_out = _d["d_hub_in_mm"] / 2, _d["d_hub_out_mm"] / 2
    beta_in, beta_out = _d["beta_in_tip_deg"], _d["beta_out_tip_deg"]
    wrap, sweep = np.radians(_d["wrap_deg"]), np.radians(_d["sweep_deg"])
    n_blades = _d["blades"]
    OUT_NAME = sys.argv[7]
    LAM = np.radians(float(sys.argv[3])); T_ROOT, T_TIP = float(sys.argv[4]), float(sys.argv[5]); STOCK = float(sys.argv[6])
    FILLET_R = float(sys.argv[8]) if len(sys.argv) > 8 else 0.0

# ---------------- blade geometry helpers ----------------
th_fine = np.linspace(0, wrap, 2000)
beta_fine = np.radians(beta_in + (beta_out - beta_in) * th_fine / wrap)
z_fine = np.concatenate([[0], np.cumsum(r_t * np.tan(beta_fine[1:]) * np.diff(th_fine))])
L = z_fine[-1]
z_of = lambda th: np.interp(th, th_fine, z_fine)
dz_dth = lambda th: r_t * np.tan(np.radians(beta_in + (beta_out - beta_in) * th / wrap))
hub_r = lambda z: r_h_in + (r_h_out - r_h_in) * np.clip(z, 0, L) / L


def mid_point(u, v):
    """u in [0,1] along blade (LE->TE), v in [0,1] hub(embedded)->tip(overshoot)."""
    # radial span at the LE-adjusted station: solve radius from v using hub at z
    # first guess of theta from hub-relative span fraction
    s = np.clip(v * 1.2 - 0.1, 0, 1)            # fraction of real span (for sweep)
    th_le = s * sweep
    th = th_le + u * (wrap - th_le)
    z0 = z_of(th)
    rh = hub_r(z0) - embed
    r = rh + v * (r_t + overshoot - rh)
    z = z0 - (r - hub_r(z0)) * np.tan(LAM)
    return np.array([r * np.cos(th), r * np.sin(th), z]), th, r


def normal_at(u, v, du=1e-4, dv=1e-4):
    p0 = mid_point(u, v)[0]
    pu = mid_point(min(u + du, 1), v)[0] - mid_point(max(u - du, 0), v)[0]
    pv = mid_point(u, min(v + dv, 1))[0] - mid_point(u, max(v - dv, 0))[0]
    n = np.cross(pu, pv)
    return n / np.linalg.norm(n), p0


def vec(p):
    return cq.Vector(*map(float, p))


def fillet_add(h):
    """extra total thickness (both sides) giving a root fillet of radius FILLET_R; h = height above the hub surface"""
    R = FILLET_R
    if R <= 0 or h >= R: return 0.0
    if h <= 0: return 2 * R
    return 2 * (R - math.sqrt(max(R * R - (R - h) ** 2, 0.0)))

def v_grid():
    span = r_t + overshoot - (min(r_h_in, r_h_out) - embed)
    v_lo = (embed - 0.15) / (r_t + overshoot - (max(r_h_in, r_h_out) - embed))
    v_hi = (embed + abs(r_h_out - r_h_in) + FILLET_R + 0.15) / (r_t + overshoot - (min(r_h_in, r_h_out) - embed))
    vv = list(np.linspace(0, 1, n_v))
    if FILLET_R > 0: vv += list(np.linspace(max(v_lo, 0.0), min(v_hi, 1.0), 26))
    return sorted(set(round(x, 6) for x in vv))

def blade_solid(phi0):
    sections = []; caps_src = []
    for u in np.linspace(0, 1, n_u):
        side_a, side_b = [], []
        for v in v_grid():
            n, p = normal_at(u, v)
            rr = np.hypot(p[0], p[1]); rh0 = hub_r(np.clip(p[2], 0, L))
            f = np.clip((rr - rh0) / (r_t - rh0), 0, 1)
            tb = T_ROOT + (T_TIP - T_ROOT) * f + fillet_add(rr - rh0)
            side_a.append(p + n * tb / 2)
            side_b.append(p - n * tb / 2)
        rot = lambda q: np.array([q[0] * np.cos(phi0) - q[1] * np.sin(phi0),
                                  q[0] * np.sin(phi0) + q[1] * np.cos(phi0), q[2]])
        A = [vec(rot(q)) for q in side_a]
        B = [vec(rot(q)) for q in side_b][::-1]
        e1 = cq.Edge.makeSpline(A)
        e2 = cq.Edge.makeLine(A[-1], B[0])
        e3 = cq.Edge.makeSpline(B)
        e4 = cq.Edge.makeLine(B[-1], A[0])
        sections.append(cq.Wire.assembleEdges([e1, e2, e3, e4]))
        caps_src.append((A, [vec(rot(q)) for q in side_b]))
    loft = BRepOffsetAPI_ThruSections(False, False, 1e-6)
    for w in sections:
        loft.AddWire(w.wrapped)
    loft.CheckCompatibility(False)
    loft.Build()
    side = cq.Shape.cast(loft.Shape())
    caps = [cq.Face.makeRuledSurface(cq.Edge.makeSpline(caps_src[k][0]), cq.Edge.makeSpline(caps_src[k][1])) for k in (0, -1)]   # end caps = ruled (exact)
    shell = cq.Shell.makeShell(side.Faces() + caps)
    sol = cq.Solid.makeSolid(shell)
    if sol.Volume() < 0:
        sol = cq.Solid(sol.wrapped.Reversed())
    return sol


# ---------------- hub (revolved profile in XZ plane) ----------------
pts = [
    (0.0, -nose_len),
    (r_h_in, -nose_len),                   # cylindrical land (nut seat)
    (r_h_in, 0.0),                          # nose -> blade inlet
    (r_h_out, L),                           # tapered hub under blades
    (r_h_out, L + aft_len),                 # aft spigot
    (0.0, L + aft_len),
]
hub = (cq.Workplane("XZ").polyline(pts).close()
       .revolve(360, (0, 0, 0), (0, 1, 0)))

# ---------------- assemble ----------------
tip_env = cq.Workplane("XY").workplane(offset=-12).circle(r_t + STOCK).extrude(L + aft_len + 14)
PHASE = 0.0
part = hub
BL = []
for b in range(n_blades):
    _bs = blade_solid(b * 2 * np.pi / n_blades + PHASE)              # built in place (no rigid copy), phase avoids the 0/180 deg cap failure

    blade = cq.Workplane("XY").add(_bs)
    blade = blade.intersect(tip_env)
    try: BL.append(blade.cut(hub).val())   # exposed blade only (outside the hub)
    except Exception: BL.append(blade.val())
    for _tol in (1e-4, 3e-4, 1e-3, None):
        try:
            _u = part.union(blade, tol=_tol) if _tol else part.union(blade)
            if _u.val().isValid(): part = _u; break
        except Exception: pass
    else: raise RuntimeError("blade union failed")

part = part.intersect(tip_env)          # global tip trim (per-blade intersect can fail silently)
part = part.rotate((0,0,0),(0,0,1), -np.degrees(PHASE))
# hub left solid: bores are cut in the combined part
try:
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    _dd = BRepExtrema_DistShapeShape(BL[0].wrapped, BL[1].wrapped); _dd.Perform()
    print('min blade-to-blade distance (mm): %.3f' % _dd.Value())
    _p1=_dd.PointOnShape1(1); _p2=_dd.PointOnShape2(1); print('  at r %.2f z %.2f -> r %.2f z %.2f' % (math.hypot(_p1.X(),_p1.Y()), _p1.Z(), math.hypot(_p2.X(),_p2.Y()), _p2.Z()))
except Exception as ex: print('gap check skipped', ex)
solid = part.val()
print("valid:", solid.isValid())
print("volume (mm^3): %.1f" % solid.Volume())
bb = solid.BoundingBox()
print("bbox: x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f" % (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
print("blade axial length L = %.2f mm" % L)
print("mass in 316L (8.0 g/cc): %.2f g" % (solid.Volume() * 8.0e-3))

cq.exporters.export(part, OUT_NAME + ".step")
print("exported")
