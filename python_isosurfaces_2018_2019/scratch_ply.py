#!/usr/bin/env python

import math

def f1(T, I, O, P, F):
    return lambda x: (x, (T + I * math.sin(P + x*F)) / O, (I * math.cos(P + x*F)) / O)

def f2(T, I, O, P, F):
    return lambda x: (x, -(T - I * math.sin(P + x*F)) / O, (I * math.cos(P + x*F)) / O)

f = f2(O=2.0, I=0.4, F=20, P=math.pi, T=0.3)
print("ply")
print("format ascii 1.0")
r = range(-400, 400)
print("element vertex %d" % (len(r)))
print("property float32 x")
print("property float32 y")
print("property float32 z")
print("end_header")
for xi in r:
    print("%f %f %f" % f(float(xi) / 200))
