"""Section through the 50/230 deg plane: bleed port (50 deg, +x) and weep port (230 deg, -x)."""
import numpy as np, cadquery as cq
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
exec(open("xsection_v19.py").read().split("data={}")[0])        # reuse names, colours, sec()
sol=cq.importers.importStep("pump_assembly_HTP_v19.step").solids().vals()
d={n:sec(s,50.0) for n,s in zip(names,sol)}
fig,ax=plt.subplots(figsize=(14,9.5))
for n,(T,S) in d.items():
    z=3 if n in ("ring","carrier") else 2
    if T: ax.add_collection(PolyCollection(T,facecolors=col[n],edgecolors=col[n],linewidths=0.2,zorder=z))
    if S: ax.add_collection(LineCollection(S,colors="k",linewidths=0.7,zorder=z+0.5))
ax.set_aspect("equal"); ax.set_xlim(-34,40); ax.set_ylim(-22,2); ax.axvline(0,color="k",lw=0.4,ls="--")
A=dict(fontsize=9,arrowprops=dict(arrowstyle="->",lw=0.8,color="#a01818"),zorder=7,bbox=dict(fc="white",ec="none",alpha=0.9,pad=1.5))
ax.annotate("BLEED → tank (50°)\nØ1.8 drilling inside the 2.0 bleed groove,\nbetween floating ring carrier and lip seal;\nM5 × 5 in the flange with a Ø8 boss below",(20,-7.3),(18.5,-17.5),**A)
ax.annotate("WEEP → overboard (230°)\nØ2.0 from the weep cavity (lip seal ↔ bearings),\nM5 × 6 on a Ø8 boss (r 13–19), clear of the\nseal bore and the bearing seat",(-16,-16.6),(-33.5,-6.3),**A)
B=dict(fontsize=8.5,zorder=7,bbox=dict(fc="white",ec="none",alpha=0.85,pad=1))
ax.text(6.0,-1.3,"floating ring + carrier",**B); ax.text(6.3,-12.2,"lip seal 10×24×7",**B); ax.text(5.6,-20.8,"front 708 pair",**B)
ax.set_xlabel("distance along the 50° (+) / 230° (−) direction (mm)"); ax.set_ylabel("z (mm), +z = inlet")
ax.set_title("ZEPHYR e-pump v19 (HTP; IPA identical here): section through the bleed and weep ports",fontsize=11)
plt.tight_layout(); plt.savefig("pump_v19_ports_section.png",dpi=150); print("ok")
