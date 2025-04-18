import taichi as ti
import numpy as np
import random
import time
import math
import json
import os
import sys

# Initialize Taichi with CPU arch for compatibility
ti.init(arch=ti.cpu, default_fp=ti.f32, debug=False, kernel_profiler=False)

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "Gravity Cubes 2D"
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (1.0, 1.0, 1.0)
RED = (1.0, 0.0, 0.0)
GREEN = (0.0, 1.0, 0.0)
BLUE = (0.0, 0.0, 1.0)
YELLOW = (1.0, 1.0, 0.0)
CYAN = (0.0, 1.0, 1.0)
MAGENTA = (1.0, 0.0, 1.0)
GRAY = (0.5, 0.5, 0.5)

# Physics settings
GRAVITY = 9.8  # Units per second squared
FRICTION = 0.98  # Friction coefficient
BOUNCE_FACTOR = 0.7  # Bounce coefficient

# Maximum number of objects and particles
MAX_OBJECTS = 100
MAX_PARTICLES = 500

# Define Taichi fields for simulation
pos_x = ti.field(dtype=ti.f32, shape=MAX_OBJECTS)
pos_y = ti.field(dtype=ti.f32, shape=MAX_OBJECTS)
vel_x = ti.field(dtype=ti.f32, shape=MAX_OBJECTS)
vel_y = ti.field(dtype=ti.f32, shape=MAX_OBJECTS)
size = ti.field(dtype=ti.f32, shape=MAX_OBJECTS)
rotation = ti.field(dtype=ti.f32, shape=MAX_OBJECTS)
rotation_speed = ti.field(dtype=ti.f32, shape=MAX_OBJECTS)
is_static = ti.field(dtype=ti.i32, shape=MAX_OBJECTS)
obj_type = ti.field(dtype=ti.i32, shape=MAX_OBJECTS)  # 0=cube, 1=platform, 2=collectible
active = ti.field(dtype=ti.i32, shape=MAX_OBJECTS)
mass = ti.field(dtype=ti.f32, shape=MAX_OBJECTS)
color_r = ti.field(dtype=ti.f32, shape=MAX_OBJECTS)
color_g = ti.field(dtype=ti.f32, shape=MAX_OBJECTS)
color_b = ti.field(dtype=ti.f32, shape=MAX_OBJECTS)

# Particle fields
p_pos_x = ti.field(dtype=ti.f32, shape=MAX_PARTICLES)
p_pos_y = ti.field(dtype=ti.f32, shape=MAX_PARTICLES)
p_vel_x = ti.field(dtype=ti.f32, shape=MAX_PARTICLES)
p_vel_y = ti.field(dtype=ti.f32, shape=MAX_PARTICLES)
p_life = ti.field(dtype=ti.f32, shape=MAX_PARTICLES)
p_max_life = ti.field(dtype=ti.f32, shape=MAX_PARTICLES)
p_size = ti.field(dtype=ti.f32, shape=MAX_PARTICLES)
p_color_r = ti.field(dtype=ti.f32, shape=MAX_PARTICLES)
p_color_g = ti.field(dtype=ti.f32, shape=MAX_PARTICLES)
p_color_b = ti.field(dtype=ti.f32, shape=MAX_PARTICLES)
p_active = ti.field(dtype=ti.i32, shape=MAX_PARTICLES)

# Game state
debug_mode = ti.field(dtype=ti.i32, shape=())
frame_time = ti.field(dtype=ti.f32, shape=())
camera_x = ti.field(dtype=ti.f32, shape=())
camera_y = ti.field(dtype=ti.f32, shape=())
camera_zoom = ti.field(dtype=ti.f32, shape=())
next_obj_id = ti.field(dtype=ti.i32, shape=())
next_particle_id = ti.field(dtype=ti.i32, shape=())
active_objects = ti.field(dtype=ti.i32, shape=())
active_particles = ti.field(dtype=ti.i32, shape=())

# Initialize fields
@ti.kernel
def init_fields():
    # Initialize state fields
    debug_mode[None] = 1  # Start with debug mode on
    frame_time[None] = 0.0
    camera_x[None] = 0.0
    camera_y[None] = 0.0
    camera_zoom[None] = 1.0
    next_obj_id[None] = 0
    next_particle_id[None] = 0
    active_objects[None] = 0
    active_particles[None] = 0
    
    # Initialize object fields
    for i in range(MAX_OBJECTS):
        active[i] = 0
    
    # Initialize particle fields
    for i in range(MAX_PARTICLES):
        p_active[i] = 0

# Physics update kernels
@ti.kernel
def update_physics(dt: ti.f32):
    # Update objects
    for i in range(MAX_OBJECTS):
        if active[i] == 1 and is_static[i] == 0:
            # Apply gravity 
            vel_y[i] -= GRAVITY * dt * 100  # Scale gravity to make it visible
            
            # Apply friction
            vel_x[i] *= FRICTION
            vel_y[i] *= FRICTION
            
            # Update position
            pos_x[i] += vel_x[i] * dt
            pos_y[i] += vel_y[i] * dt
            
            # Update rotation
            rotation[i] += rotation_speed[i] * dt
            
            # Boundary collision
            if pos_x[i] - size[i] < 0:
                pos_x[i] = size[i]
                vel_x[i] = -vel_x[i] * BOUNCE_FACTOR
            elif pos_x[i] + size[i] > SCREEN_WIDTH:
                pos_x[i] = SCREEN_WIDTH - size[i]
                vel_x[i] = -vel_x[i] * BOUNCE_FACTOR
                
            if pos_y[i] - size[i] < 0:
                pos_y[i] = size[i]
                vel_y[i] = -vel_y[i] * BOUNCE_FACTOR
            elif pos_y[i] + size[i] > SCREEN_HEIGHT:
                pos_y[i] = SCREEN_HEIGHT - size[i]
                vel_y[i] = -vel_y[i] * BOUNCE_FACTOR

@ti.kernel
def resolve_collisions():
    # Object-object collision detection and resolution
    for i in range(MAX_OBJECTS):
        if active[i] == 0 or is_static[i] == 1:
            continue
            
        for j in range(i+1, MAX_OBJECTS):
            if active[j] == 0:
                continue
                
            # Quick AABB check
            min_dist = size[i] + size[j]
            if abs(pos_x[i] - pos_x[j]) > min_dist or abs(pos_y[i] - pos_y[j]) > min_dist:
                continue
                
            # Distance calculation
            dx = pos_x[i] - pos_x[j]
            dy = pos_y[i] - pos_y[j]
            distance = ti.sqrt(dx*dx + dy*dy)
            
            if distance < min_dist:
                # Unit normal vector
                nx = dx / distance if distance > 0 else 0.0
                ny = dy / distance if distance > 0 else 1.0
                
                # Penetration depth
                overlap = min_dist - distance
                
                # Handle collectible pickup
                if obj_type[i] == 0 and obj_type[j] == 2:  # Cube and collectible
                    active[j] = 0
                    active_objects[None] -= 1
                    create_particles_at(pos_x[j], pos_y[j], color_r[j], color_g[j], color_b[j], 10)
                    continue
                elif obj_type[j] == 0 and obj_type[i] == 2:  # Cube and collectible
                    active[i] = 0
                    active_objects[None] -= 1
                    create_particles_at(pos_x[i], pos_y[i], color_r[i], color_g[i], color_b[i], 10)
                    continue
                
                # Position adjustment
                if is_static[j] == 1:
                    # j is static, move only i
                    pos_x[i] += nx * overlap
                    pos_y[i] += ny * overlap
                    
                    # Velocity reflection
                    dot_product = vel_x[i] * nx + vel_y[i] * ny
                    if dot_product < 0:  # Moving towards j
                        vel_x[i] -= 2 * dot_product * nx * BOUNCE_FACTOR
                        vel_y[i] -= 2 * dot_product * ny * BOUNCE_FACTOR
                        create_particles_at(pos_x[i], pos_y[i], color_r[i], color_g[i], color_b[i], 5)
                    
                elif is_static[i] == 1:
                    # i is static, move only j
                    pos_x[j] -= nx * overlap
                    pos_y[j] -= ny * overlap
                    
                    # Velocity reflection
                    dot_product = vel_x[j] * nx + vel_y[j] * ny
                    if dot_product > 0:  # Moving towards i
                        vel_x[j] -= 2 * dot_product * nx * BOUNCE_FACTOR
                        vel_y[j] -= 2 * dot_product * ny * BOUNCE_FACTOR
                        create_particles_at(pos_x[j], pos_y[j], color_r[j], color_g[j], color_b[j], 5)
                    
                else:
                    # Both dynamic - distribute by mass
                    m1 = mass[i]
                    m2 = mass[j]
                    total_mass = m1 + m2
                    
                    if total_mass > 0:
                        weight_i = m2 / total_mass
                        weight_j = m1 / total_mass
                        
                        pos_x[i] += nx * overlap * weight_i
                        pos_y[i] += ny * overlap * weight_i
                        pos_x[j] -= nx * overlap * weight_j
                        pos_y[j] -= ny * overlap * weight_j
                        
                        # Exchange impulse
                        v1x, v1y = vel_x[i], vel_y[i]
                        v2x, v2y = vel_x[j], vel_y[j]
                        
                        # Relative velocity
                        rv_x = v1x - v2x
                        rv_y = v1y - v2y
                        
                        # Velocity along normal
                        vel_along_normal = rv_x * nx + rv_y * ny
                        
                        # Only continue if objects are moving toward each other
                        if vel_along_normal > 0:
                            continue
                            
                        # Impulse scalar
                        j_scalar = -(1 + BOUNCE_FACTOR) * vel_along_normal
                        j_scalar /= 1/m1 + 1/m2
                        
                        # Apply impulse
                        impulse_x = j_scalar * nx
                        impulse_y = j_scalar * ny
                        
                        vel_x[i] += impulse_x / m1
                        vel_y[i] += impulse_y / m1
                        vel_x[j] -= impulse_x / m2
                        vel_y[j] -= impulse_y / m2
                        
                        # Add randomness
                        rand_factor = 2.0
                        vel_x[i] += (ti.random() - 0.5) * rand_factor
                        vel_y[i] += (ti.random() - 0.5) * rand_factor
                        vel_x[j] += (ti.random() - 0.5) * rand_factor
                        vel_y[j] += (ti.random() - 0.5) * rand_factor
                        
                        # Create particles
                        create_particles_at((pos_x[i] + pos_x[j])/2, (pos_y[i] + pos_y[j])/2, 
                                          (color_r[i] + color_r[j])/2, 
                                          (color_g[i] + color_g[j])/2, 
                                          (color_b[i] + color_b[j])/2, 5)

@ti.kernel
def update_particles(dt: ti.f32):
    for i in range(MAX_PARTICLES):
        if p_active[i] == 1:
            # Update position
            p_pos_x[i] += p_vel_x[i] * dt
            p_pos_y[i] += p_vel_y[i] * dt
            
            # Apply gravity
            p_vel_y[i] -= GRAVITY * dt * 50
            
            # Update lifetime and size
            p_life[i] -= dt * 30
            p_size[i] = p_size[i] * (p_life[i] / p_max_life[i])
            
            # Deactivate if lifetime is over or too small
            if p_life[i] <= 0 or p_size[i] < 0.5:
                p_active[i] = 0
                active_particles[None] -= 1

# Object creation functions
@ti.func
def create_object(x: ti.f32, y: ti.f32, obj_size: ti.f32, r: ti.f32, g: ti.f32, b: ti.f32, 
                  static: ti.i32, obj_type_val: ti.i32) -> ti.i32:
    obj_id = -1
    if next_obj_id[None] < MAX_OBJECTS:
        obj_id = next_obj_id[None]
        next_obj_id[None] += 1
        active_objects[None] += 1
        
        # Initialize object properties
        pos_x[obj_id] = x
        pos_y[obj_id] = y
        size[obj_id] = obj_size
        color_r[obj_id] = r
        color_g[obj_id] = g
        color_b[obj_id] = b
        is_static[obj_id] = static
        obj_type[obj_id] = obj_type_val
        active[obj_id] = 1
        mass[obj_id] = obj_size * obj_size  # Mass proportional to area
        
        # Set random rotation for cubes or constant for collectibles
        if obj_type_val == 0:  # Cube
            rotation_speed[obj_id] = (ti.random() - 0.5) * 10
        elif obj_type_val == 2:  # Collectible
            rotation_speed[obj_id] = 2.0
        else:
            rotation_speed[obj_id] = 0.0
            
        rotation[obj_id] = 0.0
        vel_x[obj_id] = 0.0
        vel_y[obj_id] = 0.0
    return obj_id

@ti.kernel
def add_cube(x: ti.f32, y: ti.f32, s: ti.f32, r: ti.f32, g: ti.f32, b: ti.f32) -> ti.i32:
    return create_object(x, y, s, r, g, b, 0, 0)  # Cube type = 0

@ti.kernel
def add_platform(x: ti.f32, y: ti.f32, width: ti.f32, r: ti.f32, g: ti.f32, b: ti.f32) -> ti.i32:
    return create_object(x, y, width, r, g, b, 1, 1)  # Platform type = 1

@ti.kernel
def add_collectible(x: ti.f32, y: ti.f32, s: ti.f32, r: ti.f32, g: ti.f32, b: ti.f32) -> ti.i32:
    return create_object(x, y, s, r, g, b, 0, 2)  # Collectible type = 2

@ti.kernel
def reset_simulation():
    # Clear all objects and particles
    for i in range(MAX_OBJECTS):
        active[i] = 0
    
    for i in range(MAX_PARTICLES):
        p_active[i] = 0
    
    next_obj_id[None] = 0
    next_particle_id[None] = 0
    active_objects[None] = 0
    active_particles[None] = 0
    
    # Add floor
    platform_id = create_object(SCREEN_WIDTH/2, SCREEN_HEIGHT-20, SCREEN_WIDTH/2, 0.2, 0.2, 0.8, 1, 1)
    
    # Add walls
    left_wall = create_object(10, SCREEN_HEIGHT/2, 10, 0.2, 0.2, 0.8, 1, 1)
    right_wall = create_object(SCREEN_WIDTH-10, SCREEN_HEIGHT/2, 10, 0.2, 0.2, 0.8, 1, 1)

    # Add cubes
    for i in range(3):
        x = ti.random() * (SCREEN_WIDTH - 200) + 100
        y = ti.random() * (SCREEN_HEIGHT - 300) + 100
        s = ti.random() * 20 + 20
        r = ti.random() * 0.5 + 0.5
        g = ti.random() * 0.5 + 0.5
        b = ti.random() * 0.5 + 0.5
        cube_id = create_object(x, y, s, r, g, b, 0, 0)
    
    # Add collectibles
    for i in range(2):
        x = ti.random() * (SCREEN_WIDTH - 200) + 100
        y = ti.random() * (SCREEN_HEIGHT - 300) + 100
        collectible_id = create_object(x, y, 15, 1.0, 0.84, 0.0, 0, 2)

# Particle system functions
@ti.func
def create_particles_at(x: ti.f32, y: ti.f32, r: ti.f32, g: ti.f32, b: ti.f32, count: ti.i32):
    for i in range(count):
        if next_particle_id[None] < MAX_PARTICLES:
            p_id = next_particle_id[None]
            next_particle_id[None] = (next_particle_id[None] + 1) % MAX_PARTICLES
            
            # If we're overwriting an active particle, decrement counter
            if p_active[p_id] == 1:
                active_particles[None] -= 1
                
            # Initialize particle
            p_active[p_id] = 1
            active_particles[None] += 1
            
            angle = ti.random() * 2 * 3.14159265
            speed = ti.random() * 50 + 20
            
            p_pos_x[p_id] = x + (ti.random() - 0.5) * 10
            p_pos_y[p_id] = y + (ti.random() - 0.5) * 10
            p_vel_x[p_id] = ti.cos(angle) * speed
            p_vel_y[p_id] = ti.sin(angle) * speed
            p_size[p_id] = ti.random() * 3 + 2
            p_life[p_id] = ti.random() * 0.5 + 0.5
            p_max_life[p_id] = p_life[p_id]
            p_color_r[p_id] = r
            p_color_g[p_id] = g
            p_color_b[p_id] = b

# Draw background
@ti.kernel
def fill_pixels(pixels: ti.template(), t: ti.f32):
    for i, j in pixels:
        # Normalized coordinates
        x = i / SCREEN_WIDTH
        y = j / SCREEN_HEIGHT
        
        # Create gradient background
        r = 0.08 + y * 0.12
        g = 0.08 + y * 0.04
        b = 0.2 - y * 0.08
        
        pixels[i, j] = ti.Vector([r, g, b, 1.0])

# Draw objects to a pixel buffer
@ti.kernel
def draw_objects(pixels: ti.template()):
    for i in range(MAX_OBJECTS):
        if active[i] == 1:
            # Get object properties
            x, y = pos_x[i], pos_y[i]
            obj_size = size[i]
            r, g, b = color_r[i], color_g[i], color_b[i]
            obj_type_val = obj_type[i]
            rot = rotation[i]
            
            # Draw based on object type
            if obj_type_val == 0:  # Cube
                # Draw a rotated square
                c = ti.cos(rot * 3.14159265 / 180.0)
                s = ti.sin(rot * 3.14159265 / 180.0)
                
                for dx in range(-int(obj_size), int(obj_size)+1):
                    for dy in range(-int(obj_size), int(obj_size)+1):
                        # Rotate point
                        rx = dx * c - dy * s
                        ry = dx * s + dy * c
                        
                        # Calculate pixel position
                        px = int(x + rx)
                        py = int(y + ry)
                        
                        # Draw if within screen bounds
                        if 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                            pixels[px, py] = ti.Vector([r, g, b, 1.0])
                            
            elif obj_type_val == 1:  # Platform
                # Draw a rectangle
                half_height = obj_size / 4
                
                for dx in range(-int(obj_size), int(obj_size)+1):
                    for dy in range(-int(half_height), int(half_height)+1):
                        px = int(x + dx)
                        py = int(y + dy)
                        
                        if 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                            pixels[px, py] = ti.Vector([r, g, b, 1.0])
                            
            elif obj_type_val == 2:  # Collectible
                # Draw a circle
                for dx in range(-int(obj_size), int(obj_size)+1):
                    for dy in range(-int(obj_size), int(obj_size)+1):
                        if dx*dx + dy*dy <= obj_size*obj_size:
                            px = int(x + dx)
                            py = int(y + dy)
                            
                            if 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                                pixels[px, py] = ti.Vector([r, g, b, 1.0])

# Draw particles to a pixel buffer
@ti.kernel
def draw_particles(pixels: ti.template()):
    for i in range(MAX_PARTICLES):
        if p_active[i] == 1:
            # Get particle properties
            x, y = p_pos_x[i], p_pos_y[i]
            r, g, b = p_color_r[i], p_color_g[i], p_color_b[i]
            alpha = p_life[i] / p_max_life[i]
            particle_size = p_size[i]
            
            # Draw a small circle with alpha blending
            for dx in range(-int(particle_size), int(particle_size)+1):
                for dy in range(-int(particle_size), int(particle_size)+1):
                    if dx*dx + dy*dy <= particle_size*particle_size:
                        px = int(x + dx)
                        py = int(y + dy)
                        
                        if 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                            # Alpha blending
                            bg = pixels[px, py]
                            pixels[px, py] = ti.Vector([
                                r * alpha + bg[0] * (1-alpha),
                                g * alpha + bg[1] * (1-alpha),
                                b * alpha + bg[2] * (1-alpha),
                                1.0
                            ])

# Main function
def main():
    # Initialize simulation
    init_fields()
    reset_simulation()
    
    # Create window and canvas
    window = ti.ui.Window(TITLE, (SCREEN_WIDTH, SCREEN_HEIGHT), vsync=True)
    canvas = window.get_canvas()
    pixels = ti.Vector.field(4, dtype=ti.f32, shape=(SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # For FPS calculation
    last_time = time.time()
    fps_values = []
    
    # Main game loop
    while window.running:
        # Calculate delta time
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        # Store frame time for FPS calculation
        frame_time[None] = dt
        
        # Cap delta time to prevent large jumps
        dt = min(dt, 0.05)
        
        # Process input
        for e in window.get_events(ti.ui.PRESS):
            if e.key == ti.ui.ESCAPE:
                window.running = False
            elif e.key == 'r':
                reset_simulation()
            elif e.key == 'f1':
                debug_mode[None] = 1 - debug_mode[None]  # Toggle debug mode
        
        # Handle mouse clicks
        if window.is_pressed(ti.ui.LMB):
            # Create cube at mouse position
            mouse_x, mouse_y = window.get_cursor_pos()
            x, y = mouse_x * SCREEN_WIDTH, (1 - mouse_y) * SCREEN_HEIGHT  # Invert Y coordinate
            size_val = random.uniform(20, 40)
            r = random.uniform(0.5, 1.0)
            g = random.uniform(0.5, 1.0)
            b = random.uniform(0.5, 1.0)
            add_cube(x, y, size_val, r, g, b)
            
        if window.is_pressed(ti.ui.RMB):
            # Create platform at mouse position
            mouse_x, mouse_y = window.get_cursor_pos()
            x, y = mouse_x * SCREEN_WIDTH, (1 - mouse_y) * SCREEN_HEIGHT
            add_platform(x, y, 60, 0.2, 0.2, 0.8)
            
        if window.is_pressed(ti.ui.MMB):
            # Create collectible at mouse position
            mouse_x, mouse_y = window.get_cursor_pos()
            x, y = mouse_x * SCREEN_WIDTH, (1 - mouse_y) * SCREEN_HEIGHT
            add_collectible(x, y, 15, 1.0, 0.84, 0.0)
        
        # Camera controls
        if window.is_pressed('w'):
            camera_y[None] -= 200 * dt
        if window.is_pressed('s'):
            camera_y[None] += 200 * dt
        if window.is_pressed('a'):
            camera_x[None] -= 200 * dt
        if window.is_pressed('d'):
            camera_x[None] += 200 * dt
        if window.is_pressed('q'):
            camera_zoom[None] = max(0.1, camera_zoom[None] - 0.5 * dt)
        if window.is_pressed('e'):
            camera_zoom[None] = min(2.0, camera_zoom[None] + 0.5 * dt)
        
        # Update physics
        update_physics(dt)
        resolve_collisions()
        update_particles(dt)
        
        # Render scene
        fill_pixels(pixels, time.time())
        draw_objects(pixels)
        draw_particles(pixels)
        canvas.set_image(pixels)
        
        # Show debug info
        if debug_mode[None] == 1:
            # Calculate FPS
            fps_values.append(1.0 / max(0.001, dt))
            if len(fps_values) > 10:
                fps_values.pop(0)
            avg_fps = sum(fps_values) / len(fps_values)
            
            # Draw debug text
            window.GUI.begin("Debug", 0.01, 0.01, 0.2, 0.2)
            window.GUI.text(f"FPS: {int(avg_fps)}")
            window.GUI.text(f"Objects: {active_objects[None]}")
            window.GUI.text(f"Particles: {active_particles[None]}")
            window.GUI.text(f"Camera: ({camera_x[None]:.1f}, {camera_y[None]:.1f})")
            window.GUI.text(f"Zoom: {camera_zoom[None]:.2f}")
            window.GUI.end()
        
        # Update window
        window.show()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
