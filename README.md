# Gravity Cubes 2D
![Демонстрация игры](gif_readme/video_example.gif)

A 2D physics sandbox game built with Pygame where you can create and interact with objects that obey gravity, collision, and physics laws.

## Features

- Dynamic physics system with gravity, friction, and bouncing
- Multiple object types: cubes, platforms, and collectibles
- Particle effects during collisions
- Object creation via mouse clicks
- Camera controls and zoom
- Debug information display
- Save and load game states
- Multiple preset levels

## Installation

1. Make sure you have Python installed (Python 3.6 or newer recommended)
2. Install the required dependencies:
   ```
   pip install pygame
   ```
3. Run the game:
   ```
   python main.py
   ```

## Controls

### Mouse Controls
- **Left Mouse Button (LMB)**: Create a cube
- **Right Mouse Button (RMB)**: Create a platform (static object)
- **Middle Mouse Button (MMB)**: Create a collectible (coin)

### Keyboard Controls
- **W, A, S, D**: Move camera
- **Q, E**: Zoom camera in/out
- **R**: Reset the game
- **F1**: Toggle debug mode
- **ESC**: Exit the game
- **1, 2, 3**: Load preset levels
- **F5**: Save game
- **F9**: Load game

## Game Mechanics

### Objects

1. **Cubes**
   - Dynamic objects affected by gravity
   - Bounce off walls, floors, and other objects
   - Can collect coins
   - Have random rotation speed

2. **Platforms**
   - Static objects
   - Other objects bounce off them
   - Can be used to create levels

3. **Collectibles**
   - Can be collected by cubes
   - Rotate continuously
   - Create particles when collected

### Physics

- Objects are affected by gravity, pulling them downward
- Friction slows down objects over time
- Collisions result in realistic bouncing based on mass (determined by object size)
- Impulse-based collision resolution

### Particles

- Created during collisions and object creation
- Fade out over time
- Affected by gravity
- Add visual feedback to interactions

## Saving and Loading

The game supports saving your current setup to a file and loading it later. You can also load preset levels.

## Debug Mode

Press F1 to toggle debug information, which shows:
- Current FPS
- Number of active objects
- Number of particles
- Camera position and zoom level

## Custom Levels

You can create custom levels by saving your game setup and renaming the save file to `level1.txt`, `level2.txt`, or `level3.txt`.

## Extending the Game

The codebase is designed to be extensible. You can add new object types, physics behaviors, or game mechanics by modifying the appropriate classes in `main.py`.

## License

This project is open-source and free to use.

---

Enjoy playing with Gravity Cubes 2D! 