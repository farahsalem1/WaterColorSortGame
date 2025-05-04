import copy
import random
import pygame
import collections  # To implement BFS using deque
import heapq

# initialize pygame
pygame.init()

# setup display
WIDTH = 500
HEIGHT = 550
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('Water Sort PyGame')
font = pygame.font.Font('freesansbold.ttf', 24)
fps = 60
timer = pygame.time.Clock()

#  only 6 colors
color_choices = [
    'red',      # 0
    'blue',     # 1
    'green',    # 2
    'purple',   # 3
    'pink',     # 4
    'white'     # 5
]

tube_colors = []
initial_colors = []
tubes = 8  # 6 filled + 2 empty
new_game = True
selected = False
tube_rects = []
select_rect = 100
win = False

# for auto-execution
solution_path = []
auto_solve = False
move_index = 0
auto_timer = 0

def generate_start():
    tubes_number = len(color_choices) + 2
    tubes_colors = [[] for _ in range(tubes_number)]
    available_colors = []

    for color_index in range(len(color_choices)):
        for _ in range(4):
            available_colors.append(color_index)

    random.shuffle(available_colors)

    for color in available_colors:
        while True:
            tube_index = random.randint(0, tubes_number - 3)
            if len(tubes_colors[tube_index]) < 4:
                tubes_colors[tube_index].append(color)
                break

    return tubes_number, tubes_colors

def draw_tubes(tubes_num, tube_cols):
    tube_boxes = []
    tubes_per_row = tubes_num // 2
    spacing = WIDTH / tubes_per_row
    for i in range(tubes_per_row):
        for j in range(len(tube_cols[i])):
            pygame.draw.rect(screen, color_choices[tube_cols[i][j]], [5 + spacing * i, 200 - (50 * j), 65, 50], 0, 3)
        box = pygame.draw.rect(screen, 'blue', [5 + spacing * i, 50, 65, 200], 5, 5)
        if select_rect == i:
            pygame.draw.rect(screen, 'green', [5 + spacing * i, 50, 65, 200], 3, 5)
        tube_boxes.append(box)

    for i in range(tubes_per_row):
        idx = i + tubes_per_row
        for j in range(len(tube_cols[idx])):
            pygame.draw.rect(screen, color_choices[tube_cols[idx][j]], [5 + spacing * i, 450 - (50 * j), 65, 50], 0, 3)
        box = pygame.draw.rect(screen, 'blue', [5 + spacing * i, 300, 65, 200], 5, 5)
        if select_rect == idx:
            pygame.draw.rect(screen, 'green', [5 + spacing * i, 300, 65, 200], 3, 5)
        tube_boxes.append(box)

    return tube_boxes

def calc_move(colors, selected_rect, destination):
    chain = True
    color_on_top = 100
    length = 1
    color_to_move = 100
    if len(colors[selected_rect]) > 0:
        color_to_move = colors[selected_rect][-1]
        for i in range(1, len(colors[selected_rect])):
            if chain:
                if colors[selected_rect][-1 - i] == color_to_move:
                    length += 1
                else:
                    chain = False
    if 4 > len(colors[destination]):
        if len(colors[destination]) == 0:
            color_on_top = color_to_move
        else:
            color_on_top = colors[destination][-1]
    if color_on_top == color_to_move:
        for i in range(length):
            if len(colors[destination]) < 4:
                if len(colors[selected_rect]) > 0:
                    colors[destination].append(color_on_top)
                    colors[selected_rect].pop(-1)
    return colors

def check_victory(colors):
    for tube in colors:
        if len(tube) == 0:
            continue
        if len(tube) != 4 or len(set(tube)) != 1:
            return False
    return True

# --- BFS Algorithm ---
def serialize_state(state):
    return tuple(tuple(tube) for tube in state)

def is_goal(state):
    return check_victory([list(tube) for tube in state])

def get_neighbors(state):
    neighbors = []
    tubes = len(state)
    for i in range(tubes):
        if not state[i]:
            continue
        top_color = state[i][-1]
        chain_length = 1
        for j in range(len(state[i]) - 2, -1, -1):
            if state[i][j] == top_color:
                chain_length += 1
            else:
                break
        for j in range(tubes):
            if i == j:
                continue
            if len(state[j]) < 4 and (not state[j] or state[j][-1] == top_color):
                new_state = [list(tube) for tube in state]
                moved = 0
                while moved < chain_length and len(new_state[j]) < 4:
                    new_state[j].append(new_state[i].pop())
                    moved += 1
                neighbors.append(((i, j), serialize_state(new_state)))
    return neighbors

def bfs_solve(start_state):
    start = serialize_state(start_state)
    queue = collections.deque([(start, [])])
    visited = set()
    visited.add(start)

    while queue:
        current, path = queue.popleft()

        if is_goal(current):
            print(" Solution found in", len(path), "moves.")
            return path

        for move, neighbor in get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [move]))

    print(" No solution found.")
    return None

# --- A* Algorithm ---
def heuristic(state):
    h = 0
    for tube in state:
        if not tube:
            continue
        if len(set(tube)) != 1:
            h += len(tube)
    return h

def a_star_solve(start_state):
    start = serialize_state(start_state)
    frontier = []
    heapq.heappush(frontier, (heuristic(start), 0, start, []))
    visited = set()

    while frontier:
        est_total_cost, cost_so_far, current, path = heapq.heappop(frontier)

        if current in visited:
            continue
        visited.add(current)

        if is_goal(current):
            print(" Solution found in", len(path), "moves.")
            return path

        for move, neighbor in get_neighbors(current):
            if neighbor not in visited:
                new_cost = cost_so_far + 1
                heapq.heappush(frontier, (
                    new_cost + heuristic(neighbor),
                    new_cost,
                    neighbor,
                    path + [move]
                ))
    print(" No solution found.")
    return None

# --- Automatically select algorithm ---
def choose_algorithm(tube_colors):
    # If the puzzle seems small, BFS can solve it faster
    # You can choose this threshold based on the number of filled tubes or other logic.
    # For simplicity, we'll choose BFS if the initial state is already small
    total_colors = sum(len(tube) for tube in tube_colors)
    if total_colors < 16:  # You can adjust this threshold
        return bfs_solve
    else:
        return a_star_solve

# --- Game Loop ---
run = True
while run:
    screen.fill('black')
    timer.tick(fps)

    if new_game:
        tubes, tube_colors = generate_start()
        initial_colors = copy.deepcopy(tube_colors)
        new_game = False
        solution_path = []
        auto_solve = False
        move_index = 0

        # Select the solving algorithm based on the state of the game
        solve_algorithm = choose_algorithm(tube_colors)
        print(f"Selected algorithm: {solve_algorithm.__name__}")

    else:
        tube_rects = draw_tubes(tubes, tube_colors)

    # Execute the selected solution steps (BFS or A*)
    if auto_solve and solution_path and move_index < len(solution_path):
        auto_timer += 1
        if auto_timer > fps // 2:
            src, dst = solution_path[move_index]
            tube_colors = calc_move(tube_colors, src, dst)
            move_index += 1
            auto_timer = 0
        if move_index >= len(solution_path):
            auto_solve = False

    win = check_victory(tube_colors)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                tube_colors = copy.deepcopy(initial_colors)
            elif event.key == pygame.K_RETURN:
                new_game = True
            elif event.key == pygame.K_s:
                print(" Solving with selected algorithm...")
                solution_path = solve_algorithm(tube_colors)
                if solution_path:
                    auto_solve = True
                    move_index = 0
                    auto_timer = 0

        if event.type == pygame.MOUSEBUTTONDOWN:
            if not selected:
                for item in range(len(tube_rects)):
                    if tube_rects[item].collidepoint(event.pos):
                        selected = True
                        select_rect = item
            else:
                for item in range(len(tube_rects)):
                    if tube_rects[item].collidepoint(event.pos):
                        dest_rect = item
                        tube_colors = calc_move(tube_colors, select_rect, dest_rect)
                        selected = False
                        select_rect = 100

    if win:
        victory_text = font.render('You Won! Press Enter for a new board!', True, 'white')
        screen.blit(victory_text, (30, 265))

    restart_text = font.render('Space: Restart | Enter: New | S: Solve', True, 'white')
    screen.blit(restart_text, (10, 10))

    pygame.display.flip()

pygame.quit()
