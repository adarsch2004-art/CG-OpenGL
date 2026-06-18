#version 330

layout (location=0) in vec4 v_position;
layout (location=1) in vec3 v_color;
layout (location=2) in vec3 v_normal;
uniform mat4 modelview_projection_matrix;
uniform mat4 modelview_matrix;
out vec3 v2f_color;

void main()
{
    vec4 position_eye= modelview_matrix * v_position;

    vec3 N= normalize(mat3(modelview_matrix) * v_normal);

    vec3 light_position= vec3(0.0, 0.0, 2.0);
    vec3 L= normalize(light_position - position_eye.xyz);

    float diffuse= max(dot(N, L), 0.0);

    vec3 ambient_color= 0.2 * v_color;
    vec3 diffuse_color= diffuse * v_color;

    v2f_color = ambient_color + diffuse_color;
    gl_Position = modelview_projection_matrix * v_position;
}