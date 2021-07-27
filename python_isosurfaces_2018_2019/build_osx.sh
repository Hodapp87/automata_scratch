#!/bin/sh

g++ -L/usr/local/Cellar/cgal/4.12/lib -I/usr/local/Cellar/cgal/4.12/include \
    -L/usr/local/Cellar/gmp/6.1.2_2/lib \
    -L/usr/local/Cellar/mpfr/4.0.1/lib \
    -L/usr/local/Cellar/boost/1.67.0_1/lib \
    -DCGAL_CONCURRENT_MESH_3 \
    -lCGAL -lgmp -lmpfr -lboost_thread-mt \
    ./mesh_an_implicit_function.cpp \
    -o mesh_an_implicit_function.o
