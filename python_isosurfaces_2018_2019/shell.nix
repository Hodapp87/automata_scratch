{ pkgs ? import <nixpkgs> {} }:

let python_with_deps = pkgs.python3.withPackages
      (ps: [ps.numpy ps.numpy-stl]);
in pkgs.stdenv.mkDerivation rec {
  name = "gfx_scratch";

  buildInputs = with pkgs; [ python_with_deps ];
}
