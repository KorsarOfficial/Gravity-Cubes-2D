import config
import cube_manager
import taichi as ti
import game_state
import sound
import numpy as np

# Параметры для выбора цвета
color_sliders = {
    "r": 0.9,  # Красный (0-1)
    "g": 0.2,  # Зеленый (0-1)
    "b": 0.3   # Синий (0-1)
}

# Флаги для отображения разных частей UI
show_color_picker = False
show_advanced_settings = False

# Функция для рисования UI
def draw_ui(window, mouse_pos):
    global show_color_picker, show_advanced_settings
    
    if config.show_ui:
        gui = window.get_gui()
        
        # Создаем основное окно UI
        gui.begin("Cube Control", 0.05, 0.05, 0.3, 0.5)
        
        # Основные кнопки
        if gui.button("Add Cube"):
            # Используем текущие настройки цвета при создании
            color = [color_sliders["r"], color_sliders["g"], color_sliders["b"]]
            cube_manager.add_new_cube(color=color)
            
        # Получаем текущее количество кубов и показываем их статус
        count = cube_manager.cube_count[None]
        gui.text(f"Total cubes: {count}")
        
        # Кнопка для переключения расширенных настроек
        if gui.button("Advanced Settings" if not show_advanced_settings else "Hide Settings"):
            show_advanced_settings = not show_advanced_settings
            
        # Показываем расширенные настройки, если включено
        if show_advanced_settings:
            # Настройки размера для активного куба
            active_idx = cube_manager.get_active_cube_index()
            
            if active_idx != -1:
                current_size = cube_manager.cube_sizes[active_idx]
                gui.text(f"Cube size: {current_size:.2f}")
                
                # Кнопки изменения размера
                if gui.button("Larger"):
                    cube_manager.resize_active_cube(current_size + 0.01)
                    
                if gui.button("Smaller"):
                    cube_manager.resize_active_cube(current_size - 0.01)
                
                # Кнопка для переключения выбора цвета
                if gui.button("Change Color" if not show_color_picker else "Hide Color Picker"):
                    show_color_picker = not show_color_picker
                
                # Выбор цвета, если включен
                if show_color_picker:
                    # Получаем текущий цвет куба
                    current_color = cube_manager.cube_colors[active_idx]
                    color_sliders["r"] = current_color[0]
                    color_sliders["g"] = current_color[1] 
                    color_sliders["b"] = current_color[2]
                    
                    # Цветовые слайдеры
                    color_changed = False
                    color_sliders["r"] = gui.slider_float("Red", color_sliders["r"], 0.0, 1.0)
                    color_sliders["g"] = gui.slider_float("Green", color_sliders["g"], 0.0, 1.0)
                    color_sliders["b"] = gui.slider_float("Blue", color_sliders["b"], 0.0, 1.0)
                    
                    # Кнопка применения цвета
                    if gui.button("Apply Color"):
                        new_color = [color_sliders["r"], color_sliders["g"], color_sliders["b"]]
                        cube_manager.change_active_cube_color(new_color)
                
                # Кнопка удаления куба
                if gui.button("Delete Cube"):
                    cube_manager.delete_cube(active_idx)
                
                # Кнопка сброса позиции
                if gui.button("Reset Position"):
                    cube_manager.reset_active_cube_position()
        
        # Кнопки для выбора куба
        gui.text("Cubes:")
        for i in range(count):
            is_active = (cube_manager.cube_active[i] == 1)
            color = cube_manager.cube_colors[i]
            color_text = f"[{color[0]:.1f}, {color[1]:.1f}, {color[2]:.1f}]"
            
            # Проверяем, находится ли куб в целевой зоне
            in_target = cube_manager.is_cube_in_target_zone(i)
            target_text = "(Target!)" if in_target else ""
            
            button_text = f"Select cube {i+1} {color_text} {target_text} {'(Active)' if is_active else ''}"
            if gui.button(button_text):
                # Делаем выбранный куб активным, остальные - неактивными
                for j in range(count):
                    cube_manager.cube_active[j] = 1 if j == i else 0
        
        # Звуковые настройки
        gui.text("Sound:")
        if gui.checkbox("Sound Effects", config.sound_enabled):
            config.sound_enabled = not config.sound_enabled
            
        if gui.checkbox("Music", config.music_enabled):
            config.music_enabled = not config.music_enabled
            if config.music_enabled:
                sound.play_background_music()
            else:
                sound.stop_background_music()
        
        # Инструкции
        gui.text("Controls: WASD - movement")
        gui.text("U - hide/show menu")
        gui.text("R - reset position")
        
        # Статистика
        info = game_state.get_display_info()
        if config.show_fps:
            gui.text(f"FPS: {info['fps']}")
        if config.show_speed:
            gui.text(f"Speed: {info['speed']:.2f}")
        if config.count_steps:
            gui.text(f"Steps: {info['steps']}")
        if config.count_time:
            gui.text(f"Time: {info['time']}")
        
        # Завершаем окно UI
        gui.end()

# Обработка клавиатурных событий
def handle_keyboard_events(window):
    if window.get_event(ti.ui.PRESS):
        if window.event.key == 'u':
            # Переключаем видимость UI
            config.show_ui = not config.show_ui
        elif window.event.key == 'r':
            # Сбросить позицию активного куба
            cube_manager.reset_active_cube_position()
        elif window.event.key == 'escape':
            # Выход из приложения
            window.running = False 