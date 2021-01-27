#pragma once

#include "Vector.hpp"

//position for light source and intensity
//intensity is a 3D vector which contains the intensity info. for 3 color channels
class Light
{  
public:
    Light(const Vector3f& p, const Vector3f& i)
        : position(p)
        , intensity(i)
    {}
    virtual ~Light() = default;
    Vector3f position;
    Vector3f intensity;
};
