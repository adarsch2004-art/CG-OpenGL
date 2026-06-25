"""
/*******************************************************************************
 *
 *            #, #,         CCCCCC  VV    VV MM      MM RRRRRRR
 *           %  %(  #%%#   CC    CC VV    VV MMM    MMM RR    RR
 *           %    %## #    CC        V    V  MM M  M MM RR    RR
 *            ,%      %    CC        VV  VV  MM  MM  MM RRRRRR
 *            (%      %,   CC    CC   VVVV   MM      MM RR   RR
 *              #%    %*    CCCCCC     VV    MM      MM RR    RR
 *             .%    %/
 *                (%.      Computer Vision & Mixed Reality Group
 *
 ******************************************************************************/
/**          @copyright:   Hochschule RheinMain,
 *                         University of Applied Sciences
 *              @author:   Prof. Dr. Ulrich Schwanecke
 *             @version:   0.91
 *                @date:   07.06.2022
 ******************************************************************************/
/**         oglTemplate.py
 *
 *          Simple Python OpenGL program that uses PyOpenGL + GLFW to get an
 *          OpenGL 3.2 core profile context and animate a colored triangle.
 ****
"""

import glfw
import numpy as np
import math
import sys

from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO
from OpenGL.GL.shaders import *

from mat4 import *

EXIT_FAILURE = -1


class Scene:
    """
        OpenGL scene class that render a RGB colored tetrahedron.
    """

    def __init__(self, width, height, scenetitle="Hello Triangle"):
        self.scenetitle         = scenetitle
        self.width              = width
        self.height             = height
        self.angle              = 0
        self.angle_increment    = 1
        self.animate            = False
        self.shading_mode = 0
        self.projection_mode = 0
        self.mouse_pressed= False
        self.last_arcball_point= None
        self.arcball_matrix= np.identity(4, dtype=np.float32)
        self.middle_mouse_pressed = False
        self.last_mouse_y = 0
        self.zoom = 1.0
        self.right_mouse_pressed = False
        self.last_translate_x = 0
        self.last_translate_y = 0
        self.translate_x = 0.0
        self.translate_y = 0.0
        self.key_rotation_matrix = np.identity(4, dtype=np.float32)
        self.key_rotation_step = 10



    def init_GL(self):
        # setup buffer (vertices, colors, normals, ...)
        self.gen_buffers()

        # setup shader
        glBindVertexArray(self.vertex_array)
        vertex_shader       = open("shader.vert","r").read()
        fragment_shader     = open("shader.frag","r").read()
        vertex_prog         = compileShader(vertex_shader, GL_VERTEX_SHADER)
        frag_prog           = compileShader(fragment_shader, GL_FRAGMENT_SHADER)
        self.shader_program = compileProgram(vertex_prog, frag_prog)

        # unbind vertex array to bind it again in method draw
        glBindVertexArray(0)

 
    def gen_buffers(self):
        # TODO: 
        # 1. Load geometry from file and calc normals if not available
        if len(sys.argv) < 2:
            print("Fehler: Bitte übergebe eine Datei als Argument.")
            sys.exit(1)

        # Der erste Parameter (Index 0 ist der Skriptname själv)
        dateipfad = sys.argv[1]

        v=[]
        vn=[]
        vt=[]
        f=[]

        try:
            with open(dateipfad,"r") as datei:
                for line in datei:
                    if line.startswith("vn"):
                        parts=line.split()
                        vn.append([float(parts[1]),float(parts[2]),float(parts[3])])
                    elif line.startswith("vt"):
                        parts=line.split()
                        vt.append([float(parts[1]),float(parts[2])])
                    elif line.startswith("v"):
                        parts=line.split()
                        v.append([float(parts[1]),float(parts[2]),float(parts[3])])
                    elif line.startswith("f"):
                        parts = line.split()
                        face = []
                        for part in parts[1:]:
                            if "//" in part:
                                # Format: v//vn
                                v_index, vn_index = part.split("//")
                                face.append([int(v_index), None, int(vn_index)])
                            elif "/" in part:
                                # Format: v/vt/vn 
                                v_index, vt_index,  vn_index = part.split("/")
                                face.append([int(v_index), int(vt_index), int(vn_index)])
                            else:
                                # Format: nur v
                                face.append([int(part), None, None])
                        f.append(face)
        except FileNotFoundError:
            print(f"Fehler: Die Datei '{dateipfad}' wurde nicht gefunden.")

        hat_vt=len(vt)>0
        hat_vn=len(vn)>0
        anzahl_ecken=0
        for face in f:
            if len(face)>anzahl_ecken:
                anzahl_ecken=len(face)
        anzahl_vertices=len(v)
        anzahl_faces=len(f)

        kanten=[]
        for face in f:
            punkt_ids=[]
            for eintrag in face:
                punkt_ids.append(eintrag[0])
            
            for i in range(len(punkt_ids)):
                a=punkt_ids[i]
                b=punkt_ids[(i+1)%len(punkt_ids)]
                if a<b:
                    kante=(a,b)
                else:
                    kante=(b,a)
                kanten.append(kante)
        eindeutige_kanten=set(kanten)
        anzahl_edges=len(eindeutige_kanten)

        dreiecke=[]
        for face in f:
            laengeFace=len(face)
            if laengeFace == 3:
                dreiecke.append(face)
            elif laengeFace>3:
                for i in range(1,laengeFace-1):
                    dreieck=(face[0],face[i],face[i+1])
                    dreiecke.append(dreieck)


        def sub(x,a):
            return (x[0]-a[0],x[1]-a[1],x[2]-a[2])

        def kreuz(ba,ca):
            x=(ba[1]*ca[2])-(ba[2]*ca[1])
            y=(ba[2]*ca[0])-(ba[0]*ca[2])
            z=(ba[0]*ca[1])-(ba[1]*ca[0])
            return (x,y,z)

        def betrag(v):
            laenge=math.sqrt(pow(v[0],2)+pow(v[1],2)+pow(v[2],2))
            return laenge

        def normieren(v):
            laenge=betrag(v)
            if laenge != 0:
                return (v[0]/laenge,v[1]/laenge,v[2]/laenge)
            return (0.0,0.0,0.0)

        if hat_vn is False:
            berechne_normalen=[]
            for i in range(len(v)):
                berechne_normalen.append([0.0,0.0,0.0]) 

            for dreieck in dreiecke:
                a_id=dreieck[0][0]
                b_id=dreieck[1][0]
                c_id=dreieck[2][0]
                
                a=v[a_id-1]
                b=v[b_id-1]
                c=v[c_id-1]

                ba=sub(b,a)
                ca=sub(c,a)

                kreuzBaCa=kreuz(ba,ca)

                laenge=betrag(kreuzBaCa)

                n=(kreuzBaCa[0]/laenge,kreuzBaCa[1]/laenge,kreuzBaCa[2]/laenge)

                berechne_normalen[a_id-1][0]+=n[0]
                berechne_normalen[a_id-1][1]+=n[1]
                berechne_normalen[a_id-1][2]+=n[2]

                berechne_normalen[b_id-1][0]+=n[0]
                berechne_normalen[b_id-1][1]+=n[1]
                berechne_normalen[b_id-1][2]+=n[2]

                berechne_normalen[c_id-1][0]+=n[0]
                berechne_normalen[c_id-1][1]+=n[1]
                berechne_normalen[c_id-1][2]+=n[2]

            for i in range(len(berechne_normalen)):
                berechne_normalen[i]=normieren(berechne_normalen[i])
            
            vn=berechne_normalen

        print("Texturkoordinaten vorhanden:", hat_vt)
        print("Normalen vorhanden:", hat_vn)
        print("Maximale Anzahl Ecken pro Polygon:", anzahl_ecken)
        print("Anzahl Vertices:", anzahl_vertices)
        print("Anzahl Faces:", anzahl_faces)
        print("Anzahl Edges:", anzahl_edges)

        # 2. Load geometry and normals in buffer objects


        # generate vertex array object
        self.vertex_array = glGenVertexArrays(1)
        glBindVertexArray(self.vertex_array)

        # generate and fill buffer with vertex positions (attribute 0)
        #positions = np.array([  0.0,  0.58,  0.0, # 0. vertex
        #                       -0.5, -0.29,  0.0, # 1. vertex
         #                       0.5, -0.29,  0.0, # 2. vertex
          #                      0.0,  0.00, -0.58 # 3. vertex
           #                     ], dtype=np.float32)
        positions = np.array(v,dtype=np.float32)
        
        minimum=positions.min(axis=0)
        maximum=positions.max(axis=0)

        center=(minimum+maximum)/2.0
        size=maximum-minimum
        max_size =np.max(size)

        positions=positions-center
        positions=positions/max_size


        render_positions=[]
        render_normals=[]

        for dreieck in dreiecke:
            for point in dreieck:
                vertex_index= point[0] - 1

                render_positions.append(positions[vertex_index])

                if point[2] is not None:
                    normal_index= point[2] - 1
                    render_normals.append(vn[normal_index])
                else:
                    render_normals.append(vn[vertex_index])

        positions = np.array(render_positions,dtype=np.float32)

        pos_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, pos_buffer)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
 
        # generate and fill buffer with vertex colors (attribute 1)
        #colors = np.array([ 1.0, 0.0, 0.0, # 0. color
         #                   0.0, 1.0, 0.0, # 1. color
          #                  0.0, 0.0, 1.0, # 2. color
           #                 1.0, 1.0, 1.0  # 3. color
            #                ], dtype=np.float32)
        colors=np.zeros_like(positions, dtype=np.float32)
        colors[:,0]=0.8
        colors[:,1]=0.8
        colors[:,2]=0.8

        col_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, col_buffer)
        glBufferData(GL_ARRAY_BUFFER, colors.nbytes, colors, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)

        #normals buffer
        normals=np.array(render_normals,dtype=np.float32)
        normal_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, normal_buffer)
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(2)

        # generate index buffer (for triangle strip)
        #self.indices = np.array([0, 1, 2, 3, 0, 1], dtype=np.int32)
        self.indices = np.arange(len(positions), dtype=np.uint32)


        ind_buffer_object = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ind_buffer_object)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        # unbind buffers to bind again in draw()
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)



    def set_size(self, width, height):
        self.width = width
        self.height = height

    def projectOnSphere(self, x, y, r):
        x, y = x- self.width/2.0, self.height/2.0- y
        a = min(r*r, x**2 + y**2)
        z = math.sqrt(r*r- a)
        l = math.sqrt(x**2 + y**2 + z**2)
        return np.array([x/l, y/l, z/l], dtype=np.float32)

    def draw(self):
        # TODO:
        # 1. Render geometry 
        #    (a) just as a wireframe model and 
        #    with 
        #    (b) a shader that realize Gouraud Shading
        #    (c) a shader that realize Phong Shading
        if self.shading_mode == 0:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        # 2. Rotate object around the x, y, z axis using the keys x, y, z
        # 3. Rotate object with the mouse by realizing the arcball metaphor as 
        #    well as scaling an translation
        # 4. Realize Shadow Mapping
        # 
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.animate:
            # increment rotation angle in each frame
            self.angle += self.angle_increment
    
        # setup matrices
        #projection = perspective(45.0, self.width/self.height, 1.0, 5.0)
        aspect = self.width/self.height
        if self.projection_mode == 0:
            projection = perspective(45.0, aspect, 1.0, 5.0)
        else:
            projection = ortho(-aspect, aspect, -1.0, 1.0, 1.0, 5.0)
        view       = look_at(0,0,2, 0,0,0, 0,1,0)
        model = translate(self.translate_x, self.translate_y, 0.0) @ self.arcball_matrix @ self.key_rotation_matrix @ rotate_y(self.angle) @ scale(self.zoom, self.zoom, self.zoom)
        mvp_matrix = projection @ view @ model
        
        modelview_matrix= view @ model

        # enable shader & set uniforms
        glUseProgram(self.shader_program)
        
        # determine location of uniform variable varName
        varLocationMVP = glGetUniformLocation(self.shader_program, 'modelview_projection_matrix')
        
        varLocationMV = glGetUniformLocation(self.shader_program, 'modelview_matrix')
        # pass value to shader
        glUniformMatrix4fv(varLocationMVP, 1, GL_TRUE, mvp_matrix)

        glUniformMatrix4fv(varLocationMV, 1, GL_TRUE, modelview_matrix)

        varLocationShading = glGetUniformLocation(self.shader_program, 'shading_mode')
        glUniform1i(varLocationShading, self.shading_mode)

        # enable vertex array & draw triangle(s)
        glBindVertexArray(self.vertex_array)
        #glDrawElements(GL_TRIANGLE_STRIP, self.indices.nbytes//4, GL_UNSIGNED_INT, None)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT,None)

        # unbind the shader and vertex array state
        glUseProgram(0)
        glBindVertexArray(0)
        


class RenderWindow:
    """
        GLFW Rendering window class
    """

    def __init__(self, scene):
        # initialize GLFW
        if not glfw.init():
            sys.exit(EXIT_FAILURE)

        # request window with old OpenGL 3.2
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)

        # make a window
        self.width, self.height = scene.width, scene.height
        self.aspect = self.width / self.height
        self.window = glfw.create_window(self.width, self.height, scene.scenetitle, None, None)
        if not self.window:
            glfw.terminate()
            sys.exit(EXIT_FAILURE)

        # Make the window's context current
        glfw.make_context_current(self.window)

        # initialize GL
        self.init_GL()

        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.on_mouse_button)
        glfw.set_cursor_pos_callback(self.window, self.on_mouse_move)
        glfw.set_cursor_pos_callback(self.window, self.on_mouse_move)
        glfw.set_key_callback(self.window, self.on_keyboard)
        glfw.set_window_size_callback(self.window, self.on_size)

        # create scene
        self.scene = scene  
        if not self.scene:
            glfw.terminate()
            sys.exit(EXIT_FAILURE)

        self.scene.init_GL()

        # exit flag
        self.exitNow = False


    def init_GL(self):
        # debug: print GL and GLS version
        # print('Vendor       : %s' % glGetString(GL_VENDOR))
        # print('OpenGL Vers. : %s' % glGetString(GL_VERSION))
        # print('GLSL Vers.   : %s' % glGetString(GL_SHADING_LANGUAGE_VERSION))
        # print('Renderer     : %s' % glGetString(GL_RENDERER))

        # set background color to black
        glClearColor(0, 0, 0, 0)     

        # Enable depthtest
        glEnable(GL_DEPTH_TEST)

    def on_mouse_button(self, win, button, action, mods):
        print("mouse button: ", win, button, action, mods)
        # TODO: realize arcball metaphor for rotations as well as
        #       scaling and translation paralell to the image plane,
        #       with the mouse. 
        x, y = glfw.get_cursor_pos(win)

        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self.scene.mouse_pressed = True
            r = min(self.scene.width, self.scene.height) / 2.0
            self.scene.last_arcball_point = self.scene.projectOnSphere(x, y, r)

        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.RELEASE:
            self.scene.mouse_pressed = False
            self.scene.last_arcball_point = None

        if button == glfw.MOUSE_BUTTON_MIDDLE and action == glfw.PRESS:
            self.scene.middle_mouse_pressed = True
            self.scene.last_mouse_y = y

        if button == glfw.MOUSE_BUTTON_MIDDLE and action == glfw.RELEASE:
            self.scene.middle_mouse_pressed = False

        if button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.PRESS:
            self.scene.right_mouse_pressed = True
            self.scene.last_translate_x = x
            self.scene.last_translate_y = y

        if button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.RELEASE:
            self.scene.right_mouse_pressed = False


    def on_mouse_move(self, win, x, y):
        if self.scene.mouse_pressed:
            r = min(self.scene.width, self.scene.height) / 2.0

            p1 = self.scene.last_arcball_point
            p2 = self.scene.projectOnSphere(x, y, r)

            axis = np.cross(p1, p2)
            axis_length = np.linalg.norm(axis)

            if axis_length > 0.0001:
                dot = np.dot(p1, p2)
                dot = max(-1.0, min(1.0, dot))

                angle = math.degrees(math.acos(dot))

                rotation = rotate(angle, axis)
                self.scene.arcball_matrix = rotation @ self.scene.arcball_matrix

            self.scene.last_arcball_point = p2
        
        if self.scene.middle_mouse_pressed:
            dy = y - self.scene.last_mouse_y

            zoom_speed = 0.01
            self.scene.zoom = self.scene.zoom * (1.0 - dy * zoom_speed)

            self.scene.zoom = max(0.1, min(self.scene.zoom, 5.0))

            self.scene.last_mouse_y = y
        
        if self.scene.right_mouse_pressed:
            dx = x - self.scene.last_translate_x
            dy = y - self.scene.last_translate_y

            translation_speed = 2.0 / self.scene.height

            self.scene.translate_x += dx * translation_speed
            self.scene.translate_y -= dy * translation_speed

            self.scene.last_translate_x = x
            self.scene.last_translate_y = y


    def on_keyboard(self, win, key, scancode, action, mods):
        print("keyboard: ", win, key, scancode, action, mods)
        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            if key == glfw.KEY_A:
                self.scene.animate = not self.scene.animate
            if key == glfw.KEY_P:
                # TODO:
                self.scene.projection_mode = (self.scene.projection_mode + 1) % 2
                print("toggle projection: orthographic / perspective ")
            if key == glfw.KEY_S:
                # TODO:
                self.scene.shading_mode = (self.scene.shading_mode + 1) % 3
                print("toggle shading: wireframe, grouraud, phong")
            if key == glfw.KEY_X:
                # TODO:
                self.scene.key_rotation_matrix = rotate_x(self.scene.key_rotation_step) @ self.scene.key_rotation_matrix
                print("rotate: around x-axis")
            if key == glfw.KEY_Y:
                # TODO:
                self.scene.key_rotation_matrix = rotate_y(self.scene.key_rotation_step) @ self.scene.key_rotation_matrix
                print("rotate: around y-axis")
            if key == glfw.KEY_Z:
                # TODO:
                self.scene.key_rotation_matrix = rotate_z(self.scene.key_rotation_step) @ self.scene.key_rotation_matrix
                print("rotate: around z-axis")


    def on_size(self, win, width, height):
        self.scene.set_size(width, height)


    def run(self):
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # poll for and process events
            glfw.poll_events()

            # setup viewport
            width, height = glfw.get_framebuffer_size(self.window)
            glViewport(0, 0, width, height);

            # call the rendering function
            self.scene.draw()
            
            # swap front and back buffer
            glfw.swap_buffers(self.window)

        # end
        glfw.terminate()



# main function
if __name__ == '__main__':

    print("presse 'a' to toggle animation...")

    # set size of render viewport
    width, height = 640, 480

    # instantiate a scene
    scene = Scene(width, height)

    # pass the scene to a render window ... 
    rw = RenderWindow(scene)

    # ... and start main loop
    rw.run()
