import taichi as ti
import numpy as np
import config
import sound
import game_state
import random
from config import *

# Maximum number of cubes
max_cubes = 5

# Физические константы для CubeManager
GRAVITY = 9.8
BOUNCE_FACTOR = 0.8
RANDOM_ROTATION = True
ROTATION_SPEED = 5.0

# Field declarations (without initialization)
cube_positions = None
cube_colors = None
cube_sizes = None
cube_active = None
cube_count = None
last_positions = None  # For tracking collisions and speed
cube_steps = None      # Step counter for each cube

# Cube fields initialization
def init():
    global cube_positions, cube_colors, cube_sizes, cube_active, cube_count, last_positions, cube_steps
    
    # Initialize fields for storing cube data
    cube_positions = ti.Vector.field(2, dtype=ti.f32, shape=max_cubes)
    cube_colors = ti.Vector.field(3, dtype=ti.f32, shape=max_cubes)
    cube_sizes = ti.field(dtype=ti.f32, shape=max_cubes)
    cube_active = ti.field(dtype=ti.i32, shape=max_cubes)
    cube_count = ti.field(dtype=ti.i32, shape=())
    last_positions = ti.Vector.field(2, dtype=ti.f32, shape=max_cubes)
    cube_steps = ti.field(dtype=ti.i32, shape=max_cubes)

# First cube initialization
@ti.kernel
def init_first_cube():
    # Create first cube in the center
    cube_positions[0] = ti.Vector([0.5, 0.5])
    cube_colors[0] = ti.Vector([config.default_cube_color[0], 
                               config.default_cube_color[1], 
                               config.default_cube_color[2]])
    cube_sizes[0] = config.default_cube_size
    cube_active[0] = 1  # 1 = active, 0 = inactive
    last_positions[0] = cube_positions[0]
    cube_steps[0] = 0
    cube_count[None] = 1

# Function for determining the active cube
def get_active_cube_index():
    # Find the active cube
    for i in range(cube_count[None]):
        if cube_active[i] == 1:
            return i
    return -1  # If no active cube

# Adding a new cube with specified parameters
def add_new_cube(color=None, size=None, spawn_point_idx=None):
    count = cube_count[None]
    if count < max_cubes:
        # Deactivate all cubes
        for i in range(count):
            cube_active[i] = 0
        
        # Define new cube parameters
        if color is None:
            # Create random color if not specified
            r = np.random.random()
            g = np.random.random()
            b = np.random.random()
            color = [r, g, b]
        
        # Use default size if not specified
        if size is None:
            size = config.default_cube_size
        
        # Determine spawn point
        if spawn_point_idx is None:
            spawn_point_idx = config.current_spawn_point
        
        spawn_idx = spawn_point_idx % len(config.spawn_points)
        spawn_x = config.spawn_points[spawn_idx][0]
        spawn_y = config.spawn_points[spawn_idx][1]
        
        # Add new cube
        cube_positions[count] = ti.Vector([spawn_x, spawn_y])
        cube_colors[count] = ti.Vector([color[0], color[1], color[2]])
        cube_sizes[count] = size
        cube_active[count] = 1  # New cube is active
        last_positions[count] = cube_positions[count]
        cube_steps[count] = 0
        
        # Increment counter
        cube_count[None] += 1
        
        # Play cube creation sound
        if config.sound_enabled:
            sound.play_create_cube()
            
        return True
    return False

# Delete cube by index
def delete_cube(index):
    count = cube_count[None]
    if index >= 0 and index < count:
        # If not deleting the last cube, shift all cubes after it
        if index < count - 1:
            for i in range(index, count - 1):
                cube_positions[i] = cube_positions[i + 1]
                cube_colors[i] = cube_colors[i + 1]
                cube_sizes[i] = cube_sizes[i + 1]
                cube_active[i] = cube_active[i + 1]
                last_positions[i] = last_positions[i + 1]
                cube_steps[i] = cube_steps[i + 1]
        
        # Decrease cube counter
        cube_count[None] -= 1
        
        # If all cubes deleted, create a default one
        if cube_count[None] == 0:
            init_first_cube()
        # Otherwise, if active cube deleted, activate the last one
        elif index == get_active_cube_index():
            cube_active[cube_count[None] - 1] = 1
            
        return True
    return False

# Resize active cube
def resize_active_cube(new_size):
    active_index = get_active_cube_index()
    if active_index != -1:
        # Limit size
        if new_size < config.min_cube_size:
            new_size = config.min_cube_size
        elif new_size > config.max_cube_size:
            new_size = config.max_cube_size
            
        cube_sizes[active_index] = new_size
        return True
    return False

# Change active cube color
def change_active_cube_color(new_color):
    active_index = get_active_cube_index()
    if active_index != -1:
        cube_colors[active_index] = ti.Vector([new_color[0], new_color[1], new_color[2]])
        return True
    return False

# Reset active cube position to starting point
def reset_active_cube_position():
    active_index = get_active_cube_index()
    if active_index != -1:
        spawn_idx = config.current_spawn_point % len(config.spawn_points)
        spawn_x = config.spawn_points[spawn_idx][0]
        spawn_y = config.spawn_points[spawn_idx][1]
        
        cube_positions[active_index] = ti.Vector([spawn_x, spawn_y])
        last_positions[active_index] = cube_positions[active_index]
        cube_steps[active_index] = 0
        return True
    return False

# Update active cube position based on WASD keys
def update_active_cube_position(window):
    # Find active cube
    active_index = get_active_cube_index()
    if active_index == -1:
        return
    
    # Save previous position
    last_pos = np.array([cube_positions[active_index][0], cube_positions[active_index][1]])
    last_positions[active_index] = ti.Vector([last_pos[0], last_pos[1]])
    
    # Current cube position
    pos = np.array([cube_positions[active_index][0], cube_positions[active_index][1]])
    new_pos = pos.copy()
    size = cube_sizes[active_index]
    
    # Flag for tracking movement
    moved = False
    
    # Process WASD keys
    if window.is_pressed('w'):
        new_pos[1] += config.move_speed
        moved = True
    if window.is_pressed('s'):
        new_pos[1] -= config.move_speed
        moved = True
    if window.is_pressed('a'):
        new_pos[0] -= config.move_speed
        moved = True
    if window.is_pressed('d'):
        new_pos[0] += config.move_speed
        moved = True
    
    # Check collisions only if cube is moving
    if moved:
        # Check collisions
        from collision import check_collision
        had_collision = check_collision(new_pos, size)
        
        if not had_collision:
            # If no collision, update position
            cube_positions[active_index] = ti.Vector([new_pos[0], new_pos[1]])
            
            # Increment step counter
            cube_steps[active_index] += 1
            game_state.increment_step()
            
            # Calculate speed (approximate)
            dx = new_pos[0] - last_pos[0]
            dy = new_pos[1] - last_pos[1]
            speed = np.sqrt(dx*dx + dy*dy) * 100  # Scale for display convenience
            game_state.update_cube_speed(speed)
        elif config.sound_enabled:
            # If collision detected, play sound
            sound.play_collision()
    else:
        # If cube not moving, speed is 0
        game_state.update_cube_speed(0.0)

# Check if cube is in target zone
def is_cube_in_target_zone(cube_index):
    if cube_index < 0 or cube_index >= cube_count[None]:
        return False
        
    # Cube position
    pos = np.array([cube_positions[cube_index][0], cube_positions[cube_index][1]])
    
    # Check each target zone
    for zone in config.target_zones:
        zone_x, zone_y, zone_radius = zone
        
        # Distance from cube to zone center
        dist = np.sqrt((pos[0] - zone_x)**2 + (pos[1] - zone_y)**2)
        
        # If cube center is inside zone, return True
        if dist <= zone_radius:
            return True
            
    return False 

class CubeManager:
    def __init__(self, renderer):
        self.renderer = renderer
        self.cubes = []
        self.selected_cube_index = None
        
        # Load the cube model at initialization
        self.cube_model = self.renderer.load_model_obj("cube.obj")
        
    def create_cube(self, position=None):
        # Create cube with random position if not specified
        if position is None:
            position = [
                random.uniform(-5, 5),
                random.uniform(-5, 5),
                random.uniform(-15, -5)
            ]
        
        # Generate random color for the cube
        color = [
            random.uniform(0.2, 1.0),
            random.uniform(0.2, 1.0),
            random.uniform(0.2, 1.0)
        ]
        
        # Generate random rotation for the cube
        rotation = [
            random.uniform(0, 360),
            random.uniform(0, 360),
            random.uniform(0, 360)
        ]
        
        # Set initial cube properties
        self.cubes.append({
            'position': position,
            'rotation': rotation,
            'scale': [1.0, 1.0, 1.0],
            'color': color,
            'velocity': [0, 0, 0]
        })
        
        # Play sound when cube is created
        sound.play_create_cube()
        
        return len(self.cubes) - 1  # Return index of created cube
    
    def update(self, delta_time):
        # Update all cubes (position, rotation, etc.)
        for i, cube in enumerate(self.cubes):
            # Apply gravity
            cube['velocity'][1] -= GRAVITY * delta_time
            
            # Update position based on velocity
            for j in range(3):
                cube['position'][j] += cube['velocity'][j] * delta_time
            
            # Boundary checking for floor
            if cube['position'][1] < -5:
                cube['position'][1] = -5
                cube['velocity'][1] = -cube['velocity'][1] * BOUNCE_FACTOR
                sound.play_collision()
            
            # Random rotation
            if RANDOM_ROTATION:
                for j in range(3):
                    cube['rotation'][j] += random.uniform(-1, 1) * ROTATION_SPEED * delta_time
    
    def render(self):
        # Draw all cubes
        for i, cube in enumerate(self.cubes):
            # Highlight selected cube
            highlight = (i == self.selected_cube_index)
            
            # Check if we're in 2D mode
            is_2d_mode = hasattr(self.renderer, 'is_2d') and self.renderer.is_2d
            
            if is_2d_mode:
                # В 2D режиме используем только x и y позиции
                pos = [cube['position'][0], cube['position'][1], 0.0]
                scale = [cube['scale'][0], cube['scale'][1], 1.0]  # В 2D z-scale не важен
            else:
                # В 3D используем все параметры
                pos = cube['position']
                scale = cube['scale']
            
            # Если куб выделен, делаем его немного ярче
            color = cube['color'].copy()
            if highlight:
                for j in range(3):
                    color[j] = min(1.0, color[j] * 1.5)
            
            # Добавляем альфа-компонент, если его нет
            if len(color) == 3:
                color.append(1.0)
                
            # Используем draw_cube вместо draw_model
            self.renderer.draw_cube(
                pos,
                scale,
                color
            )
    
    def select_cube(self, index):
        # Select a cube by index
        if 0 <= index < len(self.cubes):
            self.selected_cube_index = index
            return True
        return False
    
    def apply_force_to_selected(self, force):
        # Apply force to the selected cube
        if self.selected_cube_index is not None:
            for i in range(3):
                self.cubes[self.selected_cube_index]['velocity'][i] += force[i]