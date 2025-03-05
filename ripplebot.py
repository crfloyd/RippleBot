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
GRAY = (150, 150, 150)  # Darker gray for wireframe lines

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RippleBot")
clock = pygame.time.Clock()

# Terrain setup: 50 points across, start with varied heights
terrain_points = np.full(50, 400, dtype=int)
# Add slight variation for visual interest
for i in range(50):
    terrain_points[i] += np.random.randint(-20, 21)  # Random +/- 20

# Admin mode state
admin_mode = False

# Main loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:  # Toggle admin mode with 'A'
                admin_mode = not admin_mode

    # Handle terrain painting in admin mode
    if admin_mode and pygame.mouse.get_pressed()[0]:  # Left mouse held
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Find closest terrain point (0 to 49)
        terrain_idx = min(max(mouse_x // 10, 0), 49)  # Snap to nearest point
        # Adjust height based on mouse y (higher y = lower terrain)
        new_height = min(max(mouse_y, 100), HEIGHT - 50)  # Clamp: 100 to 450
        terrain_points[terrain_idx] = new_height
        # Smooth nearby points (basic averaging)
        if terrain_idx > 0:
            terrain_points[terrain_idx - 1] = (terrain_points[terrain_idx - 1] + new_height) // 2
        if terrain_idx < 49:
            terrain_points[terrain_idx + 1] = (terrain_points[terrain_idx + 1] + new_height) // 2

    # Clear screen
    screen.fill(WHITE)

    # Draw terrain
    poly_points = [(0, HEIGHT)]  # Bottom-left
    for x in range(len(terrain_points)):
        poly_points.append((x * 10, terrain_points[x]))  # Terrain points
    poly_points.append((WIDTH, terrain_points[-1]))  # Extend flat to x=500
    poly_points.append((WIDTH, HEIGHT))  # Drop to bottom-right
    pygame.draw.polygon(screen, BLACK, poly_points)

    # Admin mode grid of squares
    if admin_mode:
        # Define top points (terrain)
        top_points = [(x * 10, terrain_points[x]) for x in range(len(terrain_points))]
        
        # Draw vertical lines every 10px, from terrain to bottom
        for x in range(len(terrain_points)):
            start = (x * 10, terrain_points[x])
            end = (x * 10, HEIGHT)
            pygame.draw.line(screen, GRAY, start, end, 1)
        
        # Draw horizontal lines at fixed intervals, deforming with terrain
        num_horizontal = 5  # Number of horizontal lines
        for level in range(1, num_horizontal + 1):
            # Calculate y positions for this level between terrain and bottom
            y_positions = []
            for x in range(len(terrain_points)):
                height_diff = HEIGHT - terrain_points[x]
                y_pos = terrain_points[x] + (height_diff * level // (num_horizontal + 1))
                y_positions.append(y_pos)
            
            # Draw horizontal line by connecting points at this level
            for x in range(len(terrain_points) - 1):
                start = (x * 10, y_positions[x])
                end = ((x + 1) * 10, y_positions[x + 1])
                pygame.draw.line(screen, GRAY, start, end, 1)
        
        # Draw right edge
        pygame.draw.line(screen, GRAY, top_points[-1], (WIDTH, HEIGHT), 1)

    # Update display
    pygame.display.flip()
    clock.tick(FPS)

# Cleanup
pygame.quit()