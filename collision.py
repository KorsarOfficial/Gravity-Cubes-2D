import config
import numpy as np

# Функция для проверки столкновения куба со стенами
def check_collision(pos, size):
    # Вычисляем границы поля
    field_min_x = (1.0 - config.field_width) / 2.0
    field_max_x = field_min_x + config.field_width
    field_min_y = (1.0 - config.field_height) / 2.0
    field_max_y = field_min_y + config.field_height
    
    # Границы куба
    cube_min_x = pos[0] - size / 2
    cube_max_x = pos[0] + size / 2
    cube_min_y = pos[1] - size / 2
    cube_max_y = pos[1] + size / 2
    
    # Проверка столкновения с внешними стенами
    if (cube_min_x <= field_min_x or cube_max_x >= field_max_x or 
        cube_min_y <= field_min_y or cube_max_y >= field_max_y):
        return True
    
    # Проверка столкновения с внутренними стенами
    for i in range(config.num_inner_walls):
        wall = config.inner_wall_data[i]
        wx1, wy1, wx2, wy2 = wall[0], wall[1], wall[2], wall[3]
        
        # Проверяем только если стена и куб пересекаются
        if ((wx1 <= cube_max_x and wx2 >= cube_min_x) and 
            (min(wy1, wy2) - config.wall_thickness/2 <= cube_max_y and max(wy1, wy2) + config.wall_thickness/2 >= cube_min_y)):
            
            # Вертикальная стена
            if abs(wx1 - wx2) < config.wall_thickness:
                wall_x = wx1
                if abs(cube_min_x - wall_x) < config.wall_thickness or abs(cube_max_x - wall_x) < config.wall_thickness:
                    return True
                    
            # Горизонтальная стена
            if abs(wy1 - wy2) < config.wall_thickness:
                wall_y = wy1
                if abs(cube_min_y - wall_y) < config.wall_thickness or abs(cube_max_y - wall_y) < config.wall_thickness:
                    return True
    
    return False 