// Taken from:
// https://doc.cgal.org/latest/Surface_mesher/Surface_mesher_2mesh_an_implicit_function_8cpp-example.html
// https://doc.cgal.org/latest/Surface_mesher/index.html
// https://doc.cgal.org/latest/Mesh_3/index.html

#include <CGAL/Surface_mesh_default_triangulation_3.h>
#include <CGAL/Complex_2_in_triangulation_3.h>
#include <CGAL/IO/Complex_2_in_triangulation_3_file_writer.h>
#ifdef CGAL_FACETS_IN_COMPLEX_2_TO_TRIANGLE_MESH_H
  #include <CGAL/IO/facets_in_complex_2_to_triangle_mesh.h>
#else
  // NixOS currently has CGAL 4.11, not 4.12.  I guess 4.12 is needed
  // for this.  The #ifdef is unnecessary, but the header and call for
  // below are deprecated.
  #include <CGAL/IO/output_surface_facets_to_polyhedron.h>
#endif
#include <CGAL/make_surface_mesh.h>
#include <CGAL/Surface_mesh.h>
#include <CGAL/Implicit_surface_3.h>
#include <CGAL/IO/print_wavefront.h>
#include <CGAL/Polyhedron_3.h>

#include <iostream>
#include <fstream>
#include <limits>
#include <algorithm>

// Triangulation
typedef CGAL::Surface_mesh_default_triangulation_3 Tr;
typedef CGAL::Complex_2_in_triangulation_3<Tr> C2t3;

// Domain?
typedef Tr::Geom_traits GT;
typedef GT::Sphere_3 Sphere_3;
typedef GT::Point_3 Point_3;
typedef GT::Vector_3 Vector_3;
typedef GT::FT FT;
typedef FT (*Function)(Point_3);
typedef CGAL::Implicit_surface_3<GT, Function> Surface_3;
// how does this differ from CGAL::Implicit_mesh_domain_3<Function,K>?

typedef CGAL::Polyhedron_3<GT> Polyhedron;

FT sphere_function(Point_3 p) {
    Point_3 p2(p.x() + 0.1 * cos(p.x() * 20),
               p.y(),
               p.z() + 0.1 * sin(p.z() * 4));
    const FT x2=p2.x()*p2.x(), y2=p2.y()*p2.y(), z2=p2.z()*p2.z();
    return x2+y2+z2-1;
}

Vector_3 sphere_gradient(Point_3 p) {
	float A = 0.1;
	float B = 0.1;
	float F1 = 20;
	float F2 = 4;
	return Vector_3(2*(A*cos(p.x()*F1) + p.x())*(1 - A*F1*sin(p.x()*F1)),
					2*p.y(),
					2*(B*sin(p.z()*F2) + p.z())*(1 + B*F2*cos(p.z()*F2)));
}

FT spiral_function(Point_3 p) {
    float outer = 2.0;
    float inner = 0.4; // 0.9
    float freq = 20; // 10
    float phase = M_PI; // 3 * M_PI / 2;
    float thresh = 0.3;
    const FT d1 = p.y()*outer - inner * sin(p.x()*freq + phase);
    const FT d2 = p.z()*outer - inner * cos(p.x()*freq + phase);
    return std::max(sqrt(d1*d1 + d2*d2) - thresh,
                    p.x()*p.x() + p.y()*p.y() + p.z()*p.z() - 1.9*1.9);
}

Vector_3 spiral_gradient(Point_3 p) {
    float outer = 2.0;
    float inner = 0.4;
    float freq = 20;
    float phase = M_PI;
    float thresh = 0.3;
	// "block([%1,%2,%3,%4,%5,%6],%1:P+x*F,%2:cos(%1),%3:z*O-I*%2,%4:sin(%1),%5:y*O-I*%4,%6:1/sqrt(%5^2+%3^2),[((2*F*I*%3*%4-2*F*I*%2*%5)*%6)/2,O*%5*%6,O*%3*%6])"
	float v1 = phase + p.x() * freq;
	float v2 = cos(v1);
	float v3 = p.z() * outer - inner * v2;
	float v4 = sin(v1);
	float v5 = p.y() * outer - inner * v4;
	float v6 = 1.0 / sqrt(v5*v5 + v3*v3);
	return Vector_3(((2*freq*inner*v3*v4-2*freq*inner*v2*v5)*v6)/2,
					outer * v5 * v6,
					outer * v3 * v6);
}

int main() {
    Tr tr;            // 3D-Delaunay triangulation
    C2t3 c2t3 (tr);   // 2D-complex in 3D-Delaunay triangulation

    FT bounding_sphere_rad = 2.0;
    
    // defining the surface
    Surface_3 surface(spiral_function,             // pointer to function
                      Sphere_3(CGAL::ORIGIN,
                               bounding_sphere_rad*bounding_sphere_rad)); // bounding sphere

    std::string fname("spiral_thing4.obj");
    float angular_bound = 30;
    float radius_bound = 0.02;
    float distance_bound = 0.02;
    
    // Note that "2." above is the *squared* radius of the bounding sphere!
    // defining meshing criteria
    CGAL::Surface_mesh_default_criteria_3<Tr> criteria(
        angular_bound, radius_bound, distance_bound);

    std::cout << "angular bound = " << angular_bound << ", "
              << "radius bound = " << radius_bound << ", "
              << "distance bound = " << distance_bound << std::endl;

    std::cout << "Making surface mesh..." << std::endl;
    // meshing surface
    CGAL::make_surface_mesh(c2t3, surface, criteria, CGAL::Manifold_tag());
    std::cout << "Vertices: " << tr.number_of_vertices() << std::endl;

    // This didn't work on some calls instead of 'poly':
    //CGAL::Surface_mesh<Point_3> sm;
    Polyhedron poly;                                        
    std::cout << "Turning facets to triangle mesh..." << std::endl;
    
#ifdef CGAL_FACETS_IN_COMPLEX_2_TO_TRIANGLE_MESH_H
    CGAL::facets_in_complex_2_to_triangle_mesh(c2t3, poly);
#else
    CGAL::output_surface_facets_to_polyhedron(c2t3, poly);
#endif

    FT err = 0.0;
	FT inf = std::numeric_limits<FT>::infinity();
    for (Polyhedron::Point_iterator it = poly.points_begin();
         it != poly.points_end();
         ++it)
	{

		FT rate = 2e-6;
		FT f0 = abs(spiral_function(*it));
		FT f;
		for (int i = 0; i < 100; ++i) {
			f = spiral_function(*it);
			Vector_3 grad(spiral_gradient(*it));

			*it -= grad * rate * (f > 0 ? 1 : -1);
			/*
			std::cout << "Iter " << i << ": "
					  << "F(" << it->x() << "," << it->y() << "," << it->z()
					  << ")=" << f << ", F'=" << grad << std::endl;
			*/
		}
		//FT diff = (abs(f) - abs(f0)) / f0;
        /*
		std::cout << "F(" << it->x() << "," << it->y() << "," << it->z()
				  << "): " << f0 << " to " << f << std::endl;
        */
		
        err += f * f;
    }
    err = sqrt(err);
    std::cout << "RMS isosurface distance: " << err << std::endl;
    
    std::cout << "Mesh vertices: " << poly.size_of_vertices() << ", "
              << "facets: " << poly.size_of_facets() << std::endl;
    
    std::cout << "Writing to " << fname << "..." << std::endl;
    std::ofstream ofs(fname);
    CGAL::print_polyhedron_wavefront(ofs, poly);
}
