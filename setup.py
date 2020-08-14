#!/usr/bin/env python3
from setuptools import setup, Extension
import pybind11
setup(
    name="libcontroller",
    version="0.0.1",
    setup_requires=["pybind11"],
    ext_modules=[
        Extension("libcontroller", ["controller.cpp"],
                  include_dirs=[pybind11.get_include()], language='c++',
                  extra_compile_args=["-std=c++2a", "-fvisibility=hidden", "-funroll-loops"],
                  libraries=["wiringPi"])
    ],
    author="HamiltonHuaji",
    description="Ultrasonic",
    python_requires=">=3.7",
)