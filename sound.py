import pygame
import os
import config

# Initialize sound system
def init():
    pygame.mixer.init()
    
    # Load sounds
    global sound_collision, sound_create_cube, music_background, sound_collectible
    
    # Create sounds directory if it doesn't exist
    if not os.path.exists('sounds'):
        os.makedirs('sounds')
        print("Created 'sounds' directory. Please add sound files there.")
    
    # Sound file paths
    collision_path = 'sounds/collision.wav'
    create_cube_path = 'sounds/create_cube.wav'
    music_path = 'sounds/background.mp3'
    collectible_path = 'sounds/collectible.wav'
    
    # Check if sound files exist and load them
    try:
        if os.path.exists(collision_path):
            sound_collision = pygame.mixer.Sound(collision_path)
        else:
            print(f"Warning: {collision_path} not found.")
            sound_collision = None
            
        if os.path.exists(create_cube_path):
            sound_create_cube = pygame.mixer.Sound(create_cube_path)
        else:
            print(f"Warning: {create_cube_path} not found.")
            sound_create_cube = None
            
        if os.path.exists(collectible_path):
            sound_collectible = pygame.mixer.Sound(collectible_path)
        else:
            print(f"Warning: {collectible_path} not found.")
            sound_collectible = None
            
        if os.path.exists(music_path):
            music_background = music_path
        else:
            print(f"Warning: {music_path} not found.")
            music_background = None
    except Exception as e:
        print(f"Error loading sounds: {e}")
        sound_collision = None
        sound_create_cube = None
        music_background = None
        sound_collectible = None

# Play collision sound
def play_collision():
    if 'sound_collision' in globals() and sound_collision:
        sound_collision.play()

# Play cube creation sound
def play_create_cube():
    if 'sound_create_cube' in globals() and sound_create_cube:
        sound_create_cube.play()

# Play collectible sound
def play_collectible():
    if 'sound_collectible' in globals() and sound_collectible:
        sound_collectible.play()

# Play background music
def play_background_music():
    if 'music_background' in globals() and music_background:
        try:
            pygame.mixer.music.load(music_background)
            pygame.mixer.music.play(-1)  # -1 means infinite loop
        except Exception as e:
            print(f"Error playing background music: {e}")

# Stop background music
def stop_background_music():
    pygame.mixer.music.stop()

# Set background music volume (0.0 - 1.0)
def set_music_volume(volume):
    pygame.mixer.music.set_volume(volume)

class SoundSystem:
    def __init__(self):
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Set volume
        pygame.mixer.music.set_volume(config.music_volume)
        
        # Load sound effects
        self.sounds = {
            'create': None,
            'collision': None,
            'game_over': None,
            'collectible': None
        }
        
        # Try to load sounds if available
        try:
            self.sounds['create'] = pygame.mixer.Sound('sounds/create.wav')
            self.sounds['collision'] = pygame.mixer.Sound('sounds/collision.wav')
            self.sounds['game_over'] = pygame.mixer.Sound('sounds/game_over.wav')
            self.sounds['collectible'] = pygame.mixer.Sound('sounds/collectible.wav')
            
            # Set sound volumes
            for sound in self.sounds.values():
                if sound:
                    sound.set_volume(config.sound_volume)
        except:
            print("Warning: Could not load sound files. Continuing without sound.")
    
    def play_create_cube(self):
        """Play sound when creating a cube"""
        if config.sound_enabled and self.sounds['create']:
            self.sounds['create'].play()
    
    def play_collision(self):
        """Play sound when a collision occurs"""
        if config.sound_enabled and self.sounds['collision']:
            self.sounds['collision'].play()
    
    def play_game_over(self):
        """Play sound when game is over"""
        if config.sound_enabled and self.sounds['game_over']:
            self.sounds['game_over'].play()
            
    def play_collectible(self):
        """Play sound when collecting an item"""
        if config.sound_enabled and self.sounds['collectible']:
            self.sounds['collectible'].play()

# Simple functions for direct use
def play_create_cube():
    # Placeholder for direct sound play
    pass

def play_collision():
    # Placeholder for direct sound play
    pass

def play_collectible():
    # Play collectible pickup sound
    pass 