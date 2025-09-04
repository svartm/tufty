import time
import random

from pimoroni import Button
from picographics import PicoGraphics, DISPLAY_TUFTY_2040
from picovector import PicoVector, Polygon, Transform

display = PicoGraphics(display=DISPLAY_TUFTY_2040)
vector = PicoVector(display)

display.set_backlight(1.0)
display.set_font("bitmap6")

button_a = Button(7, invert=False)
button_b = Button(8, invert=False)
button_c = Button(9, invert=False)
button_up = Button(22, invert=False)
button_down = Button(6, invert=False)

# Create pens
WHITE = display.create_pen(255, 255, 255)
GREY = display.create_pen(0, 0, 0)
BLACK = display.create_pen(0, 0, 0)
GREEN = display.create_pen(0, 255, 0)

# Set misc global values
WIDTH, HEIGHT = display.get_bounds() # Display size
ROWS, COLS = 5,5 # Board dimensions
BOARD = [[0 for _ in range(COLS)] for _ in range(ROWS)]

# Clear the display
def reset():
    display.set_pen(BLACK)
    display.clear()

# Write text on the display
def write(color, message):
    display.set_pen(color)
    display.text(message, 8, 8, WIDTH - 8, 2)

# Test function to draw a UI frame
def draw_frame():
    w = 2 # line weight
    display.set_pen(GREEN)
    frame = Polygon()
    # Top 0 to 320
    frame.rectangle(0, 0, WIDTH, w)
    # Bottom 0 to 320
    frame.rectangle(0, HEIGHT, WIDTH, -w)
    # Right 4 to 236
    frame.rectangle(WIDTH, w, -w, HEIGHT-2*w) # don't overwrite horizontal lines in corners
    # Left 4 to 236
    frame.rectangle(0, w, w, HEIGHT-2*w)
    # Draw and update
    vector.draw(frame)


# Helper to get neighbors with direction
def get_neighbors_with_dir(x, y):
    # Connection bitmasks
    connections = {
        (1, 0): 1,  # +x
        (0, 1): 2,  # +y
        (0, -1): 4, # -y
        (-1, 0): 8  # -x
    }
    neighbors = []
    for dx, dy in connections:
        nx, ny = (x + dx) % ROWS, (y + dy) % COLS
        neighbors.append(((nx, ny), connections[(dx, dy)]))
    return neighbors


# Generate the game board
def generate_board():
    # Initialize tile dicts
    empty_tiles = {(x, y): BOARD[x][y] for x in range(ROWS) for y in range(COLS) if (x, y) != (0, 0)}
    extendable_tiles = {(0, 0): BOARD[0][0]}  # origin tile
    full_tiles = {}


    while len(full_tiles) < ROWS * COLS:
        if not extendable_tiles:
            break  # failsafe 

        # Randomly select an extendable tile A
        A = random.choice(list(extendable_tiles.keys()))

        # Randomly select an empty neighbor B
        neighbors = [(n, d) for n, d in get_neighbors_with_dir(*A) if n in empty_tiles]
        if not neighbors:
            full_tiles[A] = extendable_tiles.pop(A)
            continue # failsafe
        B, dir_A_to_B = random.choice(neighbors)

        dir_B_to_A = {1: 8, 2: 4, 4: 2, 8: 1}[dir_A_to_B] # B connection should have opposite direction
        BOARD[A[0]][A[1]] += dir_A_to_B # Add connection to A
        extendable_tiles[A] = BOARD[A[0]][A[1]]
        empty_tiles.pop(B)
        BOARD[B[0]][B[1]] += dir_B_to_A # Add connection to B 
        # Debug print
        # print(f"New connection: A={A} val={BOARD[A[0]][A[1]]}, B={B} val={BOARD[B[0]][B[1]]}")
       
        # Check if A is now full
        neighbors_of_A = [n for n, _ in get_neighbors_with_dir(*A) if n in empty_tiles]
        if not neighbors_of_A:
            full_tiles[A] = extendable_tiles.pop(A)

        # Check if B is now full or extendable
        neighbors_of_B = [n for n, _ in get_neighbors_with_dir(*B) if n in empty_tiles]
        if not neighbors_of_B:
            full_tiles[B] = BOARD[B[0]][B[1]]
        else:
            extendable_tiles[B] = BOARD[B[0]][B[1]]

        # Check and update neighbors of B
        for n, _ in get_neighbors_with_dir(*B):
            if n not in empty_tiles and n not in full_tiles:
                n_neighbors = [m for m, _ in get_neighbors_with_dir(*n) if m in empty_tiles]
                if not n_neighbors and n in extendable_tiles:
                    full_tiles[n] = extendable_tiles.pop(n)
                
# Helper to draw a tile for net game
def draw_tile(x, y, value):
    w = 2 # grid line weight
    grid_size = 40
    tile_size = grid_size - w
    node_border = 8
    node_size = tile_size - node_border*2 # 
    pos_x = x * grid_size
    pos_y = y * grid_size
    # print("Drawing tile:", x, y)
    display.set_pen(GREEN)
    tile = Polygon()
    # Draw green square
    tile.rectangle(pos_x, pos_y, tile_size, tile_size)
    # for all but origin:
    if value in [1, 2, 4, 8]:
        # node
        tile.rectangle(pos_x + node_border, pos_y + node_border, node_size, node_size)
        tile.rectangle(pos_x, pos_y+tile_size/2-w, node_border, 2*w)
    elif value in [6, 9]:
        # straight line
        # tile.rectangle(pos_x, pos_y+grid_size/2-w, tile_size, 2*w) 
        tile.rectangle(pos_x, pos_y, tile_size/2-w, tile_size)
        tile.rectangle(pos_x, pos_y, tile_size/2+w, tile_size)
    elif value in [3, 5, 10, 12]:
        # corner
        tile.rectangle(pos_x, pos_y, tile_size/2-w, tile_size/2-w)
        tile.rectangle(pos_x, pos_y, tile_size/2+w, tile_size/2+w)
        # tile.rectangle(pos_x+grid_size/2-w, pos_y+grid_size/2-w, 2*w, 2*w) #middle pixels
    elif value in [7, 11, 13, 14]:
        # T crossing
        tile.rectangle(pos_x, pos_y, tile_size/2-w, tile_size/2-w)
        tile.rectangle(pos_x + tile_size/2+w, pos_y, tile_size/2-w, tile_size/2-w)
        tile.rectangle(pos_x, pos_y, tile_size, tile_size/2+w)
    elif value == 15:
        # + crossing
        tile.rectangle(pos_x, pos_y, tile_size/2-w, tile_size/2-w)
        tile.rectangle(pos_x + tile_size/2+w, pos_y, tile_size/2-w, tile_size/2-w)
        tile.rectangle(pos_x, pos_y + tile_size/2+w, tile_size/2-w, tile_size/2-w)
        tile.rectangle(pos_x + tile_size/2+w, pos_y + tile_size/2+w, tile_size/2-w, tile_size/2-w)
        tile.rectangle(pos_x, pos_y, tile_size, tile_size) # invert
    # todo draw origin node
    vector.draw(tile)
    display.update()
    time.sleep(0.2)

# Draw the full board
def draw_board():
    for y in range(len(BOARD[0])):
        for x in range(len(BOARD)):
            value = BOARD[x][y]            
            draw_tile(x, y, value)
    print("Finished drawing")
    display.update()
    time.sleep(5)
    

# Helper to print ascii visualization of the board
def print_board():
    # ASCII for tile values
    ascii_tiles = {
        0: " ",
        1: "╺",
        2: "╻",
        3: "┏",
        4: "╹",
        5: "┗",
        6: "┃",
        7: "┣",
        8: "╸",
        9: "━",
        10: "┓",
        11: "┳",
        12: "┛",
        13: "┻",
        14: "┫",
        15: "╋",
    }
    output = ""
    for y in range(COLS):
        for x in range(ROWS):
            output += ascii_tiles[BOARD[x][y]]
        output += "\n"
    print(output)

# Prepare game
generate_board()
print("Board generated")
print_board()

# Draw board
#draw_board()
#print("Board drawn")

# Main loop for handling user input
while True:
    if button_a.is_pressed:
        print("\nA")
        reset()
        draw_board()
        print("Board drawn!")
        display.update()
        time.sleep(2)
    if button_b.is_pressed:
        print("\nB")
        reset()
        write(GREEN, "Hello from B!")
        display.update()
        time.sleep(2)
    if button_c.is_pressed:
        print("\nC")
        reset()
        write(GREEN, "Hello from C!")
        draw_frame()
        display.update()
        time.sleep(2)
    else:
        reset()
        write(WHITE, "Press a button!")
        display.update()
    time.sleep(0.1)
