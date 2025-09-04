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

def reset():
    display.set_pen(BLACK)
    display.clear()

# Initialize board array with zeros
board = [[0 for _ in range(COLS)] for _ in range(ROWS)]

# Initialize tile dicts
empty_tiles = {(x, y): board[x][y] for x in range(ROWS) for y in range(COLS) if (x, y) != (0, 0)}
extendable_tiles = {(0, 0): board[0][0]}  # origin tile
full_tiles = {}

# Connection bitmasks
CONNECTIONS = {
    (1, 0): 1,  # +x
    (0, 1): 2,  # +y
    (0, -1): 4, # -y
    (-1, 0): 8  # -x

}

# Helper to get neighbors with direction (wrapping around edges)
def get_neighbors_with_dir(x, y):
    neighbors = []
    for dx, dy in CONNECTIONS:
        nx, ny = (x + dx) % ROWS, (y + dy) % COLS
        neighbors.append(((nx, ny), CONNECTIONS[(dx, dy)]))
    return neighbors


# Main loop to generate the game board
while len(full_tiles) < ROWS * COLS:
    if not extendable_tiles:
        break  # failsafe 

    # Randomly select one from extendable tiles A
    A = random.choice(list(extendable_tiles.keys()))

    # Find all empty neighbors of A
    neighbors = [(n, d) for n, d in get_neighbors_with_dir(*A) if n in empty_tiles]
    if not neighbors:
        full_tiles[A] = extendable_tiles.pop(A)
        continue

    # Randomly select one empty neighbor B
    B, dir_A_to_B = random.choice(neighbors)

    # B should get opposite direction bitmask
    dir_B_to_A = {1: 8, 2: 4, 4: 2, 8: 1}[dir_A_to_B]

    # Debug print
    print(f"Adding connection: A={A} val={board[A[0]][A[1]]}, B={B} val={board[B[0]][B[1]]}")

    # Update connections for A and B
    board[A[0]][A[1]] += dir_A_to_B
    extendable_tiles[A] = board[A[0]][A[1]]

    empty_tiles.pop(B)
    board[B[0]][B[1]] += dir_B_to_A

   
    # Check if A is full
    neighbors_of_A = [n for n, _ in get_neighbors_with_dir(*A) if n in empty_tiles]
    if not neighbors_of_A:
        full_tiles[A] = extendable_tiles.pop(A)

    # Check if B is full or extendable
    neighbors_of_B = [n for n, _ in get_neighbors_with_dir(*B) if n in empty_tiles]
    if not neighbors_of_B:
        full_tiles[B] = board[B[0]][B[1]]
    else:
        extendable_tiles[B] = board[B[0]][B[1]]

    # Check and update neighbors of B
    for n, _ in get_neighbors_with_dir(*B):
        if n not in empty_tiles and n not in full_tiles:
            n_neighbors = [m for m, _ in get_neighbors_with_dir(*n) if m in empty_tiles]
            if not n_neighbors and n in extendable_tiles:
                full_tiles[n] = extendable_tiles.pop(n)
                
# ASCII for tile values
ASCII_TILES = {
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

# Helper to print ascii visualization of the board
def print_board():
    output = ""
    for y in range(COLS):
        for x in range(ROWS):
            output += ASCII_TILES[board[x][y]]
        output += "\n"
    print(output)

# Print board after generation
print("Board generated")
print_board()

# Draw UI frame
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

# Helper to draw a tile
def draw_tile(x, y, value):
    w = 2 # line weight
    grid_size = 40
    print("Drawing tile:", x, y)
    display.set_pen(GREEN)
    tile = Polygon()
    # Draw green square
    tile.rectangle(x*grid_size, y*grid_size, grid_size-w, grid_size-w)
    vector.draw(tile)
    display.update()
    time.sleep(0.2)

# Draw all tiles
def draw_board():
    for y in range(len(board[0])):
        for x in range(len(board)):
            value = board[x][y]            
            draw_tile(x, y, value)
    print("Finished drawing")
    display.update()
    time.sleep(5)


# Helper function for writing text on the display
def write(color, message):
    display.set_pen(color)
    display.text(message, 8, 8, WIDTH - 8, 2)

# Main loop for handling user input
while True:
    if button_a.is_pressed:
        print("\nA")
        reset()
        draw_board()
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
