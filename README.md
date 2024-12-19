# Timing-Optimized-Gate-Positioning
**1. Overview**

This project addresses the problem of optimizing gate positions in a combinational circuit to minimize the **critical path delay**. The critical path delay is the maximum delay among all possible paths from any primary input to any primary output in the circuit.

**2. Problem Description**

The task involves:

-   Assigning positions to rectangular logic gates in a 2D plane.
-   Ensuring that no gates overlap.
-   Minimizing the critical path delay using gate and wire delay parameters.

**Inputs:**

1.  Gate specifications:
    -   Width, height, and gate delay.
    -   Coordinates of input and output pins for each gate.
2.  Wire delay per unit length.
3.  Connectivity information:
    -   Which pins are connected by wires.

**Outputs:**

1.  A bounding box for all gates.
2.  The critical path with the associated delay.
3.  Locations of the bottom-left corner of each gate in the bounding box.

**3. Solution Approach**

The problem is solved systematically using the following approach:

**Step 1: Parse Input**

-   Read gate dimensions, delays, pin locations, wire delay, and connectivity from the input file.

**Step 2: Critical Path Analysis**

-   Identify the critical path in the circuit using:
    -   Gate delays.
    -   Wire delays calculated using the **Semi-Perimeter Method** (bounding box of connected pins).
-   Compute the delay for each path as: TP=∑(gi,wm)∈P(Dgi+Dwire⋅Lwm)T_P = \\sum_{(g_i, w_m) \\in P} \\left( D_{g_i} + D_{\\text{wire}} \\cdot L_{w_m} \\right)
-   Determine the **Critical Path Delay**: Tcp=max⁡P∈PTPT_{\\text{cp}} = \\max_{P \\in \\mathcal{P}} T_P

**Step 3: Placement Algorithm**

-   Assign initial positions using a heuristic to ensure:
    -   No overlaps.
    -   Compact arrangement within the bounding box.
-   Iteratively optimize gate positions to minimize the critical path delay.

**Step 4: Output Generation**

-   Output the bounding box dimensions.
-   Specify the critical path and its delay.
-   Provide the final positions of each gate.

**4. Input/Output Formats**

**Input:**

-   Gate specifications:
-   \<name_of_gate\> \<width\> \<height\> \<delay\>
-   Pin locations:
-   pins \<name_of_gate\> \<x_1, y_1\> ... \<x_m, y_m\>
-   Wire connections:
-   wire \<gate_a.pin_a\> \<gate_b.pin_b\>
-   Wire delay:
-   wire_delay \<value\>

**Output:**

-   Bounding box:
-   bounding_box \<width\> \<height\>
-   Critical path:
-   critical_path \<pin_1\> \<pin_2\> ... \<pin_n\>
-   critical_path_delay \<value\>
-   Gate positions:
-   \<name_of_gate\> \<x_coord\> \<y_coord\>

**5. Example**

**Input:**

g1 2 3 5

pins g1 0 1 2 2

g2 3 2 3

pins g2 0 0 3 1

g3 2 2 6

pins g3 0 1 0 2 2 1

wire_delay 4

wire g1.p2 g3.p1

wire g2.p2 g3.p2

**Output:**

bounding_box 7 3

critical_path g1.p1 g1.p2 g3.p1 g3.p3

critical_path_delay 27

g1 0 0

g2 2 0

g3 5 0

**6. Key Features**

-   Handles up to 1000 gates and 40,000 pins efficiently.
-   Employs the semi-perimeter method for wire length estimation.
-   Generates compact, non-overlapping gate layouts.

**7. Testing**

-   Validate against provided test cases.
-   Generate additional test cases for edge scenarios, ensuring adherence to constraints such as integral coordinates and bounding box limits.
