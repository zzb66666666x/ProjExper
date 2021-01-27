#pragma once
#include "Scene.hpp"

struct hit_payload
{
    //data needed for checking light hitting objects
    float tNear;
    uint32_t index;
    Vector2f uv;
    Object* hit_obj;    //a Object pointer which can be assigned with the address of trinagles or spheres
};

class Renderer
{//no member variable for data, no customized constructors
public:
    void Render(const Scene& scene);

private:
};