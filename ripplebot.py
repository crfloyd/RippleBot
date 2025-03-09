import pygame
import numpy as np
import math

pygame.init()

# -----------------------
# Configuration & Setup
# -----------------------
WIDTH = 1000
HEIGHT = 600
GRID_COLS = 50
CELL_SIZE = WIDTH // GRID_COLS
GRID_ROWS = HEIGHT // CELL_SIZE

FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE  = (0, 100, 200)
GRAY  = (150, 150, 150)

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Side-View Water (Fills from Bottom)")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# -----------------------
# Terrain Setup (1D)
# -----------------------
base_height = HEIGHT * 4 // 5
amplitude = HEIGHT // 25
num_waves = 2

terrain_points = np.zeros(GRID_COLS, dtype=int)
for c in range(GRID_COLS):
    x = c * CELL_SIZE
    angle = x * (2 * math.pi * num_waves / WIDTH)
    # Original sine wave
    raw_value = base_height + int(amplitude * math.sin(angle))
    # Snap to a multiple of CELL_SIZE for stair steps:
    terrain_points[c] = (raw_value // CELL_SIZE) * CELL_SIZE

# Also snap the right edge:
terrain_right_edge = base_height + int(amplitude * math.sin(WIDTH * (2 * math.pi * num_waves / WIDTH)))
terrain_right_edge = (terrain_right_edge // CELL_SIZE) * CELL_SIZE

# -----------------------
# 2D Arrays
# -----------------------
# coverage[r,c] = fraction from the BOTTOM of cell [r,c] that is occupied by terrain.
# capacity[r,c] = 1 - coverage[r,c]
# water[r,c] in [0..capacity[r,c]] is how much water fills from the BOTTOM up.
coverage = np.zeros((GRID_ROWS, GRID_COLS), dtype=float)
capacity = np.zeros((GRID_ROWS, GRID_COLS), dtype=float)
water    = np.zeros((GRID_ROWS, GRID_COLS), dtype=float)

# Settled logic to reduce flicker
settled = np.zeros((GRID_ROWS, GRID_COLS), dtype=bool)
settle_count = np.zeros((GRID_ROWS, GRID_COLS), dtype=int)

# Flow parameters
MaxValue = 1.0
MaxCompression = 0.25
MinValue = 0.001
MinFlow  = 0.0005
MaxFlow  = 0.2
FlowSpeed = 0.2
SETTLE_THRESHOLD = 8

# -----------------------
# Compute Coverage (from the bottom)
# -----------------------
def compute_coverage():
    for c in range(GRID_COLS):
        t_y = terrain_points[c]  # screen coord from top
        for r in range(GRID_ROWS):
            # Cell spans [cell_top, cell_bottom] in screen coords
            cell_top    = r * CELL_SIZE
            cell_bottom = (r + 1) * CELL_SIZE

            # Because we want coverage from the bottom:
            #   if terrain is above cell_bottom => no terrain in this cell => coverage=0
            #   if terrain is below cell_top => cell fully terrain => coverage=1
            #   otherwise partial coverage
            if t_y <= cell_top:
                # Terrain line is above entire cell => fully terrain from the bottom
                coverage[r, c] = 1.0
            elif t_y >= cell_bottom:
                # Terrain line is below entire cell => no terrain
                coverage[r, c] = 0.0
            else:
                # Partial coverage from the bottom
                terrain_pixels = cell_bottom - t_y
                cell_height    = cell_bottom - cell_top
                fraction = terrain_pixels / float(cell_height)
                coverage[r, c] = fraction

            capacity[r, c] = 1.0 - coverage[r, c]
            if water[r, c] > capacity[r, c]:
                water[r, c] = capacity[r, c]

compute_coverage()

# -----------------------
# Water Simulation
# -----------------------
def calculate_vertical_flow_value(a, b, max_cap):
    s = a + b
    if s <= MaxValue:
        desired = MaxValue
    elif s < 2*MaxValue + MaxCompression:
        desired = (MaxValue*MaxValue + s*MaxCompression)/(MaxValue + MaxCompression)
    else:
        desired = (s + MaxCompression)/2.0
    return min(desired, max_cap)

def simulate_water(iterations=3):
    global water, coverage, capacity, settled, settle_count
    rows, cols = water.shape
    global settled, settle_count

    for _ in range(iterations):
        diffs = np.zeros_like(water)

        for r in range(rows):
            for c in range(cols):
                if capacity[r, c] <= 0:
                    water[r, c] = 0
                    continue
                if water[r, c] < MinValue:
                    water[r, c] = 0
                    settled[r, c] = False
                    continue
                if settled[r, c]:
                    continue

                start_val = water[r, c]
                remaining = start_val

                # 1) Flow Down
                if r + 1 < rows and capacity[r+1, c] > 0:
                    below_val = water[r+1, c]
                    desired = calculate_vertical_flow_value(remaining, below_val, capacity[r+1, c])
                    flow = desired - below_val
                    if below_val > 0 and flow > MinFlow:
                        flow *= FlowSpeed
                    flow = max(flow, 0)
                    flow = min(flow, remaining, MaxFlow)
                    if flow > 0:
                        remaining -= flow
                        diffs[r, c]     -= flow
                        diffs[r+1, c]   += flow

                if remaining < MinValue:
                    diffs[r, c] -= remaining
                    continue

                # 2) Flow Left
                if c - 1 >= 0 and capacity[r, c-1] > 0:
                    left_val = water[r, c-1]
                    flow = (remaining - left_val)/4.0
                    if flow > MinFlow:
                        flow *= FlowSpeed
                    flow = max(flow, 0)
                    flow = min(flow, remaining, MaxFlow)
                    if left_val + flow > capacity[r, c-1]:
                        flow = capacity[r, c-1] - left_val
                        flow = max(flow, 0)
                    if flow > 0:
                        remaining -= flow
                        diffs[r, c]     -= flow
                        diffs[r, c-1]   += flow

                if remaining < MinValue:
                    diffs[r, c] -= remaining
                    continue

                # 3) Flow Right
                if c + 1 < cols and capacity[r, c+1] > 0:
                    right_val = water[r, c+1]
                    flow = (remaining - right_val)/3.0
                    if flow > MinFlow:
                        flow *= FlowSpeed
                    flow = max(flow, 0)
                    flow = min(flow, remaining, MaxFlow)
                    if right_val + flow > capacity[r, c+1]:
                        flow = capacity[r, c+1] - right_val
                        flow = max(flow, 0)
                    if flow > 0:
                        remaining -= flow
                        diffs[r, c]     -= flow
                        diffs[r, c+1]   += flow

                if remaining < MinValue:
                    diffs[r, c] -= remaining
                    continue

                # 4) Flow Up (pressure)
                if r - 1 >= 0 and capacity[r-1, c] > 0:
                    above_val = water[r-1, c]
                    desired = calculate_vertical_flow_value(remaining, above_val, capacity[r-1, c])
                    flow = remaining - desired
                    if flow > MinFlow:
                        flow *= FlowSpeed
                    flow = max(flow, 0)
                    flow = min(flow, remaining, MaxFlow)
                    if above_val + flow > capacity[r-1, c]:
                        flow = capacity[r-1, c] - above_val
                        flow = max(flow, 0)
                    if flow > 0:
                        remaining -= flow
                        diffs[r, c]     -= flow
                        diffs[r-1, c]   += flow

                # Settling check
                if abs(remaining - start_val) < 1e-9:
                    settle_count[r, c] += 1
                    if settle_count[r, c] >= SETTLE_THRESHOLD:
                        settled[r, c] = True
                else:
                    settle_count[r, c] = 0
                    settled[r, c] = False

        water += diffs
        water[water < 0] = 0
        for r2 in range(rows):
            for c2 in range(cols):
                if water[r2, c2] < MinValue:
                    water[r2, c2] = 0
                    settled[r2, c2] = False
                if water[r2, c2] > capacity[r2, c2]:
                    water[r2, c2] = capacity[r2, c2]
                    settled[r2, c2] = False

def build_stepped_polygon(terrain_points, cell_size, total_height, right_edge):
    """
    Creates a polygon that transitions from column to column with 
    horizontal + vertical steps, ensuring no angled lines.
    
    - terrain_points: array of snapped terrain heights for each column
    - cell_size: width of each column
    - total_height: bottom of the screen (e.g., HEIGHT)
    - right_edge: snapped terrain height at the far right boundary
    """
    poly = []
    # Start from the bottom-left corner
    poly.append((0, total_height))

    # For each column from 0 to second-last, create two steps:
    #  1) horizontal from (x_curr, y_curr) to (x_next, y_curr)
    #  2) vertical   from (x_next, y_curr) to (x_next, y_next)
    for c in range(len(terrain_points) - 1):
        x_curr = c * cell_size
        x_next = (c + 1) * cell_size
        y_curr = terrain_points[c]
        y_next = terrain_points[c + 1]

        # Horizontal step
        poly.append((x_curr, y_curr))
        poly.append((x_next, y_curr))

        # Vertical step
        poly.append((x_next, y_next))

    # Handle the last column
    last_x = (len(terrain_points) - 1) * cell_size
    last_y = terrain_points[-1]
    # Step horizontally to the far right
    poly.append((last_x, last_y))
    poly.append((len(terrain_points) * cell_size, last_y))

    # Then a vertical line to right_edge
    poly.append((len(terrain_points) * cell_size, right_edge))
    # Finally close at the bottom-right corner
    poly.append((len(terrain_points) * cell_size, total_height))

    return poly


# -----------------------
# Add Water (click)
# -----------------------
def add_water_at_cell(r, c, amount=0.1):
    if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
        free = capacity[r, c] - water[r, c]
        flow = min(amount, free)
        water[r, c] += flow
        settled[r, c] = False
        settle_count[r, c] = 0
        print(f"Added {flow:.2f} to row={r}, col={c}")

# -----------------------
# Main Loop
# -----------------------
admin_mode = False
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                admin_mode = not admin_mode
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.size
            CELL_SIZE = WIDTH // GRID_COLS
            GRID_ROWS = HEIGHT // CELL_SIZE
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            # Recompute or regenerate terrain as needed
            base_height = HEIGHT * 4 // 5
            amplitude = HEIGHT // 25
            for cc in range(GRID_COLS):
                x = cc * CELL_SIZE
                angle = x * (2 * math.pi * num_waves / WIDTH)
                raw_val = base_height + int(amplitude * math.sin(angle))
                # Snap to cell boundary for a step:
                terrain_points[cc] = (raw_val // CELL_SIZE) * CELL_SIZE

            # Also snap right edge:
            tmp_edge = base_height + int(amplitude * math.sin(WIDTH * (2 * math.pi * num_waves / WIDTH)))
            terrain_right_edge = (tmp_edge // CELL_SIZE) * CELL_SIZE

            coverage.resize((GRID_ROWS, GRID_COLS), refcheck=False)
            capacity.resize((GRID_ROWS, GRID_COLS), refcheck=False)
            water2 = np.zeros((GRID_ROWS, GRID_COLS), dtype=float)
            water[:] = 0
            settled.resize((GRID_ROWS, GRID_COLS), refcheck=False)
            settled[:] = False
            settle_count.resize((GRID_ROWS, GRID_COLS), refcheck=False)
            settle_count[:] = 0
            compute_coverage()

    # Add water at mouse if not in admin mode
    if not admin_mode and pygame.mouse.get_pressed()[0]:
        mx, my = pygame.mouse.get_pos()
        r = my // CELL_SIZE
        c = mx // CELL_SIZE
        add_water_at_cell(r, c, 0.5)

    # Simulate water
    simulate_water(iterations=3)

    # Clear screen
    screen.fill(WHITE)

    # -----------------------
    # Render Water
    #  - We fill from the BOTTOM of each cell up to water[r,c]*CELL_HEIGHT
    #  - Also do a "downflow hack": if the cell above has water, visually fill this cell
    # -----------------------
    rows, cols = water.shape
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            wval = water[r, c]
            if wval > 0:
                cell_top    = r * CELL_SIZE
                cell_bottom = (r + 1) * CELL_SIZE
                cell_height = cell_bottom - cell_top

                # fraction from bottom that is terrain
                terr_pixels = coverage[r, c] * cell_height
                water_pixels = wval * cell_height

                # "Downflow hack" if the cell above has water
                if r > 0 and water[r - 1, c] > 0:
                    water_pixels = cell_height - terr_pixels

                float_top = (cell_bottom - terr_pixels - water_pixels)
                float_bottom = (cell_bottom - terr_pixels)

                int_top = int(round(float_top))
                int_bottom = int(round(float_bottom))
                int_height = max(0, int_bottom - int_top + 1)

                rect = pygame.Rect(c * CELL_SIZE, int_top, CELL_SIZE, int_height)
                pygame.draw.rect(screen, BLUE, rect)

    # -----------------------
    # Render Terrain
    # -----------------------
    # Render Terrain with pure steps
    poly_points = build_stepped_polygon(
        terrain_points, 
        CELL_SIZE, 
        HEIGHT, 
        terrain_right_edge
    )
    pygame.draw.polygon(screen, BLACK, poly_points)


    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
