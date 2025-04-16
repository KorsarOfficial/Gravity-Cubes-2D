import taichi as ti
import config
import sound
import numpy as np
import time
import random

# Game state variables
class GameState:
    def __init__(self):
        # Score
        self.score = 0
        
        # Game over state
        self.game_over = False
        
        # Initialize cubes list
        self.cubes = []
        
        # Физические константы
        self.gravity = 9.8
        self.friction = 0.98  # Коэффициент трения (для инерции)
        self.bounce_factor = 0.7  # Коэффициент отскока при столкновениях
        
        # Create initial cubes
        self.add_initial_cubes()
        
    # Add initial cubes for testing
    def add_initial_cubes(self):
        # Add a platform as floor
        self.add_platform([0, -5], 20.0)
        
        # Add walls
        self.add_platform([-10, 0], 1.0, [0.3, 0.5, 0.8])  # Левая стенка
        self.add_platform([10, 0], 1.0, [0.3, 0.5, 0.8])   # Правая стенка
        
        # Add several dynamic cubes at different locations
        self.create_cube([0, 3])      # Куб прямо по центру
        self.create_cube([5, 5])      # Куб справа
        self.create_cube([-5, 7])     # Куб слева
        self.create_cube([2, 10])     # Куб высоко справа
        self.create_cube([-2, 10])    # Куб высоко слева
        self.create_cube([0, 0], [0, 0], 0.5)  # Маленький куб на платформе
        
        # Добавляем монетки
        self.create_collectible([3, 1])
        self.create_collectible([-3, 1])
        
        # Добавляем движущуюся платформу
        self.create_moving_platform([0, 2], [3, 0], 3.0)
        
    # Reset game state
    def reset(self):
        self.score = 0
        self.game_over = False
        self.cubes.clear()
        self.add_initial_cubes()
        
    # Update score
    def update_score(self, points=1):
        self.score += points
        return self.score
        
    # Create cube at given position
    def create_cube(self, position, velocity=None, size=1.0, fixed=False, color=None):
        if velocity is None:
            velocity = [0, 0]
            
        if color is None:
            color = [0.8, 0.2, 0.2]
        
        # В 2D используем только X и Y, Z игнорируем
        # Если передали 3D координаты, берем только X и Y
        if len(position) > 2:
            position = position[:2]
            
        cube = {
            'position': position,
            'velocity': velocity,
            'size': size,
            'fixed': fixed,
            'active': True,
            'color': color,
            'type': 'cube',
            'rotation': 0.0,
            'rotation_speed': random.uniform(-1.0, 1.0) * 50.0,  # Случайная скорость вращения
            'acceleration': [0, 0]  # Для инерции
        }
        self.cubes.append(cube)
        sound.play_create_cube()
        return cube
    
    # Add a static platform
    def add_platform(self, position, size=10.0, color=None):
        if color is None:
            color = [0.3, 0.3, 0.8]
        return self.create_cube(position, [0, 0], size, fixed=True, color=color)
    
    # Create collectible item (coin)
    def create_collectible(self, position):
        coin = {
            'position': position,
            'velocity': [0, 0],
            'size': 0.3,
            'fixed': False,
            'active': True,
            'color': [1.0, 0.9, 0.1],  # Золотой цвет
            'type': 'collectible',
            'rotation': 0,
            'rotation_speed': 90.0  # Монетки крутятся быстрее
        }
        self.cubes.append(coin)
        return coin
    
    # Create moving platform
    def create_moving_platform(self, position, endpoints, size=2.0):
        # endpoints - массив из двух точек: [start_point, end_point]
        platform = {
            'position': position.copy(),
            'velocity': [0, 0],
            'size': size,
            'fixed': True,  # Платформа фиксированная, но перемещается программно
            'active': True,
            'color': [0.2, 0.7, 0.4],  # Зеленоватый цвет
            'type': 'moving_platform',
            'start_pos': position.copy(),
            'end_pos': [position[0] + endpoints[0], position[1] + endpoints[1]],
            'move_speed': 2.0,  # Скорость движения
            'move_dir': 1,  # 1 вперед, -1 назад
            'move_timer': 0
        }
        self.cubes.append(platform)
        return platform
    
    # Update the game state
    def update(self, dt):
        # Skip if game over
        if self.game_over:
            return
            
        # Обновляем движущиеся платформы
        self.update_moving_platforms(dt)
            
        # Update each active cube
        for i, cube in enumerate(self.cubes):
            if cube['active'] and not cube['fixed']:
                # Apply gravity (в 2D только по Y)
                cube['velocity'][1] -= self.gravity * dt
                
                # Применяем трение (для инерции)
                for j in range(2):
                    cube['velocity'][j] *= self.friction
                
                # Update position
                for j in range(2):  # Только X и Y в 2D
                    cube['position'][j] += cube['velocity'][j] * dt
                
                # Обновляем вращение объектов
                if 'rotation' in cube and 'rotation_speed' in cube:
                    cube['rotation'] += cube['rotation_speed'] * dt
                
                # Check floor collision
                if cube['position'][1] - cube['size']/2 < -10:
                    cube['position'][1] = -10 + cube['size']/2
                    cube['velocity'][1] = -cube['velocity'][1] * self.bounce_factor  # Bounce with energy loss
                
                # Check walls collision
                if cube['position'][0] - cube['size']/2 < -15:
                    cube['position'][0] = -15 + cube['size']/2
                    cube['velocity'][0] = -cube['velocity'][0] * self.bounce_factor
                    
                elif cube['position'][0] + cube['size']/2 > 15:
                    cube['position'][0] = 15 - cube['size']/2
                    cube['velocity'][0] = -cube['velocity'][0] * self.bounce_factor
                    
                # Check for cube collisions
                self.check_cube_collisions(cube)
                
                # Проверяем столкновения с монетками
                if cube['type'] == 'cube':
                    self.check_collectible_collision(cube)
                
        # Check game over conditions
        self.check_game_over()
    
    # Обновление движущихся платформ
    def update_moving_platforms(self, dt):
        for platform in self.cubes:
            if platform['active'] and platform['type'] == 'moving_platform':
                # Вычисляем текущее направление движения
                direction = platform['move_dir']
                
                # Рассчитываем новую позицию
                new_pos = [
                    platform['position'][0] + direction * platform['move_speed'] * dt,
                    platform['position'][1]
                ]
                
                # Проверяем, достигли ли конечной точки
                if direction > 0:  # Движение вперед
                    if new_pos[0] >= platform['end_pos'][0]:
                        new_pos[0] = platform['end_pos'][0]
                        platform['move_dir'] = -1  # Меняем направление
                else:  # Движение назад
                    if new_pos[0] <= platform['start_pos'][0]:
                        new_pos[0] = platform['start_pos'][0]
                        platform['move_dir'] = 1  # Меняем направление
                
                # Обновляем позицию платформы
                platform['position'] = new_pos
                
                # Перемещаем все объекты, стоящие на платформе
                for cube in self.cubes:
                    if cube != platform and cube['active'] and not cube['fixed']:
                        # Проверяем, стоит ли объект на платформе
                        if self.is_cube_on_platform(cube, platform):
                            # Двигаем объект вместе с платформой
                            cube['position'][0] += direction * platform['move_speed'] * dt
    
    # Проверка, находится ли куб на платформе
    def is_cube_on_platform(self, cube, platform):
        # Проверяем, что куб находится прямо над платформой
        horizontal_distance = abs(cube['position'][0] - platform['position'][0])
        vertical_distance = cube['position'][1] - platform['position'][1]
        
        # Куб на платформе, если он находится над ней и его нижняя граница
        # находится очень близко к верхней границе платформы
        return (horizontal_distance < (cube['size'] + platform['size'])/2 * 0.8 and
                vertical_distance > 0 and
                vertical_distance < cube['size']/2 + platform['size']/2 + 0.1)
    
    # Проверка столкновения с монетками
    def check_collectible_collision(self, cube):
        for i, collectible in enumerate(self.cubes):
            if collectible['active'] and collectible['type'] == 'collectible':
                # Расчет расстояния между центрами
                dx = cube['position'][0] - collectible['position'][0]
                dy = cube['position'][1] - collectible['position'][1]
                distance = np.sqrt(dx*dx + dy*dy)
                
                # Если расстояние меньше суммы радиусов - столкновение
                if distance < (cube['size'] + collectible['size'])/2:
                    # Собираем монетку
                    collectible['active'] = False
                    # Увеличиваем счет
                    self.update_score(10)
                    # Воспроизводим звук сбора монетки
                    sound.play_collectible()
    
    # Check for collisions between cubes
    def check_cube_collisions(self, current_cube):
        if not current_cube['active']:
            return
            
        for other_cube in self.cubes:
            # Пропускаем тот же самый куб или неактивные кубы
            if other_cube is current_cube or not other_cube['active']:
                continue
                
            # Расчет расстояния между центрами
            dx = current_cube['position'][0] - other_cube['position'][0]
            dy = current_cube['position'][1] - other_cube['position'][1]
            distance = np.sqrt(dx*dx + dy*dy)
            
            # Суммарный размер (используем как радиусы)
            combined_size = (current_cube['size'] + other_cube['size']) / 2
            
            # Если расстояние меньше суммы радиусов - есть столкновение
            if distance < combined_size:
                # Если другой куб фиксирован, просто отталкиваем текущий куб
                if other_cube['fixed']:
                    # Нормализованный вектор направления от фиксированного куба
                    if distance > 0:
                        nx = dx / distance
                        ny = dy / distance
                    else:
                        # Если кубы в той же точке, отталкиваем случайно
                        angle = np.random.uniform(0, 2 * np.pi)
                        nx = np.cos(angle)
                        ny = np.sin(angle)
                    
                    # Отталкиваем текущий куб, чтобы не было пересечения
                    overlap = combined_size - distance
                    current_cube['position'][0] += nx * overlap
                    current_cube['position'][1] += ny * overlap
                    
                    # Отражаем скорость в зависимости от коэффициента отскока
                    # Рассчитываем скорость вдоль нормали
                    dot_product = current_cube['velocity'][0] * nx + current_cube['velocity'][1] * ny
                    
                    # Меняем направление только если движемся навстречу
                    if dot_product < 0:
                        current_cube['velocity'][0] -= 2 * dot_product * nx * self.bounce_factor
                        current_cube['velocity'][1] -= 2 * dot_product * ny * self.bounce_factor
                        
                    # Воспроизводим звук при столкновении
                    sound.play_collision()
                else:
                    # Оба куба подвижны, реализуем физически корректное столкновение
                    
                    # Нормализованный вектор направления
                    if distance > 0:
                        nx = dx / distance
                        ny = dy / distance
                    else:
                        # Если кубы в той же точке, отталкиваем случайно
                        angle = np.random.uniform(0, 2 * np.pi)
                        nx = np.cos(angle)
                        ny = np.sin(angle)
                    
                    # Корректируем позиции, чтобы не было пересечения
                    overlap = combined_size - distance
                    
                    # Распределяем перемещение между кубами (обратно пропорционально их размерам)
                    total_size = current_cube['size'] + other_cube['size']
                    current_weight = other_cube['size'] / total_size
                    other_weight = current_cube['size'] / total_size
                    
                    current_cube['position'][0] += nx * overlap * current_weight
                    current_cube['position'][1] += ny * overlap * current_weight
                    other_cube['position'][0] -= nx * overlap * other_weight
                    other_cube['position'][1] -= ny * overlap * other_weight
                    
                    # Рассчитываем относительную скорость вдоль нормали
                    vx_rel = current_cube['velocity'][0] - other_cube['velocity'][0]
                    vy_rel = current_cube['velocity'][1] - other_cube['velocity'][1]
                    vel_along_normal = vx_rel * nx + vy_rel * ny
                    
                    # Продолжаем только если объекты движутся навстречу
                    if vel_along_normal > 0:
                        return
                        
                    # Коэффициент восстановления (эластичность столкновения)
                    restitution = self.bounce_factor
                    
                    # Импульс столкновения
                    # Упрощенно предполагаем, что массы пропорциональны размерам
                    mass1 = current_cube['size'] ** 3  # Объем куба ~ масса
                    mass2 = other_cube['size'] ** 3
                    
                    # Рассчитываем импульс с учетом сохранения энергии
                    impulse = -(1 + restitution) * vel_along_normal
                    impulse /= (1/mass1 + 1/mass2)
                    
                    # Применяем импульс к скоростям
                    impulse_x = impulse * nx
                    impulse_y = impulse * ny
                    
                    current_cube['velocity'][0] += impulse_x / mass1
                    current_cube['velocity'][1] += impulse_y / mass1
                    other_cube['velocity'][0] -= impulse_x / mass2
                    other_cube['velocity'][1] -= impulse_y / mass2
                    
                    # Добавляем немного случайности для интересности
                    current_cube['velocity'][0] += np.random.uniform(-0.01, 0.01)
                    current_cube['velocity'][1] += np.random.uniform(-0.01, 0.01)
                    other_cube['velocity'][0] += np.random.uniform(-0.01, 0.01)
                    other_cube['velocity'][1] += np.random.uniform(-0.01, 0.01)
                    
                    # Воспроизводим звук при столкновении
                    sound.play_collision()
    
    # Check game over conditions
    def check_game_over(self):
        # Game over if no cubes left
        dynamic_cubes = sum(1 for cube in self.cubes if cube['active'] and not cube['fixed'] and cube['type'] == 'cube')
        if dynamic_cubes == 0:
            self.game_over = True

    # Get a CubeManager instance for rendering
    def get_cube_manager(self, renderer):
        from cube_manager import CubeManager
        
        # Create a new CubeManager
        cube_manager = CubeManager(renderer)
        
        # Create cubes in the CubeManager
        for cube in self.cubes:
            if cube.get('active', False):
                # Convert from 2D to 3D position if needed
                pos = cube['position'].copy()
                if len(pos) == 2:
                    pos = [pos[0], pos[1], 0.0]
                
                # Set rotation based on type
                if cube['type'] == 'cube' or cube['type'] == 'moving_platform':
                    rotation = [
                        random.uniform(0, 360),
                        random.uniform(0, 360),
                        random.uniform(0, 360)
                    ]
                else:  # Для монеток вращение только вокруг оси Y
                    rotation = [0, cube['rotation'], 0]
                
                # Assign color based on type
                if 'color' in cube:
                    color = cube['color']
                else:
                    color = [0.8, 0.2, 0.2] if not cube.get('fixed', False) else [0.3, 0.3, 0.8]
                
                # Create cube in CubeManager
                index = cube_manager.create_cube(pos)
                
                # Update properties
                cube_manager.cubes[index]['rotation'] = rotation
                cube_manager.cubes[index]['scale'] = [cube['size'], cube['size'], cube['size']]
                cube_manager.cubes[index]['color'] = color
                
                # Для монеток другая форма (сплющенный куб)
                if cube['type'] == 'collectible':
                    cube_manager.cubes[index]['scale'] = [cube['size'], cube['size']*0.2, cube['size']]
                
        return cube_manager
        
    # Сохранить состояние в файл
    def save_state(self, filename='save.txt'):
        save_data = {
            'score': self.score,
            'cubes': self.cubes
        }
        
        with open(filename, 'w') as f:
            # Преобразуем данные в строковый формат
            import json
            json_data = json.dumps(save_data)
            f.write(json_data)
            
        print(f"Состояние сохранено в {filename}")
        
    # Загрузить состояние из файла
    def load_state(self, filename='save.txt'):
        try:
            with open(filename, 'r') as f:
                import json
                data = json.load(f)
                
                # Обновляем состояние
                self.score = data['score']
                self.cubes = data['cubes']
                
            print(f"Состояние загружено из {filename}")
            return True
        except:
            print(f"Ошибка при загрузке состояния из {filename}")
            return False 