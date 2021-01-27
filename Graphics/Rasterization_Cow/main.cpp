#include <iostream>
#include <opencv2/opencv.hpp>

#include "global.hpp"
#include "rasterizer.hpp"
#include "Triangle.hpp"
#include "Shader.hpp"
#include "Texture.hpp"
#include "OBJ_Loader.h"

using std::max;
using std::pow;
using std::sqrt;

Eigen::Matrix4f get_view_matrix(Eigen::Vector3f eye_pos)
{
    Eigen::Matrix4f view = Eigen::Matrix4f::Identity();

    Eigen::Matrix4f translate;
    translate << 1,0,0,-eye_pos[0],
                 0,1,0,-eye_pos[1],
                 0,0,1,-eye_pos[2],
                 0,0,0,1;

    view = translate*view;

    return view;
}

Eigen::Matrix4f get_model_matrix(float angle)
{
    Eigen::Matrix4f rotation;
    angle = angle * MY_PI / 180.f;
    rotation << cos(angle), 0, sin(angle), 0,
                0, 1, 0, 0,
                -sin(angle), 0, cos(angle), 0,
                0, 0, 0, 1;

    Eigen::Matrix4f scale;
    scale << 2.5, 0, 0, 0,
              0, 2.5, 0, 0,
              0, 0, 2.5, 0,
              0, 0, 0, 1;

    Eigen::Matrix4f translate;
    translate << 1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1;

    return translate * rotation * scale;
}

Eigen::Matrix4f get_projection_matrix(float eye_fov, float aspect_ratio, float zNear, float zFar)
{
    // TODO: Use the same projection matrix from the previous assignments
    Eigen::Matrix4f projection = Eigen::Matrix4f::Identity();
    float t = tan(eye_fov/2*MY_PI/180) * (-zNear);
    float b = -t;
    float r = aspect_ratio * t;
    float l = -r;
    Eigen::Matrix4f trans;
    Eigen::Matrix4f scale;
    trans<<1,0,0,(-(r+l)/2),
           0,1,0,(-(t+b)/2),
           0,0,1,(-(zNear+zFar)/2),
           0,0,0,1;
    scale<<(2/(r-l)),0,0,0,
           0,(2/(t-b)),0,0,
           0,0,(2/(zNear-zFar)),0,
           0,0,0,1;
    Eigen::Matrix4f ortho = scale * trans;
    Eigen::Matrix4f persp;
    persp<<zNear, 0,0,0,
           0,zNear,0,0,
           0,0,zFar+zNear,-(zFar*zNear),
           0,0,1,0;
    projection = ortho * persp;
    return projection;
}


Eigen::Vector3f vertex_shader(const vertex_shader_payload& payload)
{
    return payload.position;
}

Eigen::Vector3f normal_fragment_shader(const fragment_shader_payload& payload)
{
    Eigen::Vector3f return_color = (payload.normal.head<3>().normalized() + Eigen::Vector3f(1.0f, 1.0f, 1.0f)) / 2.f;
    Eigen::Vector3f result;
    result << return_color.x() * 255, return_color.y() * 255, return_color.z() * 255;
    return result;
}

static Eigen::Vector3f reflect(const Eigen::Vector3f& vec, const Eigen::Vector3f& axis)
{
    auto costheta = vec.dot(axis);
    return (2 * costheta * axis - vec).normalized();
}

struct light
{
    Eigen::Vector3f position;
    Eigen::Vector3f intensity;
};

Eigen::Vector3f texture_fragment_shader(const fragment_shader_payload& payload)
{
    Eigen::Vector3f return_color = {0, 0, 0};
    if (payload.texture)
    {
        // TODO: Get the texture value at the texture coordinates of the current fragment
        float u,v;
        u = payload.tex_coords.x();
        v = payload.tex_coords.y();
        Eigen::Vector3f temp = payload.texture->getColor(u,v);
        return_color = temp;
    }
    Eigen::Vector3f texture_color;
    texture_color << return_color.x(), return_color.y(), return_color.z();

    Eigen::Vector3f ka = Eigen::Vector3f(0.005, 0.005, 0.005);
    Eigen::Vector3f kd = texture_color / 255.f;
    Eigen::Vector3f ks = Eigen::Vector3f(0.7937, 0.7937, 0.7937);

    //light: {{position},{intensity}}
    auto l1 = light{{20, 20, 20}, {500, 500, 500}};
    auto l2 = light{{-20, 20, 0}, {500, 500, 500}};

    std::vector<light> lights = {l1, l2};
    Eigen::Vector3f amb_light_intensity{10, 10, 10};
    Eigen::Vector3f eye_pos{0, 0, 10};

    float p = 150;

    Eigen::Vector3f color = texture_color;
    Eigen::Vector3f point = payload.view_pos;
    Eigen::Vector3f normal = payload.normal;

    Eigen::Vector3f result_color = {0, 0, 0};

    for (auto& light : lights)
    {
        // TODO: For each light source in the code, calculate what the *ambient*, *diffuse*, and *specular* 
        // components are. Then, accumulate that result on the *result_color* object.
        float r = (point - light.position).norm();
        float r2 = r*r;
        Eigen::Vector3f l = (light.position - point).normalized();
        Eigen::Vector3f v = (eye_pos - point).normalized();
        Eigen::Vector3f h = (v+l).normalized();
        Eigen::Vector3f ambient = ka * amb_light_intensity[0];
        Eigen::Vector3f diffuse = kd * (light.intensity[0]/(r2))*max(0.f,normal.dot(l));
        Eigen::Vector3f specular = ks * (light.intensity[0]/(r2))*pow(max(0.f, normal.dot(h)),p);
        result_color += (ambient + diffuse + specular);
    }

    return result_color * 255.f;
}

Eigen::Vector3f phong_fragment_shader(const fragment_shader_payload& payload)
{
    Eigen::Vector3f ka = Eigen::Vector3f(0.005, 0.005, 0.005);
    Eigen::Vector3f kd = payload.color;
    Eigen::Vector3f ks = Eigen::Vector3f(0.7937, 0.7937, 0.7937);

    //light: {{position},{intensity}}
    auto l1 = light{{20, 20, 20}, {500, 500, 500}};
    auto l2 = light{{-20, 20, 0}, {500, 500, 500}};

    std::vector<light> lights = {l1, l2};
    Eigen::Vector3f amb_light_intensity{10, 10, 10};
    Eigen::Vector3f eye_pos{0, 0, 10};

    float p = 150;

    Eigen::Vector3f color = payload.color;
    Eigen::Vector3f point = payload.view_pos;
    Eigen::Vector3f normal = payload.normal;

    Eigen::Vector3f result_color = {0, 0, 0};
    for (auto& light : lights)
    {
        // TODO: For each light source in the code, calculate what the *ambient*, *diffuse*, and *specular* 
        // components are. Then, accumulate that result on the *result_color* object.
        float r = (point - light.position).norm();
        float r2 = r*r;
        Eigen::Vector3f l = (light.position - point).normalized();
        Eigen::Vector3f v = (eye_pos - point).normalized();
        Eigen::Vector3f h = (v+l).normalized();
        Eigen::Vector3f ambient = ka * amb_light_intensity[0];
        Eigen::Vector3f diffuse = kd * (light.intensity[0]/(r2))*max(0.f,normal.dot(l));
        Eigen::Vector3f specular = ks * (light.intensity[0]/(r2))*pow(max(0.f, normal.dot(h)),p);
        result_color += (ambient + diffuse + specular);
    }

    return result_color * 255.f;
}



Eigen::Vector3f displacement_fragment_shader(const fragment_shader_payload& payload)
{
    
    Eigen::Vector3f ka = Eigen::Vector3f(0.005, 0.005, 0.005);
    Eigen::Vector3f kd = payload.color;
    Eigen::Vector3f ks = Eigen::Vector3f(0.7937, 0.7937, 0.7937);

    auto l1 = light{{20, 20, 20}, {500, 500, 500}};
    auto l2 = light{{-20, 20, 0}, {500, 500, 500}};

    std::vector<light> lights = {l1, l2};
    Eigen::Vector3f amb_light_intensity{10, 10, 10};
    Eigen::Vector3f eye_pos{0, 0, 10};

    float p = 150;

    Eigen::Vector3f color = payload.color; 
    Eigen::Vector3f point = payload.view_pos;
    Eigen::Vector3f normal = payload.normal;

    float kh = 0.2;
    float kn = 0.1;
    
    // TODO: Implement displacement mapping here
    // Let n = normal = (x, y, z)
    float x = normal.x();
    float y = normal.y();
    float z = normal.z();
    // Vector t = (-x*y/sqrt(x*x+z*z),sqrt(x*x+z*z),-z*y/sqrt(x*x+z*z))
    Eigen::Vector3f tangent(-1*x*y/sqrt(x*x+z*z),sqrt(x*x+z*z),-1*z*y/sqrt(x*x+z*z));
    // Vector b = n cross product t
    Eigen::Vector3f bitangent = normal.cross(tangent);
    // Matrix TBN = [t b n]
    Eigen::Matrix<float,3,3> TBN;
    TBN<<tangent,bitangent,normal; 
    // dU = kh * kn * (h(u+1/width,v)-h(u,v))
    // dV = kh * kn * (h(u,v+1/height)-h(u,v))
    float width = (float)payload.texture->width;
    float height = (float)payload.texture->height;
    float u = payload.tex_coords.x();
    float v = payload.tex_coords.y();
    float dU = kh * kn * (payload.texture->getColor(u+1/width,v).norm()-payload.texture->getColor(u,v).norm());
    float dV = kh * kn * (payload.texture->getColor(u,v+1/height).norm()-payload.texture->getColor(u,v).norm());
    // Vector ln = (-dU, -dV, 1)
    Eigen::Vector3f tangent_space_normal(-dU,-dV,1);
    // Position p = p + kn * n * h(u,v)
    point += (kn * normal * payload.texture->getColor(u,v).norm());
    // Normal n = normalize(TBN * ln)
    normal = (TBN * tangent_space_normal).normalized();

    Eigen::Vector3f result_color = {0, 0, 0};
    for (auto& light : lights)
    {
        // TODO: For each light source in the code, calculate what the *ambient*, *diffuse*, and *specular* 
        // components are. Then, accumulate that result on the *result_color* object.
        float r = (point - light.position).norm();
        float r2 = r*r;
        Eigen::Vector3f l = (light.position - point).normalized();
        Eigen::Vector3f v = (eye_pos - point).normalized();
        Eigen::Vector3f h = (v+l).normalized();
        Eigen::Vector3f ambient = ka * amb_light_intensity[0];
        Eigen::Vector3f diffuse = kd * (light.intensity[0]/(r2))*max(0.f,normal.dot(l));
        Eigen::Vector3f specular = ks * (light.intensity[0]/(r2))*pow(max(0.f, normal.dot(h)),p);
        result_color += (ambient + diffuse + specular);
    }
    return result_color * 255.f;
}


Eigen::Vector3f bump_fragment_shader(const fragment_shader_payload& payload)
{
    
    Eigen::Vector3f ka = Eigen::Vector3f(0.005, 0.005, 0.005);
    Eigen::Vector3f kd = payload.color;
    Eigen::Vector3f ks = Eigen::Vector3f(0.7937, 0.7937, 0.7937);

    auto l1 = light{{20, 20, 20}, {500, 500, 500}};
    auto l2 = light{{-20, 20, 0}, {500, 500, 500}};

    std::vector<light> lights = {l1, l2};
    Eigen::Vector3f amb_light_intensity{10, 10, 10};
    Eigen::Vector3f eye_pos{0, 0, 10};

    float p = 150;

    Eigen::Vector3f color = payload.color; 
    Eigen::Vector3f point = payload.view_pos;
    Eigen::Vector3f normal = payload.normal;

    float kh = 0.2;
    float kn = 0.1;

    // TODO: Implement bump mapping here
    // Let n = normal = (x, y, z)
    float x = normal.x();
    float y = normal.y();
    float z = normal.z();
    // Vector t = (-x*y/sqrt(x*x+z*z),sqrt(x*x+z*z),-z*y/sqrt(x*x+z*z))
    Eigen::Vector3f tangent(-1*x*y/sqrt(x*x+z*z),sqrt(x*x+z*z),-1*z*y/sqrt(x*x+z*z));
    // Vector b = n cross product t
    Eigen::Vector3f bitangent = normal.cross(tangent);
    // Matrix TBN = [t b n]
    Eigen::Matrix<float,3,3> TBN;
    TBN<<tangent,bitangent,normal; 
    // dU = kh * kn * (h(u+1/width,v)-h(u,v))
    // dV = kh * kn * (h(u,v+1/height)-h(u,v))
    float width = (float)payload.texture->width;
    float height = (float)payload.texture->height;
    float u = payload.tex_coords.x();
    float v = payload.tex_coords.y();
    float dU = kh * kn * (payload.texture->getColor(u+1/width,v).norm()-payload.texture->getColor(u,v).norm());
    float dV = kh * kn * (payload.texture->getColor(u,v+1/height).norm()-payload.texture->getColor(u,v).norm());
    // Vector ln = (-dU, -dV, 1)
    Eigen::Vector3f tangent_space_normal(-dU,-dV,1);
    // Normal n = normalize(TBN * ln)
    normal = (TBN*tangent_space_normal).normalized();
    Eigen::Vector3f result_color = {0, 0, 0};
    result_color = normal;
    return result_color * 255.f;
}

int main(int argc, const char** argv)
{
    //use a list to store all the triangles 
    std::vector<Triangle*> TriangleList;

    float angle = 140.0;    //for adjusting positions of the object
    bool command_line = false;

    //specify which 3D model to draw
    std::string filename = "output.png";
    objl::Loader Loader;
    std::string obj_path = "../models/spot/";

    // Load .obj File (default: ./model/spot)
    //How to load? 
    //Input: obj file   Output: a list of triangles in space (before MVP transform)
    bool loadout = Loader.LoadFile("../models/spot/spot_triangulated_good.obj");
    for(auto mesh:Loader.LoadedMeshes)
    {
        for(int i=0;i<mesh.Vertices.size();i+=3)
        {
            Triangle* t = new Triangle();
            for(int j=0;j<3;j++)
            {
                t->setVertex(j,Vector4f(mesh.Vertices[i+j].Position.X,mesh.Vertices[i+j].Position.Y,mesh.Vertices[i+j].Position.Z,1.0));
                t->setNormal(j,Vector3f(mesh.Vertices[i+j].Normal.X,mesh.Vertices[i+j].Normal.Y,mesh.Vertices[i+j].Normal.Z));
                /***************************************************************************************************************
                * One thing to note here:
                * We set the texture coordinate for each vertex of triangle but we don't know the actual texture image yet.
                * Basically, I think the 3D object has already taken the responsibility of defining the 1-1 map from 3D space
                * to 2D image. 
                * Later, we can specify a path to the texture image, and that way, we can fetch colors from texture image easily.
                * 
                * What't missing here?
                * The color of vetices is still unknown!!!!!!!!!!!!!
                * We will define it in rasterizer's function draw()
                ****************************************************************************************************************/
                t->setTexCoord(j,Vector2f(mesh.Vertices[i+j].TextureCoordinate.X, mesh.Vertices[i+j].TextureCoordinate.Y));
            }
            TriangleList.push_back(t);
        }
    }

    //initialize rasterizer
    rst::rasterizer r(700, 700);

    //use the height map as texture(default value)
    auto texture_path = "hmap.jpg";
    //pass the texture object into the rasterizer
    //the texture object get initialized by passing texture image path to the constructor
    //by passing the path of texture image, opencv will read the image and transfer it to useful data
    r.set_texture(Texture(obj_path + texture_path));

    /*********************************************************************************************
    * new feature of C++11
    * declaration: template <class T> function
    * by using std::function, we can package the idea of function pointer
    * active_shader is a pointer to real shader function, but we don't need to use * to address it
    * function active_shader:
    * @params: fragment_shader_payload
    * @output: Eigen::Vector3f, aka. the rgb info.
    **********************************************************************************************/
    std::function<Eigen::Vector3f(fragment_shader_payload)> active_shader = phong_fragment_shader;

    if (argc >= 2)
    {
        //we pass in enough parameters to change default shader and texture path
        command_line = true;
        filename = std::string(argv[1]);

        //reset the texture object and pass them inside rasterizer
        if (argc == 3 && std::string(argv[2]) == "texture")
        {
            std::cout << "Rasterizing using the texture shader\n";
            active_shader = texture_fragment_shader;
            texture_path = "spot_texture.png";
            r.set_texture(Texture(obj_path + texture_path));
        }
        else if (argc == 3 && std::string(argv[2]) == "normal")
        {
            std::cout << "Rasterizing using the normal shader\n";
            active_shader = normal_fragment_shader;
        }
        else if (argc == 3 && std::string(argv[2]) == "phong")
        {
            std::cout << "Rasterizing using the phong shader\n";
            active_shader = phong_fragment_shader;
        }
        else if (argc == 3 && std::string(argv[2]) == "bump")
        {
            std::cout << "Rasterizing using the bump shader\n";
            active_shader = bump_fragment_shader;
        }
        else if (argc == 3 && std::string(argv[2]) == "displacement")
        {
            std::cout << "Rasterizing using the displacement shader\n";
            active_shader = displacement_fragment_shader;
        }
    }

    //finished setting up the 3D model and the shader

    //define camera position in world coordinate
    Eigen::Vector3f eye_pos = {0,0,10};

    //load shaders to rasterizer
    r.set_vertex_shader(vertex_shader);     //vertex shader
    r.set_fragment_shader(active_shader);   //fragment shader

    int key = 0;
    int frame_count = 0;

    //get output image
    if (command_line)
    {
        //basic pipeline before drawing things
        r.clear(rst::Buffers::Color | rst::Buffers::Depth);
        r.set_model(get_model_matrix(angle));
        r.set_view(get_view_matrix(eye_pos));
        r.set_projection(get_projection_matrix(45.0, 1, 0.1, 50));

        //ready to draw
        //pass in the list of triangles to rasterizer's function draw
        r.draw(TriangleList);
        cv::Mat image(700, 700, CV_32FC3, r.frame_buffer().data());
        image.convertTo(image, CV_8UC3, 1.0f);
        cv::cvtColor(image, image, cv::COLOR_RGB2BGR);

        cv::imwrite(filename, image);

        return 0;
    }

    //open a window and do real time rendering
    while(key != 27)
    {
        r.clear(rst::Buffers::Color | rst::Buffers::Depth);

        r.set_model(get_model_matrix(angle));
        r.set_view(get_view_matrix(eye_pos));
        r.set_projection(get_projection_matrix(45.0, 1, 0.1, 50));

        //r.draw(pos_id, ind_id, col_id, rst::Primitive::Triangle);
        r.draw(TriangleList);
        cv::Mat image(700, 700, CV_32FC3, r.frame_buffer().data());
        image.convertTo(image, CV_8UC3, 1.0f);
        cv::cvtColor(image, image, cv::COLOR_RGB2BGR);

        cv::imshow("image", image);
        cv::imwrite(filename, image);
        key = cv::waitKey(10);

        if (key == 'a' )
        {
            angle -= 0.1;
        }
        else if (key == 'd')
        {
            angle += 0.1;
        }

    }
    return 0;
}
