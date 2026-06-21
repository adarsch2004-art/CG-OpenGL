#version 330

in vec3 v2f_color;
in vec3 v2f_position;
in vec3 v2f_normal;
in vec3 v2f_gouraud_color;
uniform int shading_mode;
out vec4 f_color;

void main()
{
    if(shading_mode == 1)
    {
        // Gouraud-Shading
        // Licht wurde schon im Vertex-Shader berechnet
        f_color = vec4(v2f_gouraud_color, 1.0);
    }
    else if(shading_mode == 2)
    {
        // Phong-Shading
        // Licht wird hier im Fragment-Shader berechnet
        vec3 N = normalize(v2f_normal);

        vec3 light_position = vec3(0.0, 0.0, 2.0);
        vec3 L = normalize(light_position - v2f_position);

        float diffuse = max(dot(N, L), 0.0);

        vec3 ambient_color = 0.2 * v2f_color;
        vec3 diffuse_color = diffuse * v2f_color;

        vec3 color = ambient_color + diffuse_color;

        f_color = vec4(color, 1.0);
    }
    else
    {
        // Wireframe  einfache Farbe
        f_color = vec4(v2f_color, 1.0);
    }
}
