"""Inducer blade-root fillet sizing (strength). Nominal stress: handoff worst case 40 MPa (sharp root, includes transients).
Independent check of steady loads: Euler torque on the blades + centrifugal tension (radial-element blades -> no centrifugal bending)."""
import math
mat=dict(Su=550, Sy=280, Se_mach=200, Se_print=110)   # 316L L-PBF + HIP (MPa); 17-4PH H1025 is ~2x higher - 316L governs
for name,rpm,Q,dp,Z,rt,rh,t,span_root_len in (("HTP",30000,288e-6,158e3,3,7.5,3.75,0.8,2*30),("IPA",37563,127e-6,119e3,2,6.0,3.75,0.5,2*30)):
    w=rpm*math.pi/30
    T=Q*dp/0.7/w; F=T/Z/((rt+rh)/2e3)                     # tangential force per blade (N), inducer eta ~0.7
    M=F*(rt-rh)/2e3; Zs=span_root_len/2*1e-3*(t*1e-3)**2/6   # root bending moment, section modulus over the loaded root length
    s_hyd=M/Zs/1e6; s_cf=7800*w*w*((rt/1e3)**2-(rh/1e3)**2)/2/1e6
    print(f"{name}: steady hydraulic root bending ~{s_hyd:.1f} MPa, centrifugal tension ~{s_cf:.1f} MPa (handoff worst case 40 MPa)")
    gap={"HTP":1.50,"IPA":1.82}[name]
    print(f"  r(mm)  r/t   Kt    Kf   peak(MPa)  Goodman n (printed / machined root)  floor left(mm)  blockage")
    for r in (0.05,0.2,0.3,0.4,0.5,0.6,0.8):
        Kt=1+0.18*(r/t)**-0.75; a=0.0254*(2070/mat["Su"])**1.8; q=1/(1+a/r); Kf=1+q*(Kt-1)
        sm=40*Kt; sa=0.25*40*Kf                                # 25% alternating (cavitation / inflow distortion), worst-case 40 MPa nominal
        n_p=1/(sa/mat["Se_print"]+sm/mat["Su"]); n_m=1/(sa/mat["Se_mach"]+sm/mat["Su"])
        floor=gap-2*r; blk=2*(1-math.pi/4)*r*r/(gap*(rt-rh)) if floor>0 else float('nan')
        print(f"  {r:4.2f}  {r/t:4.2f}  {Kt:4.2f}  {Kf:4.2f}   {sm:5.0f}      {n_p:4.1f} / {n_m:4.1f}                      {floor:+5.2f}        {blk*100:4.1f}%")
