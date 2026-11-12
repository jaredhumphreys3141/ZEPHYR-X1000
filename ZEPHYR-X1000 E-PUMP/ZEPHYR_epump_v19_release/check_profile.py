import sys, math, numpy as np, cadquery as cq
V,raw,TR,TT,R=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5])
src=open("inducer_cad_fillet.py").read().split("def blade_solid")[0]
sys.argv=["x","/home/claude/rel/data/inducer_designs_v16.json",V,"0",str(TR),str(TT),"0","tmp",str(R)]
exec(src)                                       # geometry helpers (mid_point, normal_at, hub_r, fillet_add, ...)
s=cq.importers.importStep(raw).val()
def thickness(p,n):
    def edge(sgn):
        lo,hi=0.0,1.5
        for _ in range(30):
            m=(lo+hi)/2
            if s.isInside(cq.Vector(*(p+sgn*n*m))): lo=m
            else: hi=m
        return lo
    return edge(1)+edge(-1)
from scipy.optimize import brentq
for u in (0.35,0.65):
    print(f"{V} u={u}: h above hub | measured t | design t (R{R})")
    for h in (0.02,0.05,0.1,0.2,0.3,0.4,0.6,1.0):
        def f(v):
            p,th,r=mid_point(u,v); return r-(hub_r(p[2])+h)
        v=brentq(f,0.0,0.6); n,p=normal_at(u,v)
        rr=math.hypot(p[0],p[1]); fr=np.clip((rr-hub_r(p[2]))/(r_t-hub_r(p[2])),0,1)
        des=TR+(TT-TR)*fr+fillet_add(h)
        print(f"   {h:4.2f}   {thickness(p,n):6.3f}   {des:6.3f}")
