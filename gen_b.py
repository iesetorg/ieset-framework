#!/usr/bin/env python3
import os
G = "./hypotheses/growth"
S = "./hypotheses/steelman"
os.makedirs(G, exist_ok=True)
os.makedirs(S, exist_ok=True)

def wy(hid, c):
    p = os.path.join(G, hid + ".yaml")
    if os.path.exists(p):
        print("SKIP:", p); return
    open(p, "w").write(c)
    print("Wrote YAML:", p)

def ws(hid, c):
    p = os.path.join(S, hid + ".md")
    if os.path.exists(p):
        print("SKIP:", p); return
    open(p, "w").write(c)
    print("Wrote steelman:", p)
