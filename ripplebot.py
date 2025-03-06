import pygame
import numpy as np
import math

# Initialize Pygame
pygame.init()

# Window settings
WIDTH = 1000
HEIGHT = 1000
GRID_COLS = 50
CELL_SIZE = WIDTH // GRID_COLS
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
CURSOR_COLOR = (150, 150, 150, 128)
BUTTON_RAISE_COLOR = (0, 200, 0)
BUTTON_LOWER_COLOR = (200, 0, 0)
SLIDER_TRACK_COLOR = (150, 150, 150)
SLIDER_HANDLE_COLOR = (255, 255, 255)
SLIDER_HANDLE_BORDER_COLOR = (0, 0, 0)

# Set up display with resizable window
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("RippleBot")
clock = pygame.time.Clock()

# Set up font for mode display
font = pygame.font.Font(None, 36)

# Terrain setup: 50 points across, generated with a sine wave
base_height = HEIGHT * 4 // 5
amplitude = HEIGHT // 25
terrain_points = np.zeros(GRID_COLS, dtype=int)
num_waves = 2
for i in range(GRID_COLS):
    x = i * CELL_SIZE
    angle = x * (2 * math.pi * num_waves / WIDTH)
    terrain_points[i] = base_height + int(amplitude * math.sin(angle))
# Height at x=WIDTH
angle = WIDTH * (2 * math.pi * num_waves / WIDTH)
terrain_height_at_width = base_height + int(amplitude * math.sin(angle))

# Admin mode state and deformation settings
admin_mode = False
deform_radius = 1
min_deform_radius = 1
max_deform_radius = 5
falloff_extension = 2
deform_mode = "raise"

# UI elements for admin mode
button_rect = pygame.Rect(10, 60, 120, 40)
slider_track_rect = pygame.Rect(10, 120, 100, 15)
slider_handle_radius = 10
slider_dragging = False

# Threshold for "near terrain" (in pixels)
NEAR_TERRAIN_THRESHOLD = 50

# Main loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                admin_mode = not admin_mode
            elif event.key == pygame.K_LEFTBRACKET:
                deform_radius = max(min_deform_radius, deform_radius - 1)
            elif event.key == pygame.K_RIGHTBRACKET:
                deform_radius = min(max_deform_radius, deform_radius + 1)
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                deform_mode = "raise"
            elif event.key == pygame.K_MINUS:
                deform_mode = "lower"
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.size
            CELL_SIZE = WIDTH // GRID_COLS
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            base_height = HEIGHT * 4 // 5
            amplitude = HEIGHT // 25
            for i in range(GRID_COLS):
                x = i * CELL_SIZE
                angle = x * (2 * math.pi * num_waves / WIDTH)
                terrain_points[i] = base_height + int(amplitude * math.sin(angle))
            angle = WIDTH * (2 * math.pi * num_waves / WIDTH)
            terrain_height_at_width = base_height + int(amplitude * math.sin(angle))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if admin_mode and button_rect.collidepoint(event.pos):
                deform_mode = "lower" if deform_mode == "raise" else "raise"
            if admin_mode:
                handle_x = slider_track_rect.x + int((deform_radius - min_deform_radius) / (max_deform_radius - min_deform_radius) * slider_track_rect.width)
                handle_pos = (handle_x, slider_track_rect.centery)
                mouse_x, mouse_y = event.pos
                if ((mouse_x - handle_x) ** 2 + (mouse_y - handle_pos[1]) ** 2) <= slider_handle_radius ** 2:
                    slider_dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            slider_dragging = False
        elif event.type == pygame.MOUSEMOTION and slider_dragging:
            mouse_x, _ = event.pos
            relative_x = max(0, min(mouse_x - slider_track_rect.x, slider_track_rect.width))
            radius_range = max_deform_radius - min_deform_radius
            new_radius = min_deform_radius + (relative_x / slider_track_rect.width) * radius_range
            deform_radius = max(min_deform_radius, min(max_deform_radius, round(new_radius)))

    # Handle terrain painting in admin mode
    if admin_mode and pygame.mouse.get_pressed()[0]:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if not button_rect.collidepoint((mouse_x, mouse_y)) and not slider_track_rect.collidepoint((mouse_x, mouse_y)):
            terrain_idx = min(max(mouse_x // CELL_SIZE, 0), GRID_COLS - 1)
            terrain_height = terrain_points[terrain_idx] if terrain_idx < GRID_COLS else terrain_height_at_width
            is_near_terrain = abs(mouse_y - terrain_height) <= NEAR_TERRAIN_THRESHOLD
            if is_near_terrain:
                new_height = min(max(mouse_y, 50), HEIGHT - 50)
                extended_radius = deform_radius + falloff_extension
                for offset in range(-extended_radius, extended_radius + 1):
                    idx = terrain_idx + offset
                    if 0 <= idx < GRID_COLS:
                        if abs(offset) <= deform_radius:
                            influence = 1.0 - abs(offset) / (deform_radius + 1)
                        else:
                            extra_distance = abs(offset) - deform_radius
                            influence = max(0, 1.0 - (extra_distance + deform_radius) / (deform_radius + falloff_extension + 1))
                        if influence > 0:
                            current_height = terrain_points[idx]
                            if deform_mode == "lower" and current_height < new_height:
                                terrain_points[idx] = int(current_height + (new_height - current_height) * influence)
                            elif deform_mode == "raise" and current_height > new_height:
                                terrain_points[idx] = int(current_height - (current_height - new_height) * influence)
                    if idx >= GRID_COLS:
                        offset_at_width = idx - (GRID_COLS - 1)
                        if abs(offset_at_width) <= deform_radius:
                            influence = 1.0 - abs(offset_at_width) / (deform_radius + 1)
                        else:
                            extra_distance = abs(offset_at_width) - deform_radius
                            influence = max(0, 1.0 - (extra_distance + deform_radius) / (deform_radius + falloff_extension + 1))
                        if influence > 0:
                            current_height = terrain_height_at_width
                            if deform_mode == "lower" and current_height < new_height:
                                terrain_height_at_width = int(current_height + (new_height - current_height) * influence)
                            elif deform_mode == "raise" and current_height > new_height:
                                terrain_height_at_width = int(current_height - (current_height - new_height) * influence)

    # Clear screen
    screen.fill(WHITE)

    # Draw terrain
    poly_points = [(0, HEIGHT)]
    for x in range(GRID_COLS):
        poly_points.append((x * CELL_SIZE, terrain_points[x]))
    poly_points.append((WIDTH, terrain_height_at_width))
    poly_points.append((WIDTH, HEIGHT))
    pygame.draw.polygon(screen, BLACK, poly_points)

    # Admin mode grid of squares
    if admin_mode:
        top_points = [(x * CELL_SIZE, terrain_points[x]) for x in range(GRID_COLS)]
        top_points.append((WIDTH, terrain_height_at_width))
        for x in range(GRID_COLS + 1):
            x_pos = x * CELL_SIZE if x < GRID_COLS else WIDTH
            start = (x_pos, top_points[x][1])
            end = (x_pos, HEIGHT)
            pygame.draw.line(screen, GRAY, start, end, 1)
        num_horizontal = 5
        for level in range(1, num_horizontal + 1):
            y_positions = []
            for x in range(GRID_COLS):
                height_diff = HEIGHT - terrain_points[x]
                y_pos = terrain_points[x] + (height_diff * level // (num_horizontal + 1))
                y_positions.append(y_pos)
            height_diff = HEIGHT - terrain_height_at_width
            y_pos = terrain_height_at_width + (height_diff * level // (num_horizontal + 1))
            y_positions.append(y_pos)
            for x in range(GRID_COLS):
                start = (x * CELL_SIZE, y_positions[x])
                end_x = (x + 1) * CELL_SIZE if x + 1 < GRID_COLS else WIDTH
                end = (end_x, y_positions[x + 1])
                pygame.draw.line(screen, GRAY, start, end, 1)

        # Handle hover effect for toggle button and slider
        mouse_x, mouse_y = pygame.mouse.get_pos()
        is_hovering_button = button_rect.collidepoint((mouse_x, mouse_y))
        is_hovering_slider = slider_track_rect.collidepoint((mouse_x, mouse_y))
        if is_hovering_button or is_hovering_slider:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Draw deformation area circle at cursor only if near terrain
        terrain_idx = min(max(mouse_x // CELL_SIZE, 0), GRID_COLS - 1)
        terrain_height = terrain_points[terrain_idx] if terrain_idx < GRID_COLS else terrain_height_at_width
        if abs(mouse_y - terrain_height) <= NEAR_TERRAIN_THRESHOLD:
            circle_radius = (deform_radius * 2 + 1) * CELL_SIZE // 2
            circle_surface = pygame.Surface((circle_radius * 2, circle_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, CURSOR_COLOR, (circle_radius, circle_radius), circle_radius)
            screen.blit(circle_surface, (mouse_x - circle_radius, mouse_y - circle_radius))

        # Draw toggle button
        button_color = BUTTON_RAISE_COLOR if deform_mode == "raise" else BUTTON_LOWER_COLOR
        if is_hovering_button:
            # Lighten the button color on hover
            button_color = tuple(min(255, c + 50) for c in button_color)
        pygame.draw.rect(screen, button_color, button_rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, button_rect, 2, border_radius=5)
        button_text = font.render(deform_mode.capitalize(), True, BLACK)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, button_text_rect)

        # Draw slider
        pygame.draw.rect(screen, SLIDER_TRACK_COLOR, slider_track_rect, border_radius=5)
        handle_x = slider_track_rect.x + int((deform_radius - min_deform_radius) / (max_deform_radius - min_deform_radius) * slider_track_rect.width)
        handle_pos = (handle_x, slider_track_rect.centery)
        pygame.draw.circle(screen, SLIDER_HANDLE_COLOR, handle_pos, slider_handle_radius)
        pygame.draw.circle(screen, SLIDER_HANDLE_BORDER_COLOR, handle_pos, slider_handle_radius, 2)
        radius_font_size = int((HEIGHT // 25) * 0.75)
        radius_font = pygame.font.Font(None, radius_font_size)
        radius_text = radius_font.render(f"Radius: {deform_radius}", True, BLACK)
        screen.blit(radius_text, (slider_track_rect.x, slider_track_rect.y + 25))

    # Update display
    pygame.display.flip()
    clock.tick(FPS)

# Cleanup
pygame.quit()