import random
import math
import time
from multiprocessing import Pool, cpu_count

def read_input(file):
    gates = {}
    wires = []
    wire_delay = 0
    with open(file, 'r') as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("g"):
            parts = line.split()
            gate_name = parts[0]
            gate = {
                'width': int(parts[1]),
                'height': int(parts[2]),
                'pins': [],
                'delay': int(parts[3]),
                'x': 0,
                'y': 0
            }
            i += 1
            line = lines[i].strip()
            if line.startswith("pins"):
                pin_parts = line.split()[2:]
                gate['pins'] = [(int(pin_parts[j]), int(pin_parts[j + 1])) for j in range(0, len(pin_parts), 2)]
            gates[gate_name] = gate
        elif line.startswith("wire_delay"):
            parts = line.split()
            wire_delay = int(parts[1])
        elif line.startswith("wire"):
            wire_parts = line.split()
            wires.append(
                (wire_parts[1].split('.')[0], int(wire_parts[1].split('.')[1][1:]),
                 wire_parts[2].split('.')[0], int(wire_parts[2].split('.')[1][1:]))
            )
        i += 1
    return gates, wires, wire_delay

def manhattan_distance(pin1, pin2):
    return abs(pin1[0] - pin2[0]) + abs(pin1[1] - pin2[1])

def primary_pins(gate_dict, wires):
    all_destinations = set((wire[2], wire[3]) for wire in wires)
    all_sources = set((wire[0], wire[1]) for wire in wires)

    main_inputs = set()
    for gate, gate_info in gate_dict.items():
        for i, pin in enumerate(gate_info['pins']):
            if pin[0] == 0:
                pin_num = i + 1
                if (gate, pin_num) not in all_destinations:
                    main_inputs.add((gate, pin_num))

    main_outputs = set()
    for gate, gate_info in gate_dict.items():
        for i, pin in enumerate(gate_info['pins']):
            if pin[0] == gate_info['width']:
                pin_num = i + 1
                if (gate, pin_num) not in all_sources:
                    main_outputs.add((gate, pin_num))
    return main_inputs, main_outputs


def find_all_paths_and_cycles(gates, wires, input_pins, output_pins):
    path_list = {(g, i + 1): [] for g, info in gates.items() for i in range(len(info['pins']))}

    for src_g, src_p, dst_g, dst_p in wires:
        path_list[(src_g, src_p)].append((dst_g, dst_p))

    for g, info in gates.items():
        in_pins = [i + 1 for i, p in enumerate(info['pins']) if p[0] == 0]
        out_pins = [i + 1 for i, p in enumerate(info['pins']) if p[0] == info['width']]
        for in_p in in_pins:
            for out_p in out_pins:
                path_list[(g, in_p)].append((g, out_p))

    def get_path_key(path):
        if len(path) < 3:
            return tuple((node[0], node[1]) for node in path)
        return (path[0][0],) + tuple((node[0], node[1]) for node in path[1:-1]) + (path[-1][0],)

    def search_path(start, end):
        stack = [(start, [start], {start}, {start})]
        unique_paths = {}

        while stack:
            node, path, visited, rec_stack = stack.pop()

            if node == end:
                path_key = get_path_key(path)
                if path_key not in unique_paths:
                    unique_paths[path_key] = path
                continue

            for next_node in reversed(path_list[node]):
                if next_node in rec_stack:
                    return True, path[path.index(next_node):], None, 0
                if next_node not in visited:
                    new_visited = visited | {next_node}
                    new_rec_stack = rec_stack | {next_node}
                    stack.append((next_node, path + [next_node], new_visited, new_rec_stack))

        return False, None, list(unique_paths.values()), len(unique_paths)

    input_gates = {pin[0] for pin in input_pins}
    representative_inputs = [next(pin for pin in input_pins if pin[0] == gate) for gate in input_gates]

    output_gates = {pin[0] for pin in output_pins}
    representative_outputs = [next(pin for pin in output_pins if pin[0] == gate) for gate in output_gates]

    all_paths = {}
    total = 0

    for in_pin in representative_inputs:
        for out_pin in representative_outputs:
            has_cycle, cycle, paths, count = search_path(in_pin, out_pin)

            if has_cycle:
                return True, cycle, None, 0

            if paths:
                for path in paths:
                    path_key = get_path_key(path)
                    if path_key not in all_paths:
                        all_paths[path_key] = path
                        total += 1

    return False, None, list(all_paths.values()), total
def format_cycle_path(cycle_path):
    return ' -> '.join([f"{gate}.p{pin}" for gate, pin in cycle_path])
def no_gate_overlap(gate_positions, gates_dict):
    positions = [(gate, *gate_positions[gate], gates_dict[gate]['width'], gates_dict[gate]['height'])
                 for gate in gate_positions]

    for i, (g1, x1, y1, w1, h1) in enumerate(positions):
        for g2, x2, y2, w2, h2 in positions[i + 1:]:
            if not (x1 + w1 <= x2 or x1 >= x2 + w2 or y1 + h1 <= y2 or y1 >= y2 + h2):
                return False
    return True


def greedy_grid_placement(rectangle_sequence, gate_dict):
    max_width = max(gate['width'] for gate in gate_dict.values())*2
    max_height = max(gate['height'] for gate in gate_dict.values())*2

    grid_size = int(math.ceil(len(gate_dict) ** 0.5))
    cell_size = max(max_width, max_height)
    placements = {}

    for i, gate_name in enumerate(gate_dict.keys()):
        x_pos = (i % grid_size) * cell_size
        y_pos = (i // grid_size) * cell_size
        placements[gate_name] = (x_pos, y_pos)
        gate_dict[gate_name]['x'] = x_pos
        gate_dict[gate_name]['y'] = y_pos

    return placements, (grid_size * cell_size, grid_size * cell_size)


def generate_neighbor(gate_positions, grid_size, gates_dict):
    new_positions = gate_positions.copy()
    gate_to_move = random.choice(list(new_positions.keys()))
    current_x, current_y = new_positions[gate_to_move]

    for gate_name, (x, y) in new_positions.items():
        gates_dict[gate_name]['x'] = x
        gates_dict[gate_name]['y'] = y

    delta_x = random.randint(-5, 5)
    delta_y = random.randint(-5, 5)

    new_x = max(0, min(current_x + delta_x, grid_size[0] - gates_dict[gate_to_move]['width']))
    new_y = max(0, min(current_y + delta_y, grid_size[1] - gates_dict[gate_to_move]['height']))

    new_positions[gate_to_move] = (new_x, new_y)
    return new_positions


def calculate_path_delay(path, gates, wire_delay_per_unit):
    total_delay = 0

    for i in range(len(path) - 1):
        current = path[i]
        next_node = path[i + 1]

        if current[0] == next_node[0]:
            total_delay += gates[current[0]]['delay']
        else:
            current_pin_loc = list(gates[current[0]]['pins'][current[1] - 1])
            current_pin_loc[0] += gates[current[0]]['x']
            current_pin_loc[1] += ((gates[current[0]]['y']))

            next_pin_loc = list(gates[next_node[0]]['pins'][next_node[1] - 1])
            next_pin_loc[0] += gates[next_node[0]]['x']
            next_pin_loc[1] += ((gates[next_node[0]]['y']))

            wire_length = manhattan_distance(current_pin_loc, next_pin_loc)
            total_delay += wire_delay_per_unit * wire_length

    return total_delay


def give_max_path(all_paths, gates, wire_delay):
    max_delay_path = None
    max_delay = float('-inf')

    for path in all_paths:
        delay = calculate_path_delay(path, gates, wire_delay)
        if delay > max_delay:
            max_delay = delay
            max_delay_path = path

    return max_delay_path, max_delay


def simulated_annealing(gates, initial_temp, final_temp, alpha, num_neighbors, wire_delay, all_paths):
    gate_sequence = [(name, gate['width'], gate['height']) for name, gate in gates.items()]
    gate_positions, initial_grid_size = greedy_grid_placement(gate_sequence, gates)

    current_solution = gate_positions.copy()
    for gate_name, (x, y) in current_solution.items():
        gates[gate_name]['x'] = x
        gates[gate_name]['y'] = y

    current_path, current_delay = give_max_path(all_paths, gates, wire_delay)

    best_solution = current_solution.copy()
    best_delay = current_delay
    best_path = current_path

    temp = initial_temp

    while temp > final_temp:
        for _ in range(num_neighbors):
            new_solution = generate_neighbor(current_solution, initial_grid_size, gates)

            for gate_name, (x, y) in new_solution.items():
                gates[gate_name]['x'] = x
                gates[gate_name]['y'] = y

            if no_gate_overlap(new_solution, gates):
                new_path, new_delay = give_max_path(all_paths, gates, wire_delay)
                delta = new_delay - current_delay

                if delta < 0 or random.random() < math.exp(-delta / temp):
                    current_solution = new_solution.copy()
                    current_delay = new_delay
                    current_path = new_path

                    if current_delay < best_delay:
                        best_solution = current_solution.copy()
                        best_delay = current_delay
                        best_path = current_path

        temp *= alpha

    return best_solution, best_delay, best_path


def parallel_simulated_annealing(gates, initial_temp, final_temp, alpha, num_iterations, num_neighbors, wire_delay, all_paths):
    num_workers = cpu_count()*3
    with Pool(num_workers) as pool:
        results = pool.starmap(
            simulated_annealing,
            [(gates.copy(), initial_temp, final_temp, alpha, num_neighbors, wire_delay, all_paths)
             for _ in range(num_iterations)]
        )

    return min(results, key=lambda x: x[1])


def write_output(output_file, gate_positions, gates, critical_path, critical_delay):
    min_x = min(x for _, (x, y) in gate_positions.items())
    min_y = min(y for _, (x, y) in gate_positions.items())

    shifted_positions = {
        gate: (x - min_x, y - min_y)
        for gate, (x, y) in gate_positions.items()
    }
    max_x = max(x + gates[gate]['width'] for gate, (x, y) in shifted_positions.items())
    max_y = max(y + gates[gate]['height'] for gate, (x, y) in shifted_positions.items())
    critical_path_list = []
    for i in critical_path:
        critical_path_list.append(i[0] + '.' + str("p") + str(i[1]))

    with open(output_file, 'w') as f:
        f.write(f"bounding_box {max_x} {max_y}\n")
        f.write(f"critical_path {' '.join(map(str, critical_path_list))}\n")
        f.write(f"critical_path_delay {critical_delay}\n")

        for gate, (x, y) in sorted(shifted_positions.items()):
            f.write(f"{gate} {x} {max_y-y-gates[gate]['height']}\n")


if __name__ == "__main__":
    start_time = time.perf_counter()
    gates, wires, wire_delay = read_input("input.txt")
    input_pins, output_pins = primary_pins(gates, wires)
    print("\nAnalyzing all possible paths and checking for cycles in the circuit...\n")
    has_cycle, cycle_path, all_paths, total_paths = find_all_paths_and_cycles(gates, wires, input_pins, output_pins)

    if has_cycle:
        print("Error: Circuit contains a cyclic path!")
        print("Cycle found:", format_cycle_path(cycle_path))
        with open("output.txt", 'w') as f:
            f.write(f"Error: Circuit contains a cyclic path\n")
            f.write(f"Cycle: {format_cycle_path(cycle_path)}\n")
        exit(1)

    gates_num = len(gates)
    wire_num = len(wires)

    grid_size = (5000, 5000)
    initial_temp = 1000
    final_temp = 0.01
    alpha = 0.95
    num_iterations = 10
    num_neighbors = 100

    if gates_num > 60 or wire_num > 500:
        alpha = 0.9
        final_temp = 0.01
    elif gates_num < 10 or wire_num < 20:
        alpha = 0.99
        final_temp = 0.001
    elif gates_num < 30 or wire_num < 60:
        alpha = 0.95
        final_temp = 0.01

    best_solution, best_delay, critical_path = parallel_simulated_annealing(
        gates, initial_temp, final_temp, alpha,
        num_iterations, num_neighbors, wire_delay, all_paths)

    for gate_name, (x, y) in best_solution.items():
        gates[gate_name]['x'] = x
        gates[gate_name]['y'] = y

    write_output("output.txt", best_solution, gates, critical_path, best_delay)
    end_time = time.perf_counter()
    print(f"\nExecution time: {end_time - start_time:.2f} seconds")
