//
// Created by goksu on 2/25/20.
//
#include "Renderer.hpp"

inline float deg2rad(const float& deg) { return deg * M_PI / 180.0; }

const float EPSILON = 0.00001;

// The main render function. This where we iterate over all pixels in the image,
// generate primary rays and cast these rays into the scene. The content of the
// framebuffer is saved to a file.
void Renderer::Render(const Scene& scene)
{
    std::vector<Vector3f> framebuffer(scene.width * scene.height);
    float scale = tan(deg2rad(scene.fov * 0.5));
    float imageAspectRatio = scene.width / (float)scene.height;
    Vector3f eye_pos(278, 273, -800);

    bool multithread = true;

    if(!multithread)
    {
        // change the spp value to change sample ammount
        spp = 128;
        std::cout << "SPP: " << spp << "\n";
        int m = 0;
        for (uint32_t j = 0; j < scene.height; ++j) {
            for (uint32_t i = 0; i < scene.width; ++i) {
                // generate primary ray direction
                float x = (2 * (i + 0.5) / (float)scene.width - 1) *
                        imageAspectRatio * scale;
                float y = (1 - 2 * (j + 0.5) / (float)scene.height) * scale;

                Vector3f dir = normalize(Vector3f(-x, y, 1));
                for (int k = 0; k < spp; k++){
                    framebuffer[m] += scene.castRay(Ray(eye_pos, dir), 0) / spp; 
                    //std::cout<<framebuffer[m]<<"\n"; 
                }
                m++;
                }
                UpdateProgress(j/(float)scene.height);
            }
        UpdateProgress(1.f);
    }
    else{
        spp = 1024;
        int m = 0;
        int spp_each = spp/NUM_THREADS;
        std::vector<Vector3f> framebuffer0(scene.width * scene.height);
        std::vector<Vector3f> framebuffer1(scene.width * scene.height);
        std::vector<Vector3f> framebuffer2(scene.width * scene.height);
        std::vector<Vector3f> framebuffer3(scene.width * scene.height);
        std::thread th0(thread_task, &framebuffer0, spp_each, spp, scene, eye_pos);
        std::thread th1(thread_task, &framebuffer1, spp_each, spp, scene, eye_pos);
        std::thread th2(thread_task, &framebuffer2, spp_each, spp, scene, eye_pos);
        std::thread th3(thread_task, &framebuffer3, spp_each, spp, scene, eye_pos);
        th0.join();
        th1.join();
        th2.join();
        th3.join();
        //collect information among frame buffers 
        for (uint32_t j = 0; j < scene.height; ++j) {
            for (uint32_t i = 0; i < scene.width; ++i) {
                framebuffer[m] = framebuffer0[m]+framebuffer1[m]+framebuffer2[m]+framebuffer3[m];
                m++;
            }
        }
    }
    // save framebuffer to file
    // FILE* fp = fopen("../images/binary_784x784_spp32.ppm", "wb");
    // FILE* fp = fopen("../images/binary_200x200_spp64.ppm", "wb");
    // FILE* fp = fopen("../images/binary_300x300_spp1024.ppm", "wb");
    // FILE* fp = fopen("../images/binary_84x84_spp64_thread4.ppm", "wb");
    FILE* fp = fopen("../images/binary_784x784_spp1024_thread4.ppm", "wb");
    (void)fprintf(fp, "P6\n%d %d\n255\n", scene.width, scene.height);
    for (auto i = 0; i < scene.height * scene.width; ++i) {
        static unsigned char color[3];
        color[0] = (unsigned char)(255 * std::pow(clamp(0, 1, framebuffer[i].x), 0.6f));
        color[1] = (unsigned char)(255 * std::pow(clamp(0, 1, framebuffer[i].y), 0.6f));
        color[2] = (unsigned char)(255 * std::pow(clamp(0, 1, framebuffer[i].z), 0.6f));
        fwrite(color, 1, 3, fp);
    }
    fclose(fp);    
}

void thread_task(std::vector<Vector3f> * framebuffer_ptr, int num_spp, int spp_tot, 
                           Scene scene, Vector3f eye_pos)
{
    int m = 0;
    float scale = tan(deg2rad(scene.fov * 0.5));
    float imageAspectRatio = scene.width / (float)scene.height;
    for (uint32_t j = 0; j < scene.height; ++j) {
        for (uint32_t i = 0; i < scene.width; ++i) {
            float x = (2 * (i + 0.5) / (float)scene.width - 1) *
                    imageAspectRatio * scale;
            float y = (1 - 2 * (j + 0.5) / (float)scene.height) * scale;
            Vector3f dir = normalize(Vector3f(-x, y, 1));
            for (int k=0; k<num_spp; k++){
                (*framebuffer_ptr)[m] += scene.castRay(Ray(eye_pos, dir), 0) / spp_tot;
                //std::cout<<(*framebuffer_ptr)[m]<<"\n";
            }
            m++;
        }   
    }
}