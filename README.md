# automata_scratch

This is repo has a few projects that are related in terms of
high-level goal, but almost completely unrelated in their descent.

- `python_extrude_meshgen` is some Python code from around 2019
  September which did a sort of extrusion-based code generation.
  While this had some good results and some good ideas, the basic
  model was too limited in terms of the topology it could express.
- `libfive_subdiv` is a short project around 2021 July attempting to
  use the Python bindings of [libfive](https://www.libfive.com/), and
  automatic differentiation in
  [autograd](https://github.com/HIPS/autograd), to turn implicit
  surfaces to meshes which were suitable for subdivision via something
  like
  [OpenSubdiv](https://graphics.pixar.com/opensubdiv/overview.html)
  (in turn so that I could render with them without having to use
  insane numbers of triangles or somehow hide the obvious errors in
  the geometry).  Briefly, the process was to use edges with crease
  weights which were set based on the curvature of the implicit
  surface.  While I accomplished this process, it didn't fulfill the
  goal.  Shortly thereafter, I was re-reading
  [Massively Parallel Rendering of Complex Closed-Form Implicit Surfaces](https://www.mattkeeter.com/research/mpr/) - which, like libfive, is by Matt Keeter -
  and found a section I'd ignored on the difficulties of producing
  good meshes from isosurfaces for the sake of rendering.  I kept
  the code around because I figured it would be useful to refer to
  later, particularly for the integration with Blender.
- `blender_scraps` contains some scraps of Python code meant to be
  used inside of Blender's Python scripting - and it contains some
  conversions from another project, Prosha, for procedural mesh
  generation in Rust (itself based on learnings from
  `python_extrude_meshgen`).  These examples were proof-of-concept of
  generating meshes as control cages rather than as "final" meshes.
