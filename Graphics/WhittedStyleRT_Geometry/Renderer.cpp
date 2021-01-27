#include <fstream>
#include "Vector.hpp"
#include "Renderer.hpp"
#include "Scene.hpp"
#include <optional>

inline float deg2rad(const float &deg)
{ return deg * M_PI/180.0; }

// Compute reflection direction
Vector3f reflect(const Vector3f &I, const Vector3f &N)
{
    //params: 
    //I: the direction of input light ray
    //N: the normal vector the hit point
    //I and N are all normalized unit vectors
    //mathmatical fact behind:
    //the geometry here is a rhombus(菱形) with side length = 1
    //suppose the input ray is pointing out and forms a angle theta with normal
    //then cos(theta) = -dot(I, N)
    //since the middle line between input and output within the rhombus has length 2cos(theta)
    //it's then obvious that output is I + 2cos(theta)*N
    return I - 2 * dotProduct(I, N) * N;
}

// [comment]
// Compute refraction direction using Snell's law
//
// We need to handle with care the two possible situations:
//
//    - When the ray is inside the object
//
//    - When the ray is outside.
//
// If the ray is outside, you need to make cosi positive cosi = -N.I
//
// If the ray is inside, you need to invert the refractive indices and negate the normal N
// [/comment]
Vector3f refract(const Vector3f &I, const Vector3f &N, const float &ior)
{
    float cosi = clamp(-1, 1, dotProduct(I, N));
    float etai = 1, etat = ior;
    Vector3f n = N;
    if (cosi < 0) { cosi = -cosi; } else { std::swap(etai, etat); n= -N; }
    float eta = etai / etat;
    float k = 1 - eta * eta * (1 - cosi * cosi);
    return k < 0 ? 0 : eta * I + (eta * cosi - sqrtf(k)) * n;
}

// [comment]
// Compute Fresnel equation
//
// \param I is the incident view direction
//
// \param N is the normal at the intersection point
//
// \param ior is the material refractive index
// [/comment]
float fresnel(const Vector3f &I, const Vector3f &N, const float &ior)
{
    float cosi = clamp(-1, 1, dotProduct(I, N));
    float etai = 1, etat = ior;
    if (cosi > 0) {  std::swap(etai, etat); }
    // Compute sini using Snell's law
    float sint = etai / etat * sqrtf(std::max(0.f, 1 - cosi * cosi));
    // Total internal reflection
    if (sint >= 1) {
        return 1;
    }
    else {
        float cost = sqrtf(std::max(0.f, 1 - sint * sint));
        cosi = fabsf(cosi);
        float Rs = ((etat * cosi) - (etai * cost)) / ((etat * cosi) + (etai * cost));
        float Rp = ((etai * cosi) - (etat * cost)) / ((etai * cosi) + (etat * cost));
        return (Rs * Rs + Rp * Rp) / 2;
    }
    // As a consequence of the conservation of energy, transmittance is given by:
    // kt = 1 - kr;
}

// [comment]
// Returns true if the ray intersects an object, false otherwise.
//
// \param orig is the ray origin
// \param dir is the ray direction
// \param objects is the list of objects the scene contains
// \param[out] tNear contains the distance to the cloesest intersected object.
// \param[out] index stores the index of the intersect triangle if the interesected object is a mesh.
// \param[out] uv stores the u and v barycentric coordinates of the intersected point
// \param[out] *hitObject stores the pointer to the intersected object (used to retrieve material information, etc.)
// \param isShadowRay is it a shadow ray. We can return from the function sooner as soon as we have found a hit.
// [/comment]
std::optional<hit_payload> trace(
        const Vector3f &orig, const Vector3f &dir,
        const std::vector<std::unique_ptr<Object> > &objects)
{
    float tNear = kInfinity;
    std::optional<hit_payload> payload;
    for (const auto & object : objects) //objects: a std vector of unique_ptr which points to spheres or MeshTriangle
    {   //loop over every thing in the scene to check intersection
        float tNearK = kInfinity;
        uint32_t indexK;
        Vector2f uvK;
        //different intersect() will be called
        if (object->intersect(orig, dir, tNearK, indexK, uvK) && tNearK < tNear)
        {   //the passed in params indexK and uvK are only useful when the object is MeshTriangles
            payload.emplace();
            payload->hit_obj = object.get();
            payload->tNear = tNearK;
            payload->index = indexK;
            payload->uv = uvK;
            tNear = tNearK;
        }
    }

    return payload;
}

// [comment]
// Implementation of the Whitted-style light transport algorithm (E [S*] (D|G) L)
//
// This function is the function that compute the color at the intersection point (shading)
// of a ray defined by a position and a direction. Note that thus function is recursive (it calls itself).
//
// If the material of the intersected object is either reflective or reflective and refractive,
// then we compute the reflection/refraction direction and cast two new rays into the scene
// by calling the castRay() function recursively. When the surface is transparent, we mix
// the reflection and refraction color using the result of the fresnel equations (it computes
// the amount of reflection and refraction depending on the surface normal, incident view direction
// and surface refractive index).
//
// If the surface is diffuse/glossy we use the Phong illumation model to compute the color
// at the intersection point.
// [/comment]
Vector3f castRay(const Vector3f &orig, const Vector3f &dir, 
                const Scene& scene,int depth){
    if (depth > scene.maxDepth) {
        //during the first pass, the depth passed in is 0
        return Vector3f(0.0,0.0,0.0);
    }
    //default color at hit point (in case the light ray doesn't hit anything)
    Vector3f hitColor = scene.backgroundColor;
    //recursion stops if the light ray hits the background
    if (auto payload = trace(orig, dir, scene.get_objects()); payload)
    {
        //if the ray doen't hit an object, the payload will be empty <-- new feature of std::optional
        Vector3f hitPoint = orig + dir * payload->tNear;
        Vector3f N; // normal
        Vector2f st; // st coordinates
        payload->hit_obj->getSurfaceProperties(hitPoint, dir, payload->index, payload->uv, N, st);
        //if the hit_obj is MeshTriangle instance:
        //      input information contains: hitPoint, dir, index, uv
        //      output contains: normal vector N of this triangle, the interpolated mesh coordinate st 
        //if the hit_obj is sphere instance:
        //      input information contains: hitPoint, dir (the index and uv will be empty)
        //      output only contains the normal vector
        //the function getSurfaceProperties will treat these params accordingly 
        switch (payload->hit_obj->materialType) {
            //in this project, to simplify the problems, we only do shading at diffuse surface which is MeshTriangles (or background)
            //aka, the REFLECTION_AND_REFRACTION case is like a color-less glass ball  
            //and the REFLECTION case is like a color-less silver mirror
            case REFLECTION_AND_REFRACTION:
            {
                Vector3f reflectionDirection = normalize(reflect(dir, N));
                Vector3f refractionDirection = normalize(refract(dir, N, payload->hit_obj->ior));
                Vector3f reflectionRayOrig = (dotProduct(reflectionDirection, N) < 0) ?
                                             hitPoint - N * scene.epsilon :
                                             hitPoint + N * scene.epsilon;
                Vector3f refractionRayOrig = (dotProduct(refractionDirection, N) < 0) ?
                                             hitPoint - N * scene.epsilon :
                                             hitPoint + N * scene.epsilon;
                //recursion here
                //two ray going out: reflection and refraction
                Vector3f reflectionColor = castRay(reflectionRayOrig, reflectionDirection, scene, depth + 1);
                Vector3f refractionColor = castRay(refractionRayOrig, refractionDirection, scene, depth + 1);
                float kr = fresnel(dir, N, payload->hit_obj->ior);
                //use the fresnel coefficient to do linear combination of two color from reflection and refraction
                hitColor = reflectionColor * kr + refractionColor * (1 - kr);
                break;
            }
            case REFLECTION:
            {
                float kr = fresnel(dir, N, payload->hit_obj->ior);  //energy loss by fresnel's law
                Vector3f reflectionDirection = normalize(reflect(dir, N));
                Vector3f reflectionRayOrig = (dotProduct(reflectionDirection, N) < 0) ?
                                             hitPoint - N * scene.epsilon :
                                             hitPoint + N * scene.epsilon;
                hitColor = castRay(reflectionRayOrig, reflectionDirection, scene, depth + 1) * kr;
                break;
            }
            default:
            {
            //DIFFUSE_AND_GLOSSY
            //recursion stops here (aka. the light ray stops bouncing when hitting diffuse material or background)
            //loop over the light source and do shading (only in this case)
                // [comment]
                // We use the Phong illumation model in the default case. The phong model
                // is composed of a diffuse and a specular reflection component.
                // [/comment]
                Vector3f lightAmt = 0, specularColor = 0;
                Vector3f shadowPointOrig = (dotProduct(dir, N) < 0) ?
                                           hitPoint + N * scene.epsilon :
                                           hitPoint - N * scene.epsilon;
                // [comment]
                // Loop over all lights in the scene and sum their contribution up
                // We also apply the lambert cosine law
                // [/comment]
                for (auto& light : scene.get_lights()) {
                    Vector3f lightDir = light->position - hitPoint;
                    // square of the distance between hitPoint and the light
                    float lightDistance2 = dotProduct(lightDir, lightDir);  //squared distance
                    lightDir = normalize(lightDir);
                    float LdotN = std::max(0.f, dotProduct(lightDir, N));
                    // is the point in shadow, and is the nearest occluding object closer to the object than the light itself?
                    auto shadow_res = trace(shadowPointOrig, lightDir, scene.get_objects());
                    //trace the light ray to the light source to see if the shading point is (directly) illuminated
                    //in shadow: the hit payload is not empty and the squared distance between hit point and shading point is less than 
                    //           the distance from shading point to light source
                    bool inShadow = shadow_res && (std::pow(shadow_res->tNear,2) < lightDistance2);
                    //intensity * LdotN gives the result of lambert cosine law
                    lightAmt += inShadow ? 0 : light->intensity * LdotN;    
                    Vector3f reflectionDirection = reflect(-lightDir, N);
                    //specular term of bling-phong model
                    specularColor += inShadow ? 0: powf(std::max(0.f, -dotProduct(reflectionDirection, dir)),
                        payload->hit_obj->specularExponent) * light->intensity/lightDistance2;
                }

                hitColor = lightAmt * payload->hit_obj->evalDiffuseColor(st) * payload->hit_obj->Kd + specularColor * payload->hit_obj->Ks;
                break;
            }
        }
    }

    return hitColor;
}

// [comment]
// The main render function. This where we iterate over all pixels in the image, generate
// primary rays and cast these rays into the scene. The content of the framebuffer is
// saved to a file.
// [/comment]
void Renderer::Render(const Scene& scene)
{   
    // framebuffer is a std::vector of Vector3f (RGB info. inside)
    // use a 1D vector to represent 2D image pixel array
    std::vector<Vector3f> framebuffer(scene.width * scene.height);

    float scale = std::tan(deg2rad(scene.fov * 0.5f));  // tan(pi/4) = 1 since scere.fov = 90 degree
    float imageAspectRatio = scene.width / (float)scene.height; // width/height

    // Use this variable as the eye position to start your rays.
    Vector3f eye_pos(0);    //eye_pos is the origin
    int m = 0;
    for (int j = 0; j < scene.height; ++j)
    {
        for (int i = 0; i < scene.width; ++i)
        {
            // generate primary ray direction
            float x;
            float y;
            // TODO: Find the x and y positions of the current pixel to get the direction
            // vector that passes through it.
            // Also, don't forget to multiply both of them with the variable *scale*, and
            // x (horizontal) variable with the *imageAspectRatio*
            //default image plane: [-1,1]*aspect_ratio x [-1,1], z = -d 
            // this plane is equivalent with [-1,1]*aspect_ratio/d x [-1,1]/d, z = -1        
            x = imageAspectRatio*((i+0.5)/(scene.width/2) - 1) * scale;
            y = ((j+0.5)/(scene.height/2)-1) * scale * -1;
            //then we have direction = (u,v,-d) = (x,y,-1) where x = u/d, y = v/d and scale = 1/d = tan(fov/2)
            Vector3f dir = Vector3f(x, y, -1); // Don't forget to normalize this direction!
            dir = normalize(dir);
            framebuffer[m++] = castRay(eye_pos, dir, scene, 0); //m++: first take its value and add 1
        }
        UpdateProgress(j / (float)scene.height);
    }

    // save framebuffer to file
    // ppm file: ppm is a useful image format(Portable Pixelmap)
    // what's inside ppm?
    // 　　P6\n
    // 　　width height\n
    // 　　255\n
    // 　　rgbrgb...
    // use fopen with binary write mode
    FILE* fp = fopen("binary.ppm", "wb");
    (void)fprintf(fp, "P6\n%d %d\n255\n", scene.width, scene.height);
    for (auto i = 0; i < scene.height * scene.width; ++i) {
        static unsigned char color[3];
        color[0] = (char)(255 * clamp(0, 1, framebuffer[i].x));
        color[1] = (char)(255 * clamp(0, 1, framebuffer[i].y));
        color[2] = (char)(255 * clamp(0, 1, framebuffer[i].z));
        fwrite(color, 1, 3, fp);
    }
    fclose(fp);    
}
