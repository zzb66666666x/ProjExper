//
// Created by LEI XU on 4/27/19.
//

#ifndef RASTERIZER_SHADER_H
#define RASTERIZER_SHADER_H
#include <eigen3/Eigen/Eigen>
#include "Texture.hpp"

//two basic types of shader
//vertex shader     (顶点着色器)
//fragment shader   (片元着色器)

//what is payload?
//the payload stores the information needed to do shading
//people should pass in the payload to actually use the shader
//payload is just like a package of necessary information for shader programs

struct fragment_shader_payload
{
    //two consturctors with different params
    fragment_shader_payload()
    {
        texture = nullptr;
    }

    /***************************
    * @ params
    * color
    * normal vector
    * texture coordinate 
    * pointer to a texture image
    ****************************/
    fragment_shader_payload(const Eigen::Vector3f& col, const Eigen::Vector3f& nor,const Eigen::Vector2f& tc, Texture* tex) :
         color(col), normal(nor), tex_coords(tc), texture(tex) {}

    Eigen::Vector3f view_pos;   //shading point
    /******************************************************************
    * What is a shading point? It's a point in eyespace, we need it to 
    * calc the distance from light source to it, we denote the distance
    * as r in Bling Phong's Reflectance Model
    *******************************************************************/


    Eigen::Vector3f color;
    Eigen::Vector3f normal;
    Eigen::Vector2f tex_coords;
    Texture* texture;
};


struct vertex_shader_payload
{
    //only need a vector representing positions  
    Eigen::Vector3f position;
};

#endif //RASTERIZER_SHADER_H
