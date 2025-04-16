import pygame
import sys
import random
import time
import math
import json
import os

# Initialize pygame
pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "Gravity Cubes 2D"
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)

# Physics settings
GRAVITY = 980  # Pixels per second squared
FRICTION = 0.98  # Friction coefficient
BOUNCE_FACTOR = 0.7  # Bounce coefficient

# Particle class
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        
        # Normalize color to RGB tuple format
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            self.color = (int(color[0]), int(color[1]), int(color[2]))
        else:
            self.color = (255, 255, 255)  # White by default
            
        self.size = random.randint(2, 5)
        self.life = random.randint(15, 45)
        self.max_life = self.life
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 3)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05  # Gravity
        self.life -= 1
        self.size = max(0, self.size * (self.life / self.max_life))
        return self.life > 0

    def draw(self, screen):
        # Calculate transparency based on remaining lifetime
        alpha = int(255 * (self.life / self.max_life))
        
        # Create color with transparency
        try:
            if isinstance(self.color, (list, tuple)) and len(self.color) >= 3:
                color_with_alpha = (int(self.color[0]), int(self.color[1]), int(self.color[2]), alpha)
            else:
                color_with_alpha = (255, 255, 255, alpha)  # White by default with transparency
                
            # Create a temporary surface for rendering transparent particles
            surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, color_with_alpha, (int(self.size), int(self.size)), int(self.size))
            screen.blit(surf, (int(self.x - self.size), int(self.y - self.size)))
        except Exception as e:
            print(f"Error rendering particle: {e} - color: {self.color}, size: {self.size}")

# Game object class
class GameObject:
    def __init__(self, x, y, size, color, is_static=False, obj_type="cube"):
        self.x = x
        self.y = y
        self.size = size
        
        # Normalize color
        if isinstance(color, (list, tuple)):
            if len(color) >= 3:
                self.color = (int(color[0]), int(color[1]), int(color[2]))
            else:
                self.color = (100, 100, 100)  # Gray by default
        else:
            self.color = (100, 100, 100)  # Gray by default
            
        self.velocity = [0, 0]
        self.is_static = is_static
        self.type = obj_type
        self.active = True
        self.rotation = 0
        self.rotation_speed = random.uniform(-50, 50) if obj_type == "cube" else 90
        
    def update(self, dt, objects):
        if not self.active or self.is_static:
            return False
        
        # For collectibles - only rotation
        if self.type == "collectible":
            self.rotation += self.rotation_speed * dt
            return False
            
        # Apply gravity
        self.velocity[1] += GRAVITY * dt
        
        # Apply friction
        self.velocity[0] *= FRICTION
        self.velocity[1] *= FRICTION
        
        # Update position
        prev_x, prev_y = self.x, self.y
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt
        
        # Update rotation
        self.rotation += self.rotation_speed * dt
        
        # Collision flag
        collision_occurred = False
        
        # Check collisions with screen boundaries
        if self.x - self.size < 0:
            self.x = self.size
            self.velocity[0] = -self.velocity[0] * BOUNCE_FACTOR
            collision_occurred = True
        elif self.x + self.size > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.size
            self.velocity[0] = -self.velocity[0] * BOUNCE_FACTOR
            collision_occurred = True
            
        if self.y - self.size < 0:
            self.y = self.size
            self.velocity[1] = -self.velocity[1] * BOUNCE_FACTOR
            collision_occurred = True
        elif self.y + self.size > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.size
            self.velocity[1] = -self.velocity[1] * BOUNCE_FACTOR
            collision_occurred = True
            
        # Check collisions with other objects
        for obj in objects:
            if obj != self and obj.active:
                dx = self.x - obj.x
                dy = self.y - obj.y
                distance = math.sqrt(dx*dx + dy*dy)
                min_dist = self.size + obj.size
                
                if distance < min_dist:
                    # Normalized direction vector
                    if distance > 0:
                        nx = dx / distance
                        ny = dy / distance
                    else:
                        angle = random.uniform(0, 2 * math.pi)
                        nx = math.cos(angle)
                        ny = math.sin(angle)
                    
                    # Penetration depth
                    overlap = min_dist - distance
                    
                    # If object is static
                    if obj.is_static:
                        # Adjust position
                        self.x += nx * overlap
                        self.y += ny * overlap
                        
                        # Reflect velocity
                        dot_product = self.velocity[0] * nx + self.velocity[1] * ny
                        if dot_product < 0:  # Moving toward the object
                            self.velocity[0] -= 2 * dot_product * nx * BOUNCE_FACTOR
                            self.velocity[1] -= 2 * dot_product * ny * BOUNCE_FACTOR
                            
                        collision_occurred = True
                        
                    # If collecting a coin
                    elif obj.type == "collectible" and self.type == "cube":
                        obj.active = False
                        collision_occurred = True
                        
                    # If both objects are dynamic
                    elif not obj.is_static and not self.is_static:
                        # Distribute displacement between objects
                        total_size = self.size + obj.size
                        self_weight = obj.size / total_size
                        obj_weight = self.size / total_size
                        
                        self.x += nx * overlap * self_weight
                        self.y += ny * overlap * self_weight
                        obj.x -= nx * overlap * obj_weight
                        obj.y -= ny * overlap * obj_weight
                        
                        # Exchange impulses
                        v1x, v1y = self.velocity
                        v2x, v2y = obj.velocity
                        
                        # Relative velocity along normal
                        v_rel_x = v1x - v2x
                        v_rel_y = v1y - v2y
                        vel_along_normal = v_rel_x * nx + v_rel_y * ny
                        
                        # Continue only if objects are approaching
                        if vel_along_normal > 0:
                            continue
                            
                        # Collision impulse
                        mass1 = self.size ** 2  # Area ~ mass in 2D
                        mass2 = obj.size ** 2
                        
                        impulse = -(1 + BOUNCE_FACTOR) * vel_along_normal
                        impulse /= (1/mass1 + 1/mass2)
                        
                        impulse_x = impulse * nx
                        impulse_y = impulse * ny
                        
                        # Apply impulse
                        self.velocity[0] += impulse_x / mass1
                        self.velocity[1] += impulse_y / mass1
                        obj.velocity[0] -= impulse_x / mass2
                        obj.velocity[1] -= impulse_y / mass2
                        
                        # Add randomness
                        self.velocity[0] += random.uniform(-5, 5)
                        self.velocity[1] += random.uniform(-5, 5)
                        obj.velocity[0] += random.uniform(-5, 5)
                        obj.velocity[1] += random.uniform(-5, 5)
                        
                        collision_occurred = True
        
        return collision_occurred
        
    def draw(self, screen):
        if not self.active:
            return
            
        if self.type == "cube":
            # Draw cube with rotation
            surface = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            
            # Convert color to RGB format
            rgb_color = self.color
            if isinstance(rgb_color, (list, tuple)) and len(rgb_color) >= 3:
                rgb_color = (int(rgb_color[0]), int(rgb_color[1]), int(rgb_color[2]))
            else:
                rgb_color = (100, 100, 100)  # Gray by default
                
            pygame.draw.rect(surface, rgb_color, (0, 0, int(self.size * 2), int(self.size * 2)))
            
            # Rotate surface
            rotated = pygame.transform.rotate(surface, self.rotation)
            
            # Get dimensions of rotated surface
            rot_rect = rotated.get_rect()
            rot_rect.center = (int(self.x), int(self.y))
            
            # Rendering
            screen.blit(rotated, rot_rect)
            
        elif self.type == "collectible":
            # Convert color to RGB format
            rgb_color = self.color
            if isinstance(rgb_color, (list, tuple)) and len(rgb_color) >= 3:
                rgb_color = (int(rgb_color[0]), int(rgb_color[1]), int(rgb_color[2]))
            else:
                rgb_color = (255, 215, 0)  # Gold for coins by default
                
            # Draw collectible (circle)
            pygame.draw.circle(screen, rgb_color, (int(self.x), int(self.y)), int(self.size))
            
        elif self.type == "platform":
            # Convert color to RGB format
            rgb_color = self.color
            if isinstance(rgb_color, (list, tuple)) and len(rgb_color) >= 3:
                rgb_color = (int(rgb_color[0]), int(rgb_color[1]), int(rgb_color[2]))
            else:
                rgb_color = (50, 50, 200)  # Blue for platforms by default
                
            # Draw platform (rectangle)
            rect = pygame.Rect(
                int(self.x - self.size), 
                int(self.y - self.size/4), 
                int(self.size * 2), 
                int(self.size/2)
            )
            pygame.draw.rect(screen, rgb_color, rect)

# Main game class
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 18)
        self.running = True
        self.objects = []
        self.particles = []
        self.selected_object = None
        self.camera_pos = [0, 0]
        self.zoom = 1.0
        self.debug = True
        
        # Create initial objects
        self.add_initial_objects()
        
    def add_initial_objects(self):
        # Floor
        floor = GameObject(SCREEN_WIDTH/2, SCREEN_HEIGHT-20, 
                           SCREEN_WIDTH/2, (50, 50, 200), True, "platform")
        self.objects.append(floor)
        
        # Walls
        left_wall = GameObject(10, SCREEN_HEIGHT/2, 
                              10, (50, 50, 200), True, "platform")
        right_wall = GameObject(SCREEN_WIDTH-10, SCREEN_HEIGHT/2, 
                               10, (50, 50, 200), True, "platform")
        self.objects.append(left_wall)
        self.objects.append(right_wall)
        
        # Cubes
        for i in range(5):
            x = random.randint(100, SCREEN_WIDTH-100)
            y = random.randint(100, SCREEN_HEIGHT-200)
            size = random.randint(20, 40)
            color = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )
            cube = GameObject(x, y, size, color)
            self.objects.append(cube)
            
        # Collectibles
        for i in range(3):
            x = random.randint(100, SCREEN_WIDTH-100)
            y = random.randint(100, SCREEN_HEIGHT-200)
            coin = GameObject(x, y, 15, (255, 215, 0), False, "collectible")
            self.objects.append(coin)
            
    def create_particles(self, pos, color=None, count=20):
        if color is None:
            color = [random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)]
        
        # Check if the provided color is valid
        if not isinstance(color, (list, tuple)) or len(color) < 3:
            color = [255, 255, 255]  # White by default
        
        for _ in range(count):
            particle_x = pos[0] + random.uniform(-10, 10)
            particle_y = pos[1] + random.uniform(-10, 10)
            self.particles.append(Particle(particle_x, particle_y, color))
            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    # Reset game
                    self.objects = []
                    self.add_initial_objects()
                elif event.key == pygame.K_F1:
                    # Toggle debug mode
                    self.debug = not self.debug
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    # Load preset levels
                    level = event.key - pygame.K_1 + 1
                    self.load_level(f"level{level}.txt")
                elif event.key == pygame.K_F5:
                    # Save game
                    self.save_game("save.txt")
                elif event.key == pygame.K_F9:
                    # Load game
                    self.load_game("save.txt")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse clicks
                x, y = pygame.mouse.get_pos()
                if event.button == 1:  # LMB - create cube
                    size = random.randint(20, 40)
                    color = (
                        random.randint(50, 255),
                        random.randint(50, 255),
                        random.randint(50, 255)
                    )
                    new_cube = GameObject(x, y, size, color)
                    self.objects.append(new_cube)
                    self.create_particles([x, y], color, 15)
                elif event.button == 3:  # RMB - create platform
                    platform = GameObject(x, y, 60, (50, 50, 200), True, "platform")
                    self.objects.append(platform)
                elif event.button == 2:  # MMB - create collectible
                    coin = GameObject(x, y, 15, (255, 215, 0), False, "collectible")
                    self.objects.append(coin)
                    self.create_particles([x, y], (255, 215, 0), 8)
                    
    def update(self, dt):
        # Update all objects
        for obj in self.objects:
            collision = obj.update(dt, self.objects)
            if collision and not obj.is_static:
                # If collision occurred, create particles
                self.create_particles([obj.x, obj.y], obj.color, 10)
        
        # Update particles
        i = 0
        while i < len(self.particles):
            if self.particles[i].update():
                i += 1
            else:
                self.particles.pop(i)
                
        # Keyboard camera control
        keys = pygame.key.get_pressed()
        move_speed = 300 * dt
        if keys[pygame.K_w]:
            self.camera_pos[1] -= move_speed
        if keys[pygame.K_s]:
            self.camera_pos[1] += move_speed
        if keys[pygame.K_a]:
            self.camera_pos[0] -= move_speed
        if keys[pygame.K_d]:
            self.camera_pos[0] += move_speed
            
        # Camera zoom
        if keys[pygame.K_q]:
            self.zoom = max(0.1, self.zoom - 0.5 * dt)
        if keys[pygame.K_e]:
            self.zoom = min(2.0, self.zoom + 0.5 * dt)
            
    def render(self):
        # Clear screen
        self.screen.fill(BLACK)
        
        # Draw gradient background
        for y in range(0, SCREEN_HEIGHT, 2):
            # Interpolate between two colors
            ratio = y / SCREEN_HEIGHT
            r = int(20 + 30 * ratio)
            g = int(20 + 10 * ratio)
            b = int(50 - 20 * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # Render all objects
        for obj in self.objects:
            obj.draw(self.screen)
            
        # Render particles
        for particle in self.particles:
            particle.draw(self.screen)
            
        # Display debug information
        if self.debug:
            # FPS
            fps_text = self.font.render(f"FPS: {int(self.clock.get_fps())}", True, WHITE)
            self.screen.blit(fps_text, (10, 10))
            
            # Object count
            obj_count = len([o for o in self.objects if o.active])
            obj_text = self.font.render(f"Objects: {obj_count}", True, WHITE)
            self.screen.blit(obj_text, (10, 30))
            
            # Particle count
            particle_text = self.font.render(f"Particles: {len(self.particles)}", True, WHITE)
            self.screen.blit(particle_text, (10, 50))
            
            # Camera position and zoom
            camera_text = self.font.render(
                f"Camera: ({int(self.camera_pos[0])}, {int(self.camera_pos[1])}) Zoom: {self.zoom:.2f}", 
                True, WHITE
            )
            self.screen.blit(camera_text, (10, 70))
        
        # Update screen
        pygame.display.flip()
        
    def save_game(self, filename):
        game_data = []
        for obj in self.objects:
            if obj.active:
                game_data.append({
                    'x': obj.x,
                    'y': obj.y,
                    'size': obj.size,
                    'color': obj.color,
                    'is_static': obj.is_static,
                    'type': obj.type,
                    'velocity': obj.velocity
                })
                
        try:
            with open(filename, 'w') as f:
                json.dump(game_data, f)
            print(f"Game saved to {filename}")
        except Exception as e:
            print(f"Error saving: {e}")
            
    def load_game(self, filename):
        try:
            if not os.path.exists(filename):
                print(f"File {filename} does not exist")
                return False
                
            with open(filename, 'r') as f:
                game_data = json.load(f)
                
            # Clear current objects
            self.objects = []
            
            # Create objects from save data
            for obj_data in game_data:
                obj = GameObject(
                    obj_data['x'],
                    obj_data['y'],
                    obj_data['size'],
                    tuple(obj_data['color']),
                    obj_data['is_static'],
                    obj_data['type']
                )
                obj.velocity = obj_data['velocity']
                self.objects.append(obj)
                
            print(f"Game loaded from {filename}")
            return True
        except Exception as e:
            print(f"Error loading: {e}")
            return False
            
    def load_level(self, filename):
        # Just call load_game with a different filename
        return self.load_game(filename)
        
    def run(self):
        last_time = time.time()
        
        while self.running:
            # Calculate delta time
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Limit dt to prevent large jumps during lag
            dt = min(dt, 0.1)
            
            # Handle events
            self.handle_events()
            
            # Update game
            self.update(dt)
            
            # Render
            self.render()
            
            # Limit FPS
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

# Launch game
if __name__ == "__main__":
    game = Game()
    game.run()
