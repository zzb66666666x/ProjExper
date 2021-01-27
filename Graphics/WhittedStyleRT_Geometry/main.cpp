#include "Scene.hpp"
#include "Sphere.hpp"
#include "Triangle.hpp"
#include "Light.hpp"
#include "Renderer.hpp"

// In the main function of the program, we create the scene (create objects and lights)
// as well as set the options for the render (image width and height, maximum recursion
// depth, field-of-view, etc.). We then call the render function().
int main()
{
    Scene scene(1280, 960);
    //C++17 feature: make_unique, return unique_ptr
    //the constructor of sphere will be called
    //unique ptr is a smart pointer which will avoid memory leak
    //that's because the unique_ptr is a class which uniquely owns the pointer 
    //when the object of unique_ptr is out of its life circle, the pointer inside it will also be released
    auto sph1 = std::make_unique<Sphere>(Vector3f(-1, 0, -12), 2);  //centered at (-1,0,12) with radius 2
    sph1->materialType = DIFFUSE_AND_GLOSSY;
    sph1->diffuseColor = Vector3f(0.815, 0.635, 0.231);

    auto sph2 = std::make_unique<Sphere>(Vector3f(0.5, -0.5, -8), 1.5);
    sph2->ior = 1.5;
    sph2->materialType = REFLECTION_AND_REFRACTION;

    //transfer the ownership of two pointers of sphere from unique_ptr in main() to that in the Scene object
    scene.Add(std::move(sph1));
    scene.Add(std::move(sph2));

    //generating triangles
    //two triangles here and the vertIndex shows how the vertices will be used to form a triangle
    Vector3f verts[4] = {{-5,-3,-6}, {5,-3,-6}, {5,-3,-16}, {-5,-3,-16}};
    uint32_t vertIndex[6] = {0, 1, 3, 1, 2, 3};
    //four coordinate vectors for one square shape
    Vector2f st[4] = {{0, 0}, {1, 0}, {1, 1}, {0, 1}};
    //pass in: vertices, index values, number of triangles, coordinate vectors for square mesh
    auto mesh = std::make_unique<MeshTriangle>(verts, vertIndex, 2, st);
    mesh->materialType = DIFFUSE_AND_GLOSSY;

    //transfer the ownership of triangle mesh to Scene object
    scene.Add(std::move(mesh));

    //two point light sources
    scene.Add(std::make_unique<Light>(Vector3f(-20, 70, 20), 0.5));
    scene.Add(std::make_unique<Light>(Vector3f(30, 50, -12), 0.5));    

    Renderer r;
    r.Render(scene);

    return 0;
}