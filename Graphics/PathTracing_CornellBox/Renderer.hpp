//
// Created by goksu on 2/25/20.
//
#pragma once

#include <thread>
#include <fstream>
#include "Scene.hpp"
#include "Vector.hpp"

#define NUM_THREADS 4

class Renderer
{
public:
    void Render(const Scene& scene);
private:
    int spp;
};

void thread_task(std::vector<Vector3f> * framebuffer_ptr, int num_spp, int spp_tot,
                     Scene scene, Vector3f eye_pos);