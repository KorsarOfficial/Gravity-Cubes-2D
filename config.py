import taichi as ti
import numpy as np

# Init Taichi
def init_taichi():
    ti.init(arch=ti.gpu)  # Use GPU if available

# Window resolution
resolution = (800, 600)

# Game field dimensions
field_width = 0.8  # relative width (% of screen)
field_height = 0.8  # relative height (% of screen)

# Graphics settings
background_color = ti.Vector([0.1, 0.1, 0.1])

# Градиентный фон
gradient_background = True
gradient_colors = [
    [0.2, 0.7, 0.2],  # Зеленый (верх)
    [0.7, 0.1, 0.1]    # Красный (низ)
]

# Физика
gravity_enabled = True
gravity_strength = 9.8
inertia_enabled = True
friction = 0.98
bounce_factor = 0.7

# Эффекты частиц
particles_enabled = True
particles_count = 10
particles_lifetime = 1.0

# Cube movement speed
move_speed = 0.01
max_speed = 0.02  # Maximum speed for display

# Wall settings
wall_thickness = 0.02
wall_color = ti.Vector([0.3, 0.3, 0.8])  # blue color

# UI settings
button_add_cube = [0.05, 0.05, 0.25, 0.10]  # [x, y, width, height]
show_ui = True
show_fps = True
show_speed = True

# Cube settings
default_cube_size = 0.08
min_cube_size = 0.03
max_cube_size = 0.15
default_cube_color = [0.9, 0.2, 0.3]  # Red

# Preset colors for cubes
preset_colors = [
    [0.9, 0.2, 0.3],  # Red
    [0.2, 0.7, 0.3],  # Green
    [0.3, 0.4, 0.9],  # Blue
    [0.9, 0.7, 0.1],  # Yellow
    [0.8, 0.3, 0.9],  # Purple
    [0.2, 0.8, 0.8],  # Cyan
    [1.0, 0.5, 0.0]   # Orange
]

# Gravity field settings
n_grid = 32  # Grid size for gravity field
gravity_strength = 9.8  # Gravity strength

# Boundary settings
boundary_min = [-10, -10, -10]
boundary_max = [10, 10, 10]

# Cube creation settings
max_cubes = 20
cube_creation_interval = 3.0  # seconds

# Spawn points
spawn_points = [
    [0.5, 0.5],  # Center
    [0.3, 0.2],  # Bottom left
    [0.7, 0.8]   # Top right
]
current_spawn_point = 0

# Target zones
target_zones = [
    [0.7, 0.2, 0.1]  # x, y, radius
]
target_zone_color = ti.Vector([0.2, 0.9, 0.2])  # Green

# Game settings
count_steps = True
count_time = True

# Inner walls: [x1, y1, x2, y2]
inner_wall_data = np.array([
    [0.3, 0.3, 0.7, 0.3],   # horizontal wall
    [0.7, 0.3, 0.7, 0.7],   # vertical wall right
    [0.3, 0.7, 0.3, 0.5],   # vertical wall left top
    [0.3, 0.5, 0.5, 0.5],   # horizontal wall center
], dtype=np.float32)
num_inner_walls = len(inner_wall_data)

# Sound settings
sound_enabled = True
music_enabled = True
sound_volume = 0.7
music_volume = 0.3

# Spawner and target settings
spawner_locations = [
    [0.2, 0.2],
    [0.8, 0.2],
    [0.5, 0.8]
]
spawner_color = [0.0, 0.7, 0.0]  # Green color for spawners
spawner_size = 0.03

target_locations = [
    [0.5, 0.5]
]
target_color = [0.9, 0.7, 0.0]  # Yellow color for targets
target_size = 0.05

# Сохранение и загрузка
save_directory = "./"  # Директория для сохранения игры
default_save_file = "save.txt"
level_files = [
    "level1.txt",
    "level2.txt",
    "level3.txt"
]

# Объекты
object_types = {
    "cube": {
        "color": [0.8, 0.2, 0.2],
        "size": 1.0
    },
    "platform": {
        "color": [0.3, 0.3, 0.8],
        "size": 10.0
    },
    "collectible": {
        "color": [1.0, 0.9, 0.1],
        "size": 0.3
    },
    "moving_platform": {
        "color": [0.2, 0.7, 0.4],
        "size": 2.0,
        "speed": 2.0
    }
} 