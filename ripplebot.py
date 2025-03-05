import pygame
import numpy as np
import math

# Initialize Pygame
pygame.init()

# Window settings
WIDTH = 500
HEIGHT = 500
FPS = 60
CELL_SIZE = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
CURSOR_COLOR = (150, 150, 150, 128)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RippleBot")
clock = pygame.time.Clock()

# Set up font for mode display
font = pygame.font.Font(None, 36)  # Default font, size 36

# Terrain setup: 50 points across, generated with a sine wave
terrain_points = np.zeros(50, dtype=int)
num_waves = 2
amplitude = 20
base_height = 400
for i in range(50):
    x = i * 10
    angle = x * (2 * math.pi * num_waves / WIDTH)
    terrain_points[i] = base_height + int(amplitude * math.sin(angle))

# Admin mode state and deformation settings
admin_mode = False
deform_radius = 1
min_deform_radius = 1
max_deform_radius = 5
falloff_extension = 2
deform_mode = "raise"  # "raise" or "lower" mode

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
                print(f"Deform radius: {deform_radius}, Mode: {deform_mode}")  # Debug
            elif event.key == pygame.K_RIGHTBRACKET:
                deform_radius = min(max_deform_radius, deform_radius + 1)
                print(f"Deform radius: {deform_radius}, Mode: {deform_mode}")  # Debug
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                deform_mode = "raise"
                print(f"Mode set to: {deform_mode}")  # Debug
            elif event.key == pygame.K_MINUS:
                deform_mode = "lower"
                print(f"Mode set to: {deform_mode}")  # Debug

    # Handle terrain painting in admin mode
    if admin_mode and pygame.mouse.get_pressed()[0]:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        terrain_idx = min(max(mouse_x // CELL_SIZE, 0), 49)
        new_height = min(max(mouse_y, 100), HEIGHT - 50)
        extended_radius = deform_radius + falloff_extension
        for offset in range(-extended_radius, extended_radius + 1):
            idx = terrain_idx + offset
            if 0 <= idx < 50:
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

    # Clear screen
    screen.fill(WHITE)

    # Draw terrain
    poly_points = [(0, HEIGHT)]
    for x in range(len(terrain_points)):
        poly_points.append((x * CELL_SIZE, terrain_points[x]))
    poly_points.append((WIDTH, terrain_points[-1]))
    poly_points.append((WIDTH, HEIGHT))
    pygame.draw.polygon(screen, BLACK, poly_points)

    # Admin mode grid of squares
    if admin_mode:
        top_points = [(x * CELL_SIZE, terrain_points[x]) for x in range(len(terrain_points))]
        for x in range(len(terrain_points)):
            start = (x * CELL_SIZE, terrain_points[x])
            end = (x * CELL_SIZE, HEIGHT)
            pygame.draw.line(screen, GRAY, start, end, 1)
        num_horizontal = 5
        for level in range(1, num_horizontal + 1):
            y_positions = []
            for x in range(len(terrain_points)):
                height_diff = HEIGHT - terrain_points[x]
                y_pos = terrain_points[x] + (height_diff * level // (num_horizontal + 1))
                y_positions.append(y_pos)
            for x in range(len(terrain_points) - 1):
                start = (x * CELL_SIZE, y_positions[x])
                end = ((x + 1) * CELL_SIZE, y_positions[x + 1])
                pygame.draw.line(screen, GRAY, start, end, 1)
        pygame.draw.line(screen, GRAY, top_points[-1], (WIDTH, HEIGHT), 1)

        # Draw deformation area circle at cursor
        mouse_x, mouse_y = pygame.mouse.get_pos()
        circle_radius = (deform_radius * 2 + 1) * CELL_SIZE // 2
        circle_surface = pygame.Surface((circle_radius * 2, circle_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, CURSOR_COLOR, (circle_radius, circle_radius), circle_radius)
        screen.blit(circle_surface, (mouse_x - circle_radius, mouse_y - circle_radius))

        # Draw mode text in top-left corner
        mode_text = font.render(f"Mode: {deform_mode.capitalize()}", True, BLACK)
        screen.blit(mode_text, (10, 10))

    # Update display
    pygame.display.flip()
    clock.tick(FPS)

# Cleanup
pygame.quit()