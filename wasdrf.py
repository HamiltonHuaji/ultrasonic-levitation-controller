#!/usr/bin/env python3

import tty, sys, termios
from libcontroller import GPIOController
import numpy as np
import time, math, traceback

fstr = '''
      15    13             
      {}    {}             
17 {}            {} 11     
           {}              
  03 {}            {} 09   
          {}    {}         
          05    07         
                           
      06    04             
      {}    {}             
08 {}            {} 02     
           {}              
  10 {}            {} 16   
          {}    {}         
          12    14         
===========================
'''

def output(phase):
    return fstr.format(
        phase[15],phase[13],
        phase[17],phase[11],
        phase[1],
        phase[3],phase[9],
        phase[5],phase[7],
        phase[6],phase[4],
        phase[8],phase[2],
        phase[0],
        phase[10],phase[16],
        phase[12],phase[14]
    )

λ = 1
cos225=0.9238795325112867
sin225=0.3826834323650898
cos24384=0.9107994336773200
sin24384=0.4128491148265588

R = 6.55*λ

spos = np.array([
    (+0.000000000000000, +0.000000000000000, -1.000000), (+0.000000000000000, +0.000000000000000, 1.000000),# 00,01
    (+cos225 * sin24384, +sin225 * sin24384, -cos24384), (-cos225 * sin24384, -sin225 * sin24384, cos24384),# 02,03
    (+sin225 * sin24384, +cos225 * sin24384, -cos24384), (-sin225 * sin24384, -cos225 * sin24384, cos24384),# 04,05
    (-sin225 * sin24384, +cos225 * sin24384, -cos24384), (+sin225 * sin24384, -cos225 * sin24384, cos24384),# 06,07
    (-cos225 * sin24384, +sin225 * sin24384, -cos24384), (+cos225 * sin24384, -sin225 * sin24384, cos24384),# 08,09
    (-cos225 * sin24384, -sin225 * sin24384, -cos24384), (+cos225 * sin24384, +sin225 * sin24384, cos24384),# 10,11
    (-sin225 * sin24384, -cos225 * sin24384, -cos24384), (+sin225 * sin24384, +cos225 * sin24384, cos24384),# 12,13
    (+sin225 * sin24384, -cos225 * sin24384, -cos24384), (-sin225 * sin24384, +cos225 * sin24384, cos24384),# 14,15
    (+cos225 * sin24384, -sin225 * sin24384, -cos24384), (-cos225 * sin24384, +sin225 * sin24384, cos24384),# 16,17
], dtype=np.float32) * R

#                   0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17
poffset = np.array([0,  8,  0,  8,  0,  8,  0,  8,  0,  8,  0,  8,  0,  8,  0,  8,  0,  8], dtype = np.int8)
qoffset = np.array([1,  1,  8, -6,  6, -4,  2,  0, -3,  6, -6,  8, -4,  6,  0,  2,  6, -3], dtype = np.int8)

xyz = np.zeros([3])
def distance():
    rs = spos - xyz
    r2s = rs * rs
    r2ds = np.sum(r2s, axis=-1)
    return 16 * (np.sqrt(r2ds) - R)

old = distance()
def rawinput():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno(), termios.TCSANOW)
        ch = sys.stdin.read(1)
        sys.stdout.write(ch)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

r=None
controller = GPIOController()
def interpolate(vstart, vend):
    diff = vstart - vend
    r2sqrt = int(np.sqrt(np.sum(diff*diff)))
    for i in range(r2sqrt):
        yield vstart * (1 - i / r2sqrt) + vend * (i /r2sqrt)
    yield vend
def submit(b):
    controller.fill_buffer(b.astype(np.int32))
    controller.swap_buffer()

'''
          z+  z-
+---+---+---+---+
| q | W | E | R |
+---+---+---+---+
| A | S | D | y
+---+---+---+
      x
'''

xrate = 0.1
yrate = 0.1
zrate = 0.2

# submit(old.astype(np.int8))

while True:
    r = rawinput()
    print('\b', end="")
    if r=='a':
        xyz[0] -= xrate
    elif r=='d':
        xyz[0] += xrate
    elif r=='s':
        xyz[1] -= yrate
    elif r=='w':
        xyz[1] += yrate
    elif r=='r':
        xyz[2] += zrate
    elif r=='f':
        xyz[2] -= zrate
    elif r=='0':
        xyz = np.zeros([3])
    elif r=='q':
        break
    new = distance()
    legacy = np.rint(old)
    for v in interpolate(old, new):
        u = np.rint(v)
        if (u != legacy).any():
            print(u+poffset+qoffset, xyz)
            submit(u + poffset + qoffset)
        time.sleep(0.1)
    old = new