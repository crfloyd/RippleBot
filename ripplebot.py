import pygame
import numpy as np

# Initialize Pygame
pygame.init()

# Window settings
WIDTH = 500
HEIGHT = 500
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RippleBot")
clock = pygame.time.Clock()

# Terrain setup: 50 points across, flat at y=400 (100px from bottom)
terrain_points = np.full(50, 400, dtype=int)  # 50 points, all at 400

# Main loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear screen
    screen.fill(WHITE)

    # Draw terrain
    poly_points = [(0, HEIGHT)]  # Bottom-left
    for x in range(len(terrain_points)):
        poly_points.append((x * 10, terrain_points[x]))  # Terrain points
    poly_points.append((WIDTH, terrain_points[-1]))  # Extend flat to x=500
    poly_points.append((WIDTH, HEIGHT))  # Drop to bottom-right
    pygame.draw.polygon(screen, BLACK, poly_points)

    # Update display
    pygame.display.flip()
    clock.tick(FPS)

# Cleanup
pygame.quit()