#pragma once

#include "Object.hpp"

#include <cstring>

bool rayTriangleIntersect(const Vector3f& v0, const Vector3f& v1, const Vector3f& v2, const Vector3f& orig,
                          const Vector3f& dir, float& tnear, float& u, float& v)
{
    // TODO: Implement this function that tests whether the triangle
    // that's specified bt v0, v1 and v2 intersects with the ray (whose
    // origin is *orig* and direction is *dir*)
    // Also don't forget to update tnear, u and v.
    Vector3f E1 = v1 - v0;
    Vector3f E2 = v2 - v0;
    Vector3f S = orig - v0;
    Vector3f S1 = crossProduct(dir, E2);
    Vector3f S2 = crossProduct(S, E1);
    float coef = 1/(dotProduct(S1, E1));
    tnear = dotProduct(S2, E2) * coef;
    u = dotProduct(S1, S) * coef;
    v = dotProduct(S2, dir) * coef;
    if (u>0 && v>0 && (1-u-v)>0 && tnear>0){
        return true;
    }
    return false;
}

class MeshTriangle : public Object
{
public:
    MeshTriangle(const Vector3f* verts, const uint32_t* vertsIndex, const uint32_t& numTris, const Vector2f* st)
    {   //constrcutor
        uint32_t maxIndex = 0;
        for (uint32_t i = 0; i < numTris * 3; ++i)  //loop over the vertices
            if (vertsIndex[i] > maxIndex)
                maxIndex = vertsIndex[i];   
        maxIndex += 1;  //in this project, the maxIndex here is 4
        //main purpose below:
        //deep copy the data passed in to the owner, the object of class MeshTriangle
        vertices = std::unique_ptr<Vector3f[]>(new Vector3f[maxIndex]);
        memcpy(vertices.get(), verts, sizeof(Vector3f) * maxIndex);
        vertexIndex = std::unique_ptr<uint32_t[]>(new uint32_t[numTris * 3]);
        memcpy(vertexIndex.get(), vertsIndex, sizeof(uint32_t) * numTris * 3);
        numTriangles = numTris;     //in this project, the param is 2
        stCoordinates = std::unique_ptr<Vector2f[]>(new Vector2f[maxIndex]);
        memcpy(stCoordinates.get(), st, sizeof(Vector2f) * maxIndex);
    }

    bool intersect(const Vector3f& orig, const Vector3f& dir, float& tnear, uint32_t& index,
                   Vector2f& uv) const override
    {
        bool intersect = false;
        //check the intersection with the whole set of triangles
        for (uint32_t k = 0; k < numTriangles; ++k)
        {   //in this project, k = 0,1
            //use the index values here to find the three vertices of one triangle
            const Vector3f& v0 = vertices[vertexIndex[k * 3]];
            const Vector3f& v1 = vertices[vertexIndex[k * 3 + 1]];
            const Vector3f& v2 = vertices[vertexIndex[k * 3 + 2]];
            float t, u, v;
            if (rayTriangleIntersect(v0, v1, v2, orig, dir, t, u, v) && t < tnear)
            {   
                //update the tnear because the vertices may block each other
                tnear = t;
                //Moller-Trumbore algorithm will find the barycentric coordinate of intersection point
                uv.x = u;  
                uv.y = v;
                //updated the index to give out the real triangle of intersection
                index = k;
                intersect |= true;
            }
        }

        return intersect;
    }

    void getSurfaceProperties(const Vector3f&, const Vector3f&, const uint32_t& index, const Vector2f& uv, Vector3f& N,
                              Vector2f& st) const override
    {
        //read out vertives of triangle by index number (which was given by the hit payload)
        //note that if the light ray hits the mesh triangles, we will know the index of this triangle which was hit (by hit payload)
        const Vector3f& v0 = vertices[vertexIndex[index * 3]];
        const Vector3f& v1 = vertices[vertexIndex[index * 3 + 1]];
        const Vector3f& v2 = vertices[vertexIndex[index * 3 + 2]];
        Vector3f e0 = normalize(v1 - v0);
        Vector3f e1 = normalize(v2 - v1);
        //use cross product to find out the normal vector of this triangle
        N = normalize(crossProduct(e0, e1));
        const Vector2f& st0 = stCoordinates[vertexIndex[index * 3]];
        const Vector2f& st1 = stCoordinates[vertexIndex[index * 3 + 1]];
        const Vector2f& st2 = stCoordinates[vertexIndex[index * 3 + 2]];
        //use barycentric coordinate to interpolate the mesh coordinate st
        //remember that the mesh is composed of two triangles and has fout mesh coordinate: (0,0),(0,1),(1,0),(1,1)
        //we read out three of them by triangle and interpolate the st for this shading point within the mesh
        st = st0 * (1 - uv.x - uv.y) + st1 * uv.x + st2 * uv.y;
        //the st will be used to evaluate the diffuse color of triangle mesh
    }

    Vector3f evalDiffuseColor(const Vector2f& st) const override
    {
        //the pattern of output mesh will be decided here (without texture mapping, but mathmatically defined)
        float scale = 5;
        float pattern = (fmodf(st.x * scale, 1) > 0.5) ^ (fmodf(st.y * scale, 1) > 0.5);
        //lerp: (1-t)*a + t*b
        return lerp(Vector3f(0.815, 0.235, 0.031), Vector3f(0.937, 0.937, 0.231), pattern);
    }

    std::unique_ptr<Vector3f[]> vertices;
    uint32_t numTriangles;
    std::unique_ptr<uint32_t[]> vertexIndex;
    std::unique_ptr<Vector2f[]> stCoordinates;
};
