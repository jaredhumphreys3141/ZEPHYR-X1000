"""Integral-carrier FRS: cartridge web is the seat. Nose must stay on the seat at full float:
hole r_h = 5.5 (Ø11, 0.5 radial to Ø10 shaft), float ±0.2 -> nose inner r >= 5.7; nose r 5.75-6.15."""
import numpy as np
D=10e-3; L=1.8e-3; c_cold=0.025e-3; ri=5e-3+c_cold
r_h, flt, n0, n1 = 5.5, 0.2, 5.75, 6.15
print(f"nose inner edge at full float: {n0-flt:.2f} mm vs hole {r_h} -> overlap margin {n0-flt-r_h:.2f} mm")
rn=(n0+n1)/2e3
clos=lambda dp: 5.9e-6*dp/10
def leak(dp,c,rho,mu):
    A=np.pi*D*c; a=1.5*rho/2/A**2; b=12*mu*L/(np.pi*D*c**3); return (-b+np.sqrt(b*b+4*a*dp))/(2*a)
for f,(rho,mu) in {"HTP":(1390,1.25e-3),"IPA":(786,2.0e-3)}.items():
    print(f, "new:", " | ".join(f"{dp} bar {leak(dp*1e5,c_cold-clos(dp),rho,mu)*1e6:.1f}" for dp in (5.5,10,15)),
          " worn(0.040):", " | ".join(f"{leak(dp*1e5,0.040e-3-clos(dp),rho,mu)*1e6:.1f}" for dp in (5.5,10,15)))
for dp in (5.5,10,15):
    F=dp*1e5*np.pi*(rn**2-ri**2); S=0.15*F; c=c_cold-clos(dp); K=0.25*np.pi*D*L*dp*1e5/c
    print(f"dp {dp}: nose load {F:.1f} N, contact p {F/(np.pi*((n1/1e3)**2-(n0/1e3)**2))/1e6:.1f} MPa, slide {S:.1f} N, lag {S/K*1e6:.1f} um ({S/K/c*100:.0f}% of c)")
    rpm=30000*np.sqrt(dp/10); U=rpm*np.pi/30*5e-3; Td=1.25e-3*U/c*np.pi*D*L*5e-3
    print(f"        friction torque {S*rn*1e3:.1f} mN.m vs drag {Td*1e3:.2f} -> {S*rn/Td:.0f}x")
print("seat tilt 0.01 over r 8.2 -> bore tilt", round(0.01/8.2*1.8e3,1), "um across the land")
