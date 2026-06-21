#version 330

layout (location=0) in vec4 v_position;
layout (location=1) in vec3 v_color;
layout (location=2) in vec3 v_normal;
uniform mat4 modelview_projection_matrix;
uniform mat4 modelview_matrix;
out vec3 v2f_color;
out vec3 v2f_position;
out vec3 v2f_normal;

void main()
{
    vec4 position_eye = modelview_matrix * v_position;

    v2f_position = position_eye.xyz;
    v2f_normal = normalize(mat3(modelview_matrix) * v_normal);
    v2f_color = v_color;

    gl_Position = modelview_projection_matrix * v_position;
}