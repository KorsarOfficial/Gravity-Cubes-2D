import taichi as ti
import config
import numpy as np
import moderngl
import moderngl_window as mglw
from moderngl_window.context.pyglet.window import Window
from moderngl_window import resources
from pathlib import Path
import random
import time

# Класс для хранения и управления частицами
class ParticleSystem:
    def __init__(self, renderer):
        self.renderer = renderer
        self.max_particles = 100
        self.particles = []
        self.lifetime = 1.0  # в секундах
        
    def emit_particles(self, position, color, count=10):
        for _ in range(count):
            # Если достигли максимума частиц, заменяем самую старую
            if len(self.particles) >= self.max_particles:
                self.particles.pop(0)
                
            # Создаем новую частицу
            particle = {
                'position': [position[0], position[1], 0.0],
                'velocity': [
                    random.uniform(-2.0, 2.0),
                    random.uniform(0.5, 3.0),
                    0.0
                ],
                'size': random.uniform(0.05, 0.2),
                'color': [
                    color[0] + random.uniform(-0.1, 0.1),
                    color[1] + random.uniform(-0.1, 0.1),
                    color[2] + random.uniform(-0.1, 0.1),
                    1.0
                ],
                'creation_time': time.time(),
                'lifetime': random.uniform(0.5, self.lifetime)
            }
            self.particles.append(particle)
    
    def update(self, dt):
        # Текущее время
        current_time = time.time()
        
        # Обновляем каждую частицу
        i = 0
        while i < len(self.particles):
            particle = self.particles[i]
            
            # Проверяем истечение времени жизни
            age = current_time - particle['creation_time']
            if age >= particle['lifetime']:
                # Удаляем частицу
                self.particles.pop(i)
                continue
                
            # Обновляем положение частицы
            particle['position'][0] += particle['velocity'][0] * dt
            particle['position'][1] += particle['velocity'][1] * dt
            
            # Применяем гравитацию
            particle['velocity'][1] -= 5.0 * dt
            
            # Обновляем прозрачность (выцветание)
            remaining_life = 1.0 - age / particle['lifetime']
            particle['color'][3] = remaining_life
            
            # Уменьшаем размер с течением времени
            particle['size'] *= (1.0 - 0.5 * dt)
            
            i += 1
    
    def render(self):
        # Рендерим каждую частицу
        for particle in self.particles:
            self.renderer.draw_cube(
                particle['position'],
                [particle['size']] * 3,
                particle['color']
            )

# Renderer class for the gravity cubes simulation
class Renderer(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Gravity Cubes"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Shaders
        self.shader_dir = 'shaders'
        
        # Создаем шейдеры вручную, так как файлов больше нет
        self.create_shaders()
        
        # Create cube mesh
        self.cube_vao = self.create_cube_vao()
        
        # Mode flag: 2D or 3D
        self.is_2d = False
        
        # Camera parameters
        self.camera_pos = np.array([0.0, 0.0, 5.0])
        self.camera_front = np.array([0.0, 0.0, -1.0])
        self.camera_up = np.array([0.0, 1.0, 0.0])
        self.camera_right = np.array([1.0, 0.0, 0.0])
        
        # Mouse control
        self.yaw = -90.0
        self.pitch = 0.0
        self.last_x = self.wnd.width / 2
        self.last_y = self.wnd.height / 2
        self.first_mouse = True
        
        # Projection matrix
        self.aspect_ratio = self.wnd.width / self.wnd.height
        self.projection = self.get_projection_matrix()
        
        # Градиентный фон
        self.background_colors = [
            (0.05, 0.1, 0.2, 1.0),   # Темно-синий внизу
            (0.2, 0.4, 0.6, 1.0)     # Голубой сверху
        ]
        
        # Создаем систему частиц
        self.particle_system = ParticleSystem(self)
        
        # Mouse capture
        self.cursor = self.mouse_exclusivity = True
        
    # Создаем шейдеры вручную
    def create_shaders(self):
        # Вершинный шейдер
        vertex_shader = """
            #version 330 core
            
            uniform mat4 model;
            uniform mat4 view;
            uniform mat4 projection;
            
            in vec3 in_position;
            in vec3 in_normal;
            
            out vec3 normal;
            out vec3 frag_pos;
            
            void main() {
                // For 2D, we use the full transformation pipeline as usual
                gl_Position = projection * view * model * vec4(in_position, 1.0);
                
                // Pass normal and position to fragment shader (used for lighting)
                normal = normalize(mat3(transpose(inverse(model))) * in_normal);
                frag_pos = vec3(model * vec4(in_position, 1.0));
            }
        """
        
        # Фрагментный шейдер
        fragment_shader = """
            #version 330 core
            
            uniform vec4 color;
            
            in vec3 normal;
            in vec3 frag_pos;
            
            out vec4 fragColor;
            
            void main() {
                // Basic lighting for 2D
                float ambient_strength = 0.7;  // Увеличил ambient для лучшей видимости в 2D
                vec3 ambient = ambient_strength * vec3(1.0, 1.0, 1.0);
                
                // Simple directional light from top-right
                vec3 light_dir = normalize(vec3(1.0, 1.0, 0.5));
                float diff = max(dot(normal, light_dir), 0.0);
                vec3 diffuse = diff * vec3(0.5, 0.5, 0.5);
                
                // Combine lighting
                vec3 result = (ambient + diffuse) * color.rgb;
                
                // Output final color with alpha
                fragColor = vec4(result, color.a);
            }
        """
        
        # Создаем шейдерную программу
        self.cube_shader = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )
    
    # Static method to create a Renderer instance from an existing WindowConfig instance
    @staticmethod
    def _wrap(window_config):
        renderer = Renderer.__new__(Renderer)
        
        # Copy all attributes from window_config
        renderer.ctx = window_config.ctx
        renderer.wnd = window_config.wnd
        
        # Initialize renderer properties
        renderer.shader_dir = 'shaders'
        renderer.is_2d = False
        renderer.camera_pos = np.array([0.0, 0.0, 5.0])
        renderer.camera_front = np.array([0.0, 0.0, -1.0])
        renderer.camera_up = np.array([0.0, 1.0, 0.0])
        renderer.camera_right = np.array([1.0, 0.0, 0.0])
        renderer.aspect_ratio = window_config.wnd.width / window_config.wnd.height
        renderer.projection = np.identity(4)  # Will be updated later
        
        # Градиентный фон
        renderer.background_colors = [
            (0.05, 0.1, 0.2, 1.0),   # Темно-синий внизу
            (0.2, 0.4, 0.6, 1.0)     # Голубой сверху
        ]
        
        # Создаем шейдеры вручную
        # Вершинный шейдер
        vertex_shader = """
            #version 330 core
            
            uniform mat4 model;
            uniform mat4 view;
            uniform mat4 projection;
            
            in vec3 in_position;
            in vec3 in_normal;
            
            out vec3 normal;
            out vec3 frag_pos;
            
            void main() {
                // For 2D, we use the full transformation pipeline as usual
                gl_Position = projection * view * model * vec4(in_position, 1.0);
                
                // Pass normal and position to fragment shader (used for lighting)
                normal = normalize(mat3(transpose(inverse(model))) * in_normal);
                frag_pos = vec3(model * vec4(in_position, 1.0));
            }
        """
        
        # Фрагментный шейдер
        fragment_shader = """
            #version 330 core
            
            uniform vec4 color;
            
            in vec3 normal;
            in vec3 frag_pos;
            
            out vec4 fragColor;
            
            void main() {
                // Basic lighting for 2D
                float ambient_strength = 0.7;  // Увеличил ambient для лучшей видимости в 2D
                vec3 ambient = ambient_strength * vec3(1.0, 1.0, 1.0);
                
                // Simple directional light from top-right
                vec3 light_dir = normalize(vec3(1.0, 1.0, 0.5));
                float diff = max(dot(normal, light_dir), 0.0);
                vec3 diffuse = diff * vec3(0.5, 0.5, 0.5);
                
                // Combine lighting
                vec3 result = (ambient + diffuse) * color.rgb;
                
                // Output final color with alpha
                fragColor = vec4(result, color.a);
            }
        """
        
        # Создаем шейдерную программу
        renderer.cube_shader = window_config.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )
        
        # Создаем VAO для куба
        # Cube vertices (8 corners)
        vertices = np.array([
            # Front face
            -0.5, -0.5,  0.5,  0.0,  0.0,  1.0,
             0.5, -0.5,  0.5,  0.0,  0.0,  1.0,
             0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
            -0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
            # Back face
            -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,
             0.5, -0.5, -0.5,  0.0,  0.0, -1.0,
             0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
            -0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
            # Top face
            -0.5,  0.5, -0.5,  0.0,  1.0,  0.0,
             0.5,  0.5, -0.5,  0.0,  1.0,  0.0,
             0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
            -0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
            # Bottom face
            -0.5, -0.5, -0.5,  0.0, -1.0,  0.0,
             0.5, -0.5, -0.5,  0.0, -1.0,  0.0,
             0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
            -0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
            # Right face
             0.5, -0.5, -0.5,  1.0,  0.0,  0.0,
             0.5,  0.5, -0.5,  1.0,  0.0,  0.0,
             0.5,  0.5,  0.5,  1.0,  0.0,  0.0,
             0.5, -0.5,  0.5,  1.0,  0.0,  0.0,
            # Left face
            -0.5, -0.5, -0.5, -1.0,  0.0,  0.0,
            -0.5,  0.5, -0.5, -1.0,  0.0,  0.0,
            -0.5,  0.5,  0.5, -1.0,  0.0,  0.0,
            -0.5, -0.5,  0.5, -1.0,  0.0,  0.0,
        ], dtype='f4')
        
        # Indices for drawing the 12 triangles (6 faces * 2 triangles)
        indices = np.array([
            0, 1, 2, 2, 3, 0,  # Front face
            4, 5, 6, 6, 7, 4,  # Back face
            8, 9, 10, 10, 11, 8,  # Top face
            12, 13, 14, 14, 15, 12,  # Bottom face
            16, 17, 18, 18, 19, 16,  # Right face
            20, 21, 22, 22, 23, 20,  # Left face
        ], dtype='i4')
        
        # Create VAO, VBO and EBO
        try:
            vbo = window_config.ctx.buffer(vertices.tobytes())
            ebo = window_config.ctx.buffer(indices.tobytes())
            
            renderer.cube_vao = window_config.ctx.vertex_array(
                renderer.cube_shader,
                [
                    (vbo, '3f 3f', 'in_position', 'in_normal'),
                ],
                ebo
            )
        except Exception as e:
            print(f"Error creating cube VAO: {e}")
            raise
            
        # Создаем систему частиц
        renderer.particle_system = ParticleSystem(renderer)
        
        return renderer
    
    # Load program from files (for _wrap method)
    @staticmethod
    def load_program(name, window_config):
        # Больше не используем файлы шейдеров, вместо этого используем строковые константы
        if name == 'cube':
            # Вершинный шейдер
            vertex_shader = """
                #version 330 core
                
                uniform mat4 model;
                uniform mat4 view;
                uniform mat4 projection;
                
                in vec3 in_position;
                in vec3 in_normal;
                
                out vec3 normal;
                out vec3 frag_pos;
                
                void main() {
                    // For 2D, we use the full transformation pipeline as usual
                    gl_Position = projection * view * model * vec4(in_position, 1.0);
                    
                    // Pass normal and position to fragment shader (used for lighting)
                    normal = normalize(mat3(transpose(inverse(model))) * in_normal);
                    frag_pos = vec3(model * vec4(in_position, 1.0));
                }
            """
            
            # Фрагментный шейдер
            fragment_shader = """
                #version 330 core
                
                uniform vec4 color;
                
                in vec3 normal;
                in vec3 frag_pos;
                
                out vec4 fragColor;
                
                void main() {
                    // Basic lighting for 2D
                    float ambient_strength = 0.7;  // Увеличил ambient для лучшей видимости в 2D
                    vec3 ambient = ambient_strength * vec3(1.0, 1.0, 1.0);
                    
                    // Simple directional light from top-right
                    vec3 light_dir = normalize(vec3(1.0, 1.0, 0.5));
                    float diff = max(dot(normal, light_dir), 0.0);
                    vec3 diffuse = diff * vec3(0.5, 0.5, 0.5);
                    
                    // Combine lighting
                    vec3 result = (ambient + diffuse) * color.rgb;
                    
                    // Output final color with alpha
                    fragColor = vec4(result, color.a);
                }
            """
            
            return window_config.ctx.program(
                vertex_shader=vertex_shader,
                fragment_shader=fragment_shader
            )
        else:
            raise ValueError(f"Unknown shader program: {name}")
    
    # Create VAO for the cube (for _wrap method)
    @staticmethod
    def create_cube_vao(window_config):
        # Cube vertices (8 corners)
        vertices = np.array([
            # Front face
            -0.5, -0.5,  0.5,  0.0,  0.0,  1.0,
             0.5, -0.5,  0.5,  0.0,  0.0,  1.0,
             0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
            -0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
            # Back face
            -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,
             0.5, -0.5, -0.5,  0.0,  0.0, -1.0,
             0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
            -0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
            # Top face
            -0.5,  0.5, -0.5,  0.0,  1.0,  0.0,
             0.5,  0.5, -0.5,  0.0,  1.0,  0.0,
             0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
            -0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
            # Bottom face
            -0.5, -0.5, -0.5,  0.0, -1.0,  0.0,
             0.5, -0.5, -0.5,  0.0, -1.0,  0.0,
             0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
            -0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
            # Right face
             0.5, -0.5, -0.5,  1.0,  0.0,  0.0,
             0.5,  0.5, -0.5,  1.0,  0.0,  0.0,
             0.5,  0.5,  0.5,  1.0,  0.0,  0.0,
             0.5, -0.5,  0.5,  1.0,  0.0,  0.0,
            # Left face
            -0.5, -0.5, -0.5, -1.0,  0.0,  0.0,
            -0.5,  0.5, -0.5, -1.0,  0.0,  0.0,
            -0.5,  0.5,  0.5, -1.0,  0.0,  0.0,
            -0.5, -0.5,  0.5, -1.0,  0.0,  0.0,
        ], dtype='f4')
        
        # Indices for drawing the 12 triangles (6 faces * 2 triangles)
        indices = np.array([
            0, 1, 2, 2, 3, 0,  # Front face
            4, 5, 6, 6, 7, 4,  # Back face
            8, 9, 10, 10, 11, 8,  # Top face
            12, 13, 14, 14, 15, 12,  # Bottom face
            16, 17, 18, 18, 19, 16,  # Right face
            20, 21, 22, 22, 23, 20,  # Left face
        ], dtype='i4')
        
        # Create VAO, VBO and EBO
        vbo = window_config.ctx.buffer(vertices.tobytes())
        ebo = window_config.ctx.buffer(indices.tobytes())
        
        # Создаем шейдер, используя встроенные строки вместо файлов
        shader = Renderer.load_program('cube', window_config)
        
        return window_config.ctx.vertex_array(
            shader,
            [
                (vbo, '3f 3f', 'in_position', 'in_normal'),
            ],
            ebo
        )
    
    def load_program(self, name):
        # Больше не используем файлы шейдеров, вместо этого используем строковые константы
        if name == 'cube':
            # Вершинный шейдер
            vertex_shader = """
                #version 330 core
                
                uniform mat4 model;
                uniform mat4 view;
                uniform mat4 projection;
                
                in vec3 in_position;
                in vec3 in_normal;
                
                out vec3 normal;
                out vec3 frag_pos;
                
                void main() {
                    // For 2D, we use the full transformation pipeline as usual
                    gl_Position = projection * view * model * vec4(in_position, 1.0);
                    
                    // Pass normal and position to fragment shader (used for lighting)
                    normal = normalize(mat3(transpose(inverse(model))) * in_normal);
                    frag_pos = vec3(model * vec4(in_position, 1.0));
                }
            """
            
            # Фрагментный шейдер
            fragment_shader = """
                #version 330 core
                
                uniform vec4 color;
                
                in vec3 normal;
                in vec3 frag_pos;
                
                out vec4 fragColor;
                
                void main() {
                    // Basic lighting for 2D
                    float ambient_strength = 0.7;  // Увеличил ambient для лучшей видимости в 2D
                    vec3 ambient = ambient_strength * vec3(1.0, 1.0, 1.0);
                    
                    // Simple directional light from top-right
                    vec3 light_dir = normalize(vec3(1.0, 1.0, 0.5));
                    float diff = max(dot(normal, light_dir), 0.0);
                    vec3 diffuse = diff * vec3(0.5, 0.5, 0.5);
                    
                    // Combine lighting
                    vec3 result = (ambient + diffuse) * color.rgb;
                    
                    // Output final color with alpha
                    fragColor = vec4(result, color.a);
                }
            """
            
            return self.ctx.program(
                vertex_shader=vertex_shader,
                fragment_shader=fragment_shader
            )
        else:
            raise ValueError(f"Unknown shader program: {name}")
    
    # Create VAO for the cube
    def create_cube_vao(self):
        # Cube vertices (8 corners)
        vertices = np.array([
            # Front face
            -0.5, -0.5,  0.5,  0.0,  0.0,  1.0,
             0.5, -0.5,  0.5,  0.0,  0.0,  1.0,
             0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
            -0.5,  0.5,  0.5,  0.0,  0.0,  1.0,
            # Back face
            -0.5, -0.5, -0.5,  0.0,  0.0, -1.0,
             0.5, -0.5, -0.5,  0.0,  0.0, -1.0,
             0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
            -0.5,  0.5, -0.5,  0.0,  0.0, -1.0,
            # Top face
            -0.5,  0.5, -0.5,  0.0,  1.0,  0.0,
             0.5,  0.5, -0.5,  0.0,  1.0,  0.0,
             0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
            -0.5,  0.5,  0.5,  0.0,  1.0,  0.0,
            # Bottom face
            -0.5, -0.5, -0.5,  0.0, -1.0,  0.0,
             0.5, -0.5, -0.5,  0.0, -1.0,  0.0,
             0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
            -0.5, -0.5,  0.5,  0.0, -1.0,  0.0,
            # Right face
             0.5, -0.5, -0.5,  1.0,  0.0,  0.0,
             0.5,  0.5, -0.5,  1.0,  0.0,  0.0,
             0.5,  0.5,  0.5,  1.0,  0.0,  0.0,
             0.5, -0.5,  0.5,  1.0,  0.0,  0.0,
            # Left face
            -0.5, -0.5, -0.5, -1.0,  0.0,  0.0,
            -0.5,  0.5, -0.5, -1.0,  0.0,  0.0,
            -0.5,  0.5,  0.5, -1.0,  0.0,  0.0,
            -0.5, -0.5,  0.5, -1.0,  0.0,  0.0,
        ], dtype='f4')
        
        # Indices for drawing the 12 triangles (6 faces * 2 triangles)
        indices = np.array([
            0, 1, 2, 2, 3, 0,  # Front face
            4, 5, 6, 6, 7, 4,  # Back face
            8, 9, 10, 10, 11, 8,  # Top face
            12, 13, 14, 14, 15, 12,  # Bottom face
            16, 17, 18, 18, 19, 16,  # Right face
            20, 21, 22, 22, 23, 20,  # Left face
        ], dtype='i4')
        
        # Create VAO, VBO and EBO
        vbo = self.ctx.buffer(vertices.tobytes())
        ebo = self.ctx.buffer(indices.tobytes())
        
        return self.ctx.vertex_array(
            self.cube_shader,
            [
                (vbo, '3f 3f', 'in_position', 'in_normal'),
            ],
            ebo
        )
    
    # Handle mouse movement
    def mouse_position_event(self, x, y, dx, dy):
        if self.first_mouse:
            self.last_x = x
            self.last_y = y
            self.first_mouse = False
            
        dx = x - self.last_x
        dy = self.last_y - y  # Reversed since y-coordinates go from bottom to top
        
        self.last_x = x
        self.last_y = y
        
        sensitivity = 0.1
        dx *= sensitivity
        dy *= sensitivity
        
        self.yaw += dx
        self.pitch += dy
        
        # Make sure that when pitch is out of bounds, screen doesn't get flipped
        if self.pitch > 89.0:
            self.pitch = 89.0
        if self.pitch < -89.0:
            self.pitch = -89.0
            
        # Update the camera vectors
        self.update_camera_vectors()
    
    # Update camera vectors based on Euler angles
    def update_camera_vectors(self):
        # Calculate new front vector
        direction = np.array([
            np.cos(np.radians(self.yaw)) * np.cos(np.radians(self.pitch)),
            np.sin(np.radians(self.pitch)),
            np.sin(np.radians(self.yaw)) * np.cos(np.radians(self.pitch))
        ])
        
        self.camera_front = direction / np.linalg.norm(direction)
        self.camera_right = np.cross(self.camera_front, np.array([0.0, 1.0, 0.0]))
        self.camera_right = self.camera_right / np.linalg.norm(self.camera_right)
        self.camera_up = np.cross(self.camera_right, self.camera_front)
        self.camera_up = self.camera_up / np.linalg.norm(self.camera_up)
    
    # Handle keyboard input
    def key_event(self, key, action, modifiers):
        if action == self.wnd.keys.ACTION_PRESS:
            if key == self.wnd.keys.ESCAPE:
                self.wnd.close()
            
        # Camera movement
        camera_speed = 0.1
        if self.wnd.keys.W in self.wnd.keys.key_states:
            self.camera_pos += camera_speed * self.camera_front
        if self.wnd.keys.S in self.wnd.keys.key_states:
            self.camera_pos -= camera_speed * self.camera_front
        if self.wnd.keys.A in self.wnd.keys.key_states:
            self.camera_pos -= camera_speed * self.camera_right
        if self.wnd.keys.D in self.wnd.keys.key_states:
            self.camera_pos += camera_speed * self.camera_right
        if self.wnd.keys.SPACE in self.wnd.keys.key_states:
            self.camera_pos += camera_speed * self.camera_up
        if self.wnd.keys.LEFT_SHIFT in self.wnd.keys.key_states:
            self.camera_pos -= camera_speed * self.camera_up
    
    # Get view matrix
    def get_view_matrix(self):
        target = self.camera_pos + self.camera_front
        return np.array(self.look_at(self.camera_pos, target, self.camera_up))
    
    # Get projection matrix
    def get_projection_matrix(self):
        if self.is_2d:
            return self.get_orthographic_projection()
        else:
            return np.array(self.perspective_matrix(45.0, self.aspect_ratio, 0.1, 100.0))
    
    # Get orthographic projection for 2D mode
    def get_orthographic_projection(self):
        # Get camera parameters
        zoom = getattr(self, 'zoom', 0.05)
        position = getattr(self, 'position', [0.0, 0.0])
        
        # Calculate orthographic projection 
        aspect = self.aspect_ratio
        height = 2.0 / zoom
        width = height * aspect
        
        left = -width/2 + position[0]
        right = width/2 + position[0]
        bottom = -height/2 + position[1]
        top = height/2 + position[1]
        near = -1000.0
        far = 1000.0
        
        projection = np.zeros((4, 4), dtype='f4')
        projection[0, 0] = 2.0 / (right - left)
        projection[1, 1] = 2.0 / (top - bottom)
        projection[2, 2] = -2.0 / (far - near)
        projection[0, 3] = -(right + left) / (right - left)
        projection[1, 3] = -(top + bottom) / (top - bottom)
        projection[2, 3] = -(far + near) / (far - near)
        projection[3, 3] = 1.0
        
        return projection
    
    # Load an OBJ model
    def load_model_obj(self, obj_file):
        # For now, just return the existing cube VAO
        # In a real implementation, this would load and parse the OBJ file
        # But for our purposes, we'll just use the cube VAO
        return self.cube_vao
    
    # Toggle between 2D and 3D mode
    def toggle_mode(self):
        self.is_2d = not self.is_2d
        print(f"Mode switched to {'2D' if self.is_2d else '3D'}")
        return self.is_2d
    
    # Set 2D mode params
    def set_2d_params(self, zoom, position):
        self.zoom = zoom
        self.position = position
    
    # Draw a cube at a specific position with a specific size
    def draw_cube(self, position, size, color):
        # Calculate model matrix
        model = np.identity(4)
        
        # Translation
        model[0, 3] = position[0]
        model[1, 3] = position[1]
        model[2, 3] = position[2]
        
        # Scale - проверяем, является ли size списком или одиночным значением
        if isinstance(size, (list, tuple, np.ndarray)):
            model[0, 0] = size[0]  # X scale
            model[1, 1] = size[1]  # Y scale
            model[2, 2] = size[2]  # Z scale
        else:
            # Если size - скалярное значение, применяем его ко всем измерениям
            model[0, 0] = size
            model[1, 1] = size
            model[2, 2] = size
        
        # Set uniforms
        self.cube_shader["model"].write(model.astype('f4').tobytes())
        self.cube_shader["view"].write(self.get_view_matrix().astype('f4').tobytes())
        self.cube_shader["projection"].write(self.projection.astype('f4').tobytes())
        self.cube_shader["color"].value = color
        
        # Draw the cube
        self.cube_vao.render()
    
    # Create a look-at matrix
    def look_at(self, position, target, up):
        forward = position - target
        forward = forward / np.linalg.norm(forward)
        
        right = np.cross(up, forward)
        right = right / np.linalg.norm(right)
        
        up = np.cross(forward, right)
        
        result = np.identity(4)
        result[0, 0] = right[0]
        result[1, 0] = right[1]
        result[2, 0] = right[2]
        result[0, 1] = up[0]
        result[1, 1] = up[1]
        result[2, 1] = up[2]
        result[0, 2] = forward[0]
        result[1, 2] = forward[1]
        result[2, 2] = forward[2]
        result[0, 3] = -np.dot(right, position)
        result[1, 3] = -np.dot(up, position)
        result[2, 3] = -np.dot(forward, position)
        
        return result
    
    # Create a perspective projection matrix
    def perspective_matrix(self, fov_deg, aspect, near, far):
        fov_rad = np.radians(fov_deg)
        f = 1.0 / np.tan(fov_rad / 2.0)
        
        result = np.zeros((4, 4))
        result[0, 0] = f / aspect
        result[1, 1] = f
        result[2, 2] = (far + near) / (near - far)
        result[3, 2] = -1.0
        result[2, 3] = (2.0 * far * near) / (near - far)
        
        return result
    
    # Рисуем градиентный фон
    def draw_gradient_background(self):
        # Очищаем экран базовым цветом
        self.ctx.clear(
            self.background_colors[0][0], 
            self.background_colors[0][1], 
            self.background_colors[0][2], 
            self.background_colors[0][3]
        )
        
        # В будущем можно реализовать более сложный градиент через шейдеры,
        # но пока простой вариант достаточен

    # Clear screen with gradient background
    def clear_screen(self):
        self.draw_gradient_background()
    
    # Resize event handler
    def resize(self, width, height):
        self.width = width
        self.height = height
        self.aspect_ratio = width / height
        self.projection = self.get_projection_matrix()
    
    # Создаем эффект частиц при столкновении
    def create_collision_particles(self, position, color, count=10):
        self.particle_system.emit_particles(position, color, count)
    
    # Update method for particles
    def update(self, dt):
        # Обновляем систему частиц
        self.particle_system.update(dt)
    
    # Render method with particle support
    def render(self, time, frame_time):
        # Update particles
        self.update(frame_time)
        
        # Clear screen with gradient
        self.clear_screen()
        
        # Set blend mode for transparency
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # Render all particles
        self.particle_system.render()

# Initialize the renderer
def create_renderer():
    return Renderer() 