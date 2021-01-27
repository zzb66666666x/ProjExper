//
// Created by goksu on 4/6/19.
//

#include <algorithm>
#include "rasterizer.hpp"
#include <opencv2/opencv.hpp>
#include <math.h>

// not used in this project 
rst::pos_buf_id rst::rasterizer::load_positions(const std::vector<Eigen::Vector3f> &positions)
{
    auto id = get_next_id();
    pos_buf.emplace(id, positions);

    return {id};
}

// not used in this project 
rst::ind_buf_id rst::rasterizer::load_indices(const std::vector<Eigen::Vector3i> &indices)
{
    auto id = get_next_id();
    ind_buf.emplace(id, indices);

    return {id};
}

// not used in this project 
rst::col_buf_id rst::rasterizer::load_colors(const std::vector<Eigen::Vector3f> &cols)
{
    auto id = get_next_id();
    col_buf.emplace(id, cols);

    return {id};
}

// not used in this project 
rst::col_buf_id rst::rasterizer::load_normals(const std::vector<Eigen::Vector3f>& normals)
{
    auto id = get_next_id();
    nor_buf.emplace(id, normals);

    normal_id = id;

    return {id};
}


// not used in this project 
// Bresenham's line drawing algorithm
void rst::rasterizer::draw_line(Eigen::Vector3f begin, Eigen::Vector3f end)
{
    auto x1 = begin.x();
    auto y1 = begin.y();
    auto x2 = end.x();
    auto y2 = end.y();

    Eigen::Vector3f line_color = {255, 255, 255};

    int x,y,dx,dy,dx1,dy1,px,py,xe,ye,i;

    dx=x2-x1;
    dy=y2-y1;
    dx1=fabs(dx);
    dy1=fabs(dy);
    px=2*dy1-dx1;
    py=2*dx1-dy1;

    if(dy1<=dx1)
    {
        if(dx>=0)
        {
            x=x1;
            y=y1;
            xe=x2;
        }
        else
        {
            x=x2;
            y=y2;
            xe=x1;
        }
        Eigen::Vector2i point = Eigen::Vector2i(x, y);
        set_pixel(point,line_color);
        for(i=0;x<xe;i++)
        {
            x=x+1;
            if(px<0)
            {
                px=px+2*dy1;
            }
            else
            {
                if((dx<0 && dy<0) || (dx>0 && dy>0))
                {
                    y=y+1;
                }
                else
                {
                    y=y-1;
                }
                px=px+2*(dy1-dx1);
            }
//            delay(0);
            Eigen::Vector2i point = Eigen::Vector2i(x, y);
            set_pixel(point,line_color);
        }
    }
    else
    {
        if(dy>=0)
        {
            x=x1;
            y=y1;
            ye=y2;
        }
        else
        {
            x=x2;
            y=y2;
            ye=y1;
        }
        Eigen::Vector2i point = Eigen::Vector2i(x, y);
        set_pixel(point,line_color);
        for(i=0;y<ye;i++)
        {
            y=y+1;
            if(py<=0)
            {
                py=py+2*dx1;
            }
            else
            {
                if((dx<0 && dy<0) || (dx>0 && dy>0))
                {
                    x=x+1;
                }
                else
                {
                    x=x-1;
                }
                py=py+2*(dx1-dy1);
            }
//            delay(0);
            Eigen::Vector2i point = Eigen::Vector2i(x, y);
            set_pixel(point,line_color);
        }
    }
}

auto to_vec4(const Eigen::Vector3f& v3, float w = 1.0f)
{
    return Vector4f(v3.x(), v3.y(), v3.z(), w);
}

static std::tuple<float, float, float> computeBarycentric2D(float x, float y, const Vector4f* v){
    float c1 = (x*(v[1].y() - v[2].y()) + (v[2].x() - v[1].x())*y + v[1].x()*v[2].y() - v[2].x()*v[1].y()) / (v[0].x()*(v[1].y() - v[2].y()) + (v[2].x() - v[1].x())*v[0].y() + v[1].x()*v[2].y() - v[2].x()*v[1].y());
    float c2 = (x*(v[2].y() - v[0].y()) + (v[0].x() - v[2].x())*y + v[2].x()*v[0].y() - v[0].x()*v[2].y()) / (v[1].x()*(v[2].y() - v[0].y()) + (v[0].x() - v[2].x())*v[1].y() + v[2].x()*v[0].y() - v[0].x()*v[2].y());
    float c3 = (x*(v[0].y() - v[1].y()) + (v[1].x() - v[0].x())*y + v[0].x()*v[1].y() - v[1].x()*v[0].y()) / (v[2].x()*(v[0].y() - v[1].y()) + (v[1].x() - v[0].x())*v[2].y() + v[0].x()*v[1].y() - v[1].x()*v[0].y());
    return {c1,c2,c3};
}

static bool insideTriangle(int x, int y, const Vector4f* _v){
    Vector3f v[3];
    for(int i=0;i<3;i++)
        v[i] = {_v[i].x(),_v[i].y(), 1.0};
    Vector3f f0,f1,f2;
    f0 = v[1].cross(v[0]);
    f1 = v[2].cross(v[1]);
    f2 = v[0].cross(v[2]);
    Vector3f p(x,y,1.);
    if((p.dot(f0)*f0.dot(v[2])>0) && (p.dot(f1)*f1.dot(v[0])>0) && (p.dot(f2)*f2.dot(v[1])>0))
        return true;
    return false;
}

void rst::rasterizer::draw(std::vector<Triangle *> &TriangleList) {
    float f1 = (50 - 0.1) / 2.0;
    float f2 = (50 + 0.1) / 2.0;

    /**************************************************************************
    * Screen Space: MVP transformation
    * World Space: RAW information with the eye position not in the origin 
    * eyespace: the space after view and model transformation
    * 
    * Shading Program and interpolation should be done in the eyespace without 
    * perspective projection (which will ruin the 3D structure of model)
    * That's why the triangle's normal vectors don't get multiplied by the 
    * projection matrix or the viewport matrix.
    * Similarily, the calculation of Barycentric Coordinate should be done in 
    * eyespace too, but it's somehow acceptable to use the <alpha, beta, gamma>
    * returned from function computeBarycentric2D
    ***************************************************************************/

    Eigen::Matrix4f mvp = projection * view * model;
    FILE * fptr = fopen("checking.txt", "w");
    fprintf(fptr, "old                                   new\n");
    for (const auto& t:TriangleList)
    {
        /************************************************************************************
        * What is happending here?
        * pass in the list of triangles loaded from object file
        * these triangles need to be processed by doing all the transformations
        * loop over these triangles and define new tiangles after transformation
        * finally, draw these triangles by rasterization and shading
        * 
        * Something to notice:
        * compared with previous projects, the vertices in class triangle is now in R^4
        * but t->v used to be an array of Vector3f in assignment 1&2
        * that's why the code below is a little bit different
        * 
        * What's in the class triangle?
        * three vertices in R^4 (forth coordinate should be 1)
        * three color vectors in R^3
        * three texture coordinate vectors in R^2
        * three normal vectors in R^3
        *************************************************************************************/
        
        //t is a pointer, define a newtri variable to keep *t
        Triangle newtri = *t;

        /****************************************************************************************************
        * make a copy of vertices before doing projection, store it in viewspace_pos
        * the viewspace_pos will be useful in the shading process when calculating reflectance model
        * we will use <alpha, beta, gamma> to interpolate a shading point in eyespace 
        * THOUGH THERE ARE SOME ERRORS IN THIS METHOD
        * the right way is to multiply the point (x,y,z,1) with inverse(M_projection)inverse(M_viewport)
        * so that we get the real shading point and also the real barycentric coordinate <alpha, beta, gamma>
        * then we interpolate normal vectors or texture coordinate ...
        * BUT IT'S STILL OK TO USE FUNCTION computeBarycentric2D
        *****************************************************************************************************/
        std::array<Eigen::Vector4f, 3> mm {
                (view * model * t->v[0]),
                (view * model * t->v[1]),
                (view * model * t->v[2])
        };
        std::array<Eigen::Vector3f, 3> viewspace_pos;
        std::transform(mm.begin(), mm.end(), viewspace_pos.begin(), [](auto& v) {
            return v.template head<3>();
        });

        //exec mvp transformation for old triangle's vertices
        //and this time, the result will finally be kept by new triangle
        //DON'T DO THE MVP TRANSFORMATION ON NORMAL VECTORS
        Eigen::Vector4f v[] = {
                mvp * t->v[0],
                mvp * t->v[1],
                mvp * t->v[2]
        };
        for (auto& vec : v) {
            //Homogeneous division 
            //the forth coordinate dorsn't get changed here
            vec.x()/=vec.w();
            vec.y()/=vec.w();
            vec.z()/=vec.w();
        }

        
        //Since the 3D model object also contains the normal vectors for each vertex,
        //so we cannot skip the transformation of normal vectors !!!
        //But what is the mathematical facts behind it?
        Eigen::Matrix4f inv_trans = (view * model).inverse().transpose();
        /******************************************************************************
        * Matrix inv_trans
        * Full name: the inverse transpose matrix of viewspace transformatin.
        * When doing transformation from world space to eye space, we need matrix M
        * M = view * model, we don't multiply the projection matrix here. If we do, it
        * will scale everything to canonical cube, that's not the space we see, but the 
        * space that can guatantee people will see 3D structure within screen.
        * Take normal vector n and a vector inside triangle v,
        * since transpose(n)*v = 0,
        * then transpose(n)*inverse(M)*M*v = 0,
        * since M*v is the vector in eyespace, call it v', we want transpose(n')*b' = 0,
        * so transpose(n') = transpose(n)*inverse(M) !!!
        * Finally, n' = transpose(inverse(M)) * n
        *******************************************************************************/
        Eigen::Vector4f n[] = {
                inv_trans * to_vec4(t->normal[0], 0.0f),
                inv_trans * to_vec4(t->normal[1], 0.0f),
                inv_trans * to_vec4(t->normal[2], 0.0f)
        };

        //Viewport transformation
        //loop over the vertices scale the each vertex v[j] to be inside screen space 
        //DON'T DO THE VIEWPORT TRANSFORMATION ON NORMAL VECTORS
        for (auto & vert : v)
        {
            vert.x() = 0.5*width*(vert.x()+1.0);
            vert.y() = 0.5*height*(vert.y()+1.0);
            vert.z() = vert.z() * f1 + f2;
        }

        //finish everything about transformation, ready to modify newtri
        //We don't create new class triangle objects !!!
        
        /**********************************
        * List of what to modify:
        * Change vertices
        * Change normal vectors
        * Newly define colors for vertices 
        ***********************************/

        for (int i = 0; i < 3; ++i)
        {
            //screen space coordinates
            //don't have to drop the 4'th coordinate since the declaration of class triangle
            //shows that vertices should be vectors in R^4
            newtri.setVertex(i, v[i]);
        }

        for (int i = 0; i < 3; ++i)
        {
            //view space normal
            //drop the 4'th coordinate since normal vectors stored in newtri should be in R^3
            newtri.setNormal(i, n[i].head<3>());
        }

        //texture coordinates don't affected by any transformation, of course

        //set the color of vertices and finish modifying triangles
        newtri.setColor(0, 148,121.0,92.0);
        newtri.setColor(1, 148,121.0,92.0);
        newtri.setColor(2, 148,121.0,92.0);

        // Also pass view space vertice position, this will be useful for calculating eyespace(viewspace) shading point
        rasterize_triangle(fptr, newtri, viewspace_pos);
    }
    fclose(fptr);
}

//interpolation using barycentric coordinate
static float interpolate(float alpha, float beta, float gamma, const float vert1, const float vert2, const float vert3, float weight)
{
    return (alpha * vert1 + beta * vert2 + gamma * vert3) / weight;
}

static Eigen::Vector3f interpolate(float alpha, float beta, float gamma, const Eigen::Vector3f& vert1, const Eigen::Vector3f& vert2, const Eigen::Vector3f& vert3, float weight)
{
    return (alpha * vert1 + beta * vert2 + gamma * vert3) / weight;
}

static Eigen::Vector2f interpolate(float alpha, float beta, float gamma, const Eigen::Vector2f& vert1, const Eigen::Vector2f& vert2, const Eigen::Vector2f& vert3, float weight)
{
    auto u = (alpha * vert1[0] + beta * vert2[0] + gamma * vert3[0]);
    auto v = (alpha * vert1[1] + beta * vert2[1] + gamma * vert3[1]);

    u /= weight;
    v /= weight;

    return Eigen::Vector2f(u, v);
}

//Screen space rasterization
void rst::rasterizer::rasterize_triangle(FILE* fptr, const Triangle& t, const std::array<Eigen::Vector3f, 3>& view_pos) 
{
    // TODO: From your HW3, get the triangle rasterization code.
    // TODO: Inside your rasterization loop:
    float x_min, x_max, y_min, y_max, temp_x, temp_y;
    Eigen::Vector3f rgb;
    Eigen::Vector3f point;
    x_min = t.v[0].x();
    x_max = x_min;
    y_min = t.v[0].y();
    y_max = y_min;
    // TODO : Find out the bounding box of current triangle.
    for (int i=1; i<3; i++){
        temp_x = t.v[i].x();
        temp_y = t.v[i].y();
        if (temp_x<x_min){x_min = temp_x;}
        else if (temp_x>x_max){x_max = temp_x;}
        if (temp_y<y_min){y_min = temp_y;}
        else if (temp_y>y_max){y_max = temp_y;}
    }
    if ((x_min<0)||(x_max<0)||(y_min<0)||(y_max<0)){
        throw "invalid position for pixels";
    }
    int x_begin, x_end, y_begin, y_end;
    x_begin = (int)floor(x_min);
    x_end = (int)ceil(x_max);
    y_begin = (int)floor(y_min);
    y_end = (int)ceil(y_max);
    for (int x = x_begin; x<x_end; x++){
        for (int y = y_begin; y<y_end; y++){
            if(insideTriangle(x,y,t.v)){
                //calc barycentric coordinate and do interpolation
                auto[alpha, beta, gamma] = computeBarycentric2D(x, y, t.v);
                Eigen::Vector3f barycentric(alpha, beta, gamma);
                float Z = 1.0 / (alpha / t.v[0].w() + beta / t.v[1].w() + gamma / t.v[2].w());
                alpha = alpha/t.v[0].w()*Z;
                beta = beta/t.v[1].w()*Z;
                gamma = gamma/t.v[2].w()*Z;
                float zp = interpolate(alpha, beta, gamma, t.v[0].z(), t.v[1].z(), t.v[2].z(),1);        
                //z buffer first
                if (zp < depth_buf[get_index(x,y)]){
                    depth_buf[get_index(x,y)] = zp;
                    auto interpolated_color = interpolate(alpha, beta, gamma, t.color[0], t.color[1], t.color[2], 1);
                    auto interpolated_normal = interpolate(alpha, beta, gamma,t.normal[0],t.normal[1],t.normal[2],1).normalized();
                    auto interpolated_texcoords = interpolate(alpha, beta, gamma,t.tex_coords[0],t.tex_coords[1],t.tex_coords[2],1);
                    auto interpolated_shadingcoords = interpolate(alpha, beta, gamma,view_pos[0],view_pos[1],view_pos[2],1);
                    //initialize shader payload
                    fragment_shader_payload payload( interpolated_color, interpolated_normal, interpolated_texcoords, texture ? &*texture : nullptr);
                    payload.view_pos = interpolated_shadingcoords;
                    //Instead of passing the triangle's color directly to the frame buffer, pass the color to the shaders first to get the final color;
                    auto pixel_color = fragment_shader(payload);
                    Eigen::Vector2i point(x,y);
                    set_pixel(point, pixel_color);
                }
            }
        }
    }
}

void rst::rasterizer::set_model(const Eigen::Matrix4f& m)
{
    model = m;
}

void rst::rasterizer::set_view(const Eigen::Matrix4f& v)
{
    view = v;
}

void rst::rasterizer::set_projection(const Eigen::Matrix4f& p)
{
    projection = p;
}

void rst::rasterizer::clear(rst::Buffers buff)
{
    if ((buff & rst::Buffers::Color) == rst::Buffers::Color)
    {
        std::fill(frame_buf.begin(), frame_buf.end(), Eigen::Vector3f{0, 0, 0});
    }
    if ((buff & rst::Buffers::Depth) == rst::Buffers::Depth)
    {
        std::fill(depth_buf.begin(), depth_buf.end(), std::numeric_limits<float>::infinity());
    }
}

rst::rasterizer::rasterizer(int w, int h) : width(w), height(h)
{
    frame_buf.resize(w * h);
    depth_buf.resize(w * h);

    texture = std::nullopt;
}

int rst::rasterizer::get_index(int x, int y)
{
    return (height-y)*width + x;
}

void rst::rasterizer::set_pixel(const Vector2i &point, const Eigen::Vector3f &color)
{
    //old index: auto ind = point.y() + point.x() * width;
    int ind = (height-point.y())*width + point.x();
    frame_buf[ind] = color;
}

void rst::rasterizer::set_vertex_shader(std::function<Eigen::Vector3f(vertex_shader_payload)> vert_shader)
{
    vertex_shader = vert_shader;
}

void rst::rasterizer::set_fragment_shader(std::function<Eigen::Vector3f(fragment_shader_payload)> frag_shader)
{
    fragment_shader = frag_shader;
}

