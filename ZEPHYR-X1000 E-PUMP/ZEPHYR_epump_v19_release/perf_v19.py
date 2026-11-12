"""ZEPHYR e-pump v19 performance check against the vehicle requirements (1.1 kN, 20 s, Pc 24 bar, O/F 4.0, 8S ~28 V late)."""
import json, math
d=json.load(open("/home/claude/rel/data/design_v7.json")); ind={x["name"]:x for x in json.load(open("/home/claude/rel/data/inducer_designs_v16.json"))}
Pc=24.0; V_late=28.0
mot={"HTP":dict(Kv=1300,R=0.016),"IPA":dict(Kv=1730,R=0.016*(1300/1730)**2)}   # R: retailer listing (1300Kv); 1730Kv scaled
R_esc=0.006; I0=4.0
case={"HTP":dict(rho=1390,leak=7.0e-6,dp=35.0,pv=0.67e3),"IPA":dict(rho=786,leak=5.0e-6,dp=31.0,pv=4.4e3)}
out={}
for V in ("HTP","IPA"):
    D=d[V]; c=case[V]; m=mot[V]; n=D["rpm"]; w=n*math.pi/30
    Q=D["mdot"]/c["rho"]
    P_hyd=Q*D["dp_bar"]*1e5
    P_imp=D["P_imp_kW"]*1e3
    P_leak=c["leak"]*D["dp_bar"]*1e5/D["eta"]           # FRS bleed flow is pumped then returned to tank
    P_brg=30.0; P_seal=10.0                              # 708 set under ~1 kN thrust + grease; PTFE lip
    P_shaft=P_imp+P_leak+P_brg+P_seal
    T=P_shaft/w; Kt=60/(2*math.pi*m["Kv"]); I=T/Kt+I0
    V_need=(w*Kt+I*(m["R"]+R_esc))/0.97
    P_cu=I*I*m["R"]; P_el=V_need*I
    # NPSH: launch (1 atm + 0.3 m liquid at 4.5 g), design assumption (60 kPa), burnout estimate (~41 kPa ambient, no head)
    def npsha(p): return (p-c["pv"])/(c["rho"]*9.81)
    NPSHr=ind[V]["NPSHr_inducer_m"]
    out[V]=dict(rpm=n, mdot=D["mdot"], dp_bar=D["dp_bar"], eta=D["eta"], P_hyd_W=P_hyd, P_shaft_W=P_shaft, extra_W=P_leak+P_brg+P_seal,
                torque_Nm=T, I_A=I, V_needed=V_need, V_margin=V_late-V_need, P_elec_W=P_el, P_cu_W=P_cu,
                dT_motor_20s_K=P_cu*20/(530*0.5), NPSH_margin={k:npsha(p)/NPSHr for k,p in (("launch",101.3e3+c["rho"]*44*0.3),("design 60 kPa",60e3),("burnout ~41 kPa",41e3))},
                inj_budget_bar=D["dp_bar"]-Pc)
    o=out[V]
    print(f"\n{V}: {n:,.0f} rpm, {D['mdot']} kg/s, {D['dp_bar']:.1f} bar, eta {D['eta']:.2f}")
    print(f"  shaft power {P_shaft/1e3:.2f} kW (impeller {P_imp/1e3:.2f} + bleed/bearing/seal {o['extra_W']:.0f} W); torque {T:.3f} N.m")
    print(f"  motor {m['Kv']}Kv: {I:.0f} A, needs {V_need:.1f} V vs {V_late} V late-burn -> margin {o['V_margin']:+.1f} V; elec {P_el/1e3:.2f} kW; copper {P_cu:.0f} W (~{o['dT_motor_20s_K']:.0f} K bulk rise in 20 s)")
    print("  NPSH margin (NPSHa/NPSHr): "+", ".join(f"{k} {v:.1f}x" for k,v in o["NPSH_margin"].items()))
    print(f"  pressure left above Pc for cooling/injector/catalyst: {o['inj_budget_bar']:.1f} bar")
# venturi-test worst cases (from handoff)
for V,n,P,kv in (("HTP",33700,2700,1300),("IPA",40400,1800,1730)):
    w=n*math.pi/30; Kt=60/(2*math.pi*kv); T=(P+60)/w; I=T/Kt+I0; R=mot[V]["R"]
    print(f"{V} venturi worst: {n} rpm, {I:.0f} A, needs {(w*Kt+I*(R+R_esc))/0.97:.1f} V")
# IPA regen-jacket check: 10 m/s coolant (RPA fix) + injector 20% Pc
Q=0.10/786; A=Q/10; Dh=1.0e-3; L=0.10; v=10; f=0.03
dp_jacket=(f*L/Dh+1.5)*786*v*v/2/1e5; dp_inj=0.2*Pc
print(f"\nIPA budget: jacket at 10 m/s ~{dp_jacket:.1f} bar (Dh 1 mm, 100 mm, +1.5 heads) + injector {dp_inj:.1f} bar = {dp_jacket+dp_inj:.1f} vs {31-Pc:.1f} available")
for k in (1.03,1.05):
    print(f"  IPA +{(k-1)*100:.0f}% rpm -> {37563*k:,.0f} rpm, dp {31*k*k:.1f} bar, power x{k**3:.2f}")
tot=sum(out[V]["P_elec_W"] for V in out); I_tot=sum(out[V]["I_A"] for V in out)
print(f"\nBattery: {tot/1e3:.2f} kW electrical, ~{I_tot*out['HTP']['V_needed']/V_late:.0f}-{I_tot:.0f} A from the pack, {tot*20/3600:.0f} Wh per 20 s burn (+ESC losses ~5%)")
print(f"Engine: {0.4+0.1:.1f} kg/s at 1.1 kN -> implied Isp {1100/(0.5*9.81):.0f} s; O/F {0.4/0.1:.1f}")
json.dump(out,open("perf_v19.json","w"),indent=1,default=float)
