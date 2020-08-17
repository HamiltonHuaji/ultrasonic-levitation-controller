#!/usr/bin/env python3

from libcontroller import GPIOController
import time, math, traceback
from functools import wraps
import numpy as np

def end_session(end="\n"):
    print("", end=end)

'''
l: 输出所有相位
w/a/s/d/q/e: 有控制算法之后的前后左右
x 100: 结束一段记录, 并在100ms内线性插值完成. 同时清理action
c +1 +2,2: 1口增加1, 2口增加2
s 1=10: 1口设置为10, 不提交
p: 提交现有buffer
t: 退出
'''

buffer = np.zeros([18])
action = np.zeros([18])
basetime = time.time()
line = 1
def interpolate(percent = 1):
    return buffer + action * percent

try:
    controller = GPIOController()
    def submit(b=buffer):
        controller.fill_buffer(b.astype(np.int32))
        controller.swap_buffer()
    while True:
        try:
            command = input("{:.4f}%{}>>>".format(time.time() - basetime, line))
            line += 1
            if command == "":
                continue
            tokens = command.split()
            t = tokens[0]; opt = tokens[1:]
            if t == "l":
                print(buffer)
            elif t in "wasdqe":
                pass
            elif t == "c":
                for o in opt:
                    op = o[0]
                    pin, val = o[1:].split(",")[0:2]
                    action[int(pin)] += (1 if op=="+" else -1) * int(val)
            elif t == "s":
                for o in opt:
                    pin, val = o.split("=")[0:2]
                    if pin.isdigit():
                        buffer[int(pin)] = int(val)
                    else:
                        pinmin, pinmax = pin.split("~")
                        for p in range(int(pinmin), int(pinmax)):
                            buffer[p] = int(val)
            elif t == "p":
                submit()
            elif t == "sp":
                for o in opt:
                    pin, val = o.split("=")[0:2]
                    if pin.isdigit():
                        buffer[int(pin)] = int(val)
                    else:
                        pinmin, pinmax = pin.split("~")
                        for p in range(int(pinmin), int(pinmax)):
                            buffer[p] = int(val)
                submit()
            elif t == "x":
                starttime = time.time()
                lefttime = float(opt[0])
                while True:
                    percent = (time.time() - starttime) * 1000.0 / lefttime
                    submit(interpolate(percent))
                    if percent > 1:
                        break
                    time.sleep(0.001)
                buffer += action
                action = np.zeros([18])
            elif t == "t":
                end_session()
                break
            else:
                print("unknown: {}".format(command.encode('utf-8')))
        except EOFError as e:
            end_session()
            break
        except Exception as e:
            traceback.print_exc()
except KeyboardInterrupt as k:
    end_session()
