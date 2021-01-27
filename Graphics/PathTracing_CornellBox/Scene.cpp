//
// Created by Göksu Güvendiren on 2019-05-14.
//

#include "Scene.hpp"


void Scene::buildBVH() {
    printf(" - Generating BVH...\n\n");
    this->bvh = new BVHAccel(objects, 1, BVHAccel::SplitMethod::NAIVE);
}

Intersection Scene::Intersect(const Ray &ray) const
{
    //basic work flow:
    //scene.bvh.Intersect -> MeshTriangles.getIntersection -> 
    //MeshTriangle.bvh.Intersect -> Triangle.getIntersection -> return info
    return this->bvh->Intersect(ray);
}

void Scene::sampleLight(Intersection &pos, float &pdf) const
{
    float emit_area_sum = 0;
    for (uint32_t k = 0; k < objects.size(); ++k) {
        if (objects[k]->hasEmit()){
            emit_area_sum += objects[k]->getArea();
        }
    }
    float p = get_random_float() * emit_area_sum;
    emit_area_sum = 0;
    for (uint32_t k = 0; k < objects.size(); ++k) {
        if (objects[k]->hasEmit()){
            emit_area_sum += objects[k]->getArea();
            if (p <= emit_area_sum){
                //here the objects[k] refers to the class MeshTriangle
                objects[k]->Sample(pos, pdf);
                break;
            }
        }
    }
}

Vector3f Scene::castRay(const Ray &ray, int depth) const
{
    // TO DO Implement Path Tracing Algorithm here
    Intersection inter = Intersect(ray);
    if (inter.happened){
        //hit light source directly (here, the light source refers to the MeshTriangle with emitting material)
        if (inter.obj->hasEmit()){
            return inter.m->getEmission();
        }
        //hit diffuse material
        Vector3f L_dir = Vector3f(0);
        Vector3f L_indir = Vector3f(0);
        //variables in inter
        Vector3f wo = normalize(-ray.direction);
        Material * m = inter.m;
        Vector3f N = normalize(inter.normal);
        Vector3f p = inter.coords;

        float pdf_light = 0;
        Intersection light_inter;
        sampleLight(light_inter, pdf_light);
        Vector3f x = light_inter.coords;
        //ws is pointing from shading point to light source
        //ws is a special kind of input which directly comes from source
        Vector3f ws = normalize(x - p);
        Ray test_ray = Ray(p, ws);
        Intersection test_inter = Intersect(test_ray);
        if ((test_inter.coords - x).norm() < 0.1){
            //not blocked by objects
            //std::cout<<"check point\n";
            Vector3f N_light = light_inter.normal;
            Vector3f emit = light_inter.emit;
            float cos_shading_point = std::max(0.0f, dotProduct(ws, N));
            float cos_light_source = std::max(0.0f, dotProduct(-ws, N_light));
            L_dir = emit * m->eval(ws, wo, N) * cos_shading_point * cos_light_source
                    / (x-p).norm2()  / pdf_light;
        }
        //test Russian Roulette
        if (get_random_float()<RussianRoulette){
            //compute indirect light source
            //std::cout<<"check point\n";
            Vector3f wi = m->sampleHemisphere(wo, N);
            Ray cast_out_ray(p,wi);
            Intersection cast_ray_inter = Intersect(cast_out_ray);
            if (cast_ray_inter.happened && !(cast_ray_inter.obj->hasEmit())){
                Vector3f nextShadeColor = castRay(cast_out_ray, depth+1);
                L_indir = nextShadeColor * m->eval(wi, wo, N) * dotProduct(wi, N) 
                        / m->pdf(wi,wo,N) / RussianRoulette;
            }
        }
        return L_dir + L_indir;
    }
    return Vector3f(0);
}