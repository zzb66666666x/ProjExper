cmake_minimum_required(VERSION 3.10)
set(CMAKE_CXX_STANDARD 17)
project(Rasterizer)

set(LIBS D:/CodingLibs)
set(OpenCV_DIR ${LIBS}/opencv/mingw_build)
find_package(OpenCV REQUIRED)

set(INCLUDE_DIR ${LIBS})
include_directories(${INCLUDE_DIR})

add_executable(Rasterizer main.cpp rasterizer.hpp rasterizer.cpp \ 
global.hpp Triangle.hpp Triangle.cpp Texture.hpp Texture.cpp Shader.hpp OBJ_Loader.h)
target_link_libraries(Rasterizer ${OpenCV_LIBRARIES})
#target_compile_options(Rasterizer PUBLIC -Wall -Wextra -pedantic)