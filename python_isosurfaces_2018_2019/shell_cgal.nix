{ pkgs ? import <nixpkgs> {} }:

let stdenv = pkgs.stdenv;
in stdenv.mkDerivation rec {
  name = "cgal_scratch";

  buildInputs = with pkgs; [ cgal boost gmp mpfr ];
}

# g++ -lCGAL -lmpfr -lgmp mesh_an_implicit_function.cpp -o mesh_an_implicit_function.o
