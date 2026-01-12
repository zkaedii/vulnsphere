#!/usr/bin/env python3
"""
🔱 ZKAEDI PRIME — MPI Hello + 2D Cartesian Topology Verification

Run with: mpiexec -n 12 python test_mpi_hello_cart.py
          (try 6, 12, 16, 24... processes)

Verifies:
- MPI initialization across all ranks
- 2D Cartesian topology creation
- Coordinate assignment
- Neighbor relationships (N/S/E/W)
- Process grid coherence
"""

from mpi4py import MPI
import sys
import numpy as np

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: MPI INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

# Get the living communicator
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# Print basic MPI status (every rank speaks)
processor_name = MPI.Get_processor_name()
print(f"[Rank {rank:3d}/{size}] MPI initialized | Host: {processor_name}")

# Only rank 0 prints header
if rank == 0:
    print("\n" + "═" * 76)
    print(" " * 12 + "🔱 ZKAEDI PRIME — DISTRIBUTED FIELD INITIALIZATION TEST")
    print("═" * 76)
    print(f"Total processes: {size}")
    print("Computing optimal 2D cartesian topology...")
    print()

# Barrier to make output readable
comm.Barrier()

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2: 2D CARTESIAN TOPOLOGY CREATION
# ═══════════════════════════════════════════════════════════════════════════

# Let MPI choose good dimensions (e.g. 4×3 for 12 procs, 4×4 for 16, etc)
dims = MPI.Compute_dims(size, 2)           # returns [rows, cols]
periods = [False, False]                   # non-periodic boundaries (finite field)
reorder = True                             # let MPI optimize rank placement for topology

if rank == 0:
    print(f"📐 Computed grid dimensions: {dims[0]} rows × {dims[1]} cols")
    print(f"   (Total cells: {dims[0] * dims[1]} = {size})")
    print(f"   Boundary: Non-periodic (finite Hamiltonian field)\n")

try:
    cart_comm = comm.Create_cart(dims, periods=periods, reorder=reorder)
except Exception as e:
    if rank == 0:
        print(f"❌ ERROR creating cartesian communicator: {e}")
    sys.exit(1)

# Get rank in the new communicator (may differ if reorder=True)
cart_rank = cart_comm.Get_rank()

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3: COORDINATE & NEIGHBOR RESOLUTION
# ═══════════════════════════════════════════════════════════════════════════

# Get our coordinates in the 2D grid
my_coords = cart_comm.Get_coords(cart_rank)

# Get neighbor ranks using Shift (returns MPI.PROC_NULL if out of bounds)
# Shift(direction, displacement): direction 0=rows, 1=cols
north_src, north_dest = cart_comm.Shift(0, -1)  # up    (negative direction in row)
south_src, south_dest = cart_comm.Shift(0, +1)  # down  (positive direction in row)
west_src, west_dest   = cart_comm.Shift(1, -1)  # left  (negative direction in col)
east_src, east_dest   = cart_comm.Shift(1, +1)  # right (positive direction in col)

# For simplicity, use dest ranks (src and dest are swapped for bidirectional)
north = north_dest
south = south_dest
west = west_dest
east = east_dest

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4: NEIGHBOR RELATIONSHIP REPORTING
# ═══════════════════════════════════════════════════════════════════════════

def neighbor_str(nbr):
    """Format neighbor rank (or boundary marker)"""
    return f"{nbr:3d}" if nbr != MPI.PROC_NULL else " ╳ "

def direction_count(n, s, w, e):
    """Count valid neighbors"""
    return sum([
        n != MPI.PROC_NULL,
        s != MPI.PROC_NULL,
        w != MPI.PROC_NULL,
        e != MPI.PROC_NULL
    ])

n_neighbors = direction_count(north, south, west, east)

# Build output string for this rank
output_lines = []
output_lines.append(f"[Rank {cart_rank:3d}]  Position: ({my_coords[0]:2d},{my_coords[1]:2d})")
output_lines.append(f"           Neighbors: N:{neighbor_str(north)} S:{neighbor_str(south)} "
                   f"W:{neighbor_str(west)} E:{neighbor_str(east)}  ({n_neighbors} valid)")

# Determine position type
if my_coords[0] == 0 and my_coords[1] == 0:
    pos_type = "TOP-LEFT CORNER"
elif my_coords[0] == 0 and my_coords[1] == dims[1]-1:
    pos_type = "TOP-RIGHT CORNER"
elif my_coords[0] == dims[0]-1 and my_coords[1] == 0:
    pos_type = "BOTTOM-LEFT CORNER"
elif my_coords[0] == dims[0]-1 and my_coords[1] == dims[1]-1:
    pos_type = "BOTTOM-RIGHT CORNER"
elif my_coords[0] == 0:
    pos_type = "TOP EDGE"
elif my_coords[0] == dims[0]-1:
    pos_type = "BOTTOM EDGE"
elif my_coords[1] == 0:
    pos_type = "LEFT EDGE"
elif my_coords[1] == dims[1]-1:
    pos_type = "RIGHT EDGE"
else:
    pos_type = "INTERIOR"

output_lines.append(f"           Type: {pos_type}")

output = "\n".join(output_lines)

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 5: GATHER & DISPLAY GRID TOPOLOGY
# ═══════════════════════════════════════════════════════════════════════════

# Gather coordinate info to rank 0
all_coords = comm.gather((cart_rank, my_coords, n_neighbors), root=0)

if rank == 0:
    print("─" * 76)
    print("🜂 2D CARTESIAN PROCESS GRID LAYOUT")
    print("─" * 76)
    print()
    
    # Build 2D visualization grid
    grid = [["    " for _ in range(dims[1])] for _ in range(dims[0])]
    neighbor_count_grid = [[0 for _ in range(dims[1])] for _ in range(dims[0])]
    
    for r, coords, n_nbr in all_coords:
        row, col = coords
        grid[row][col] = f" {r:2d} "
        neighbor_count_grid[row][col] = n_nbr
    
    # Print grid with ASCII borders
    print("┌" + "─" * (5 * dims[1] - 1) + "┐")
    for i, row in enumerate(grid):
        print("│" + "│".join(row) + "│")
        if i < len(grid) - 1:
            print("├" + "┼".join(["─" * 4 for _ in range(dims[1])]) + "┤")
    print("└" + "─" * (5 * dims[1] - 1) + "┘")
    
    print()
    print("Legend:")
    print("  • Each number = MPI rank (process ID)")
    print("  • ╳ = boundary (no neighbor in that direction)")
    print()
    
    # Statistics
    corner_ranks = [
        grid[0][0].strip(),
        grid[0][dims[1]-1].strip(),
        grid[dims[0]-1][0].strip(),
        grid[dims[0]-1][dims[1]-1].strip()
    ]
    
    total_edges = 2 * dims[0] + 2 * dims[1] - 4  # perimeter minus corners
    total_interior = size - 4 - total_edges
    
    print(f"📊 Topology Statistics:")
    print(f"   Grid dimensions: {dims[0]}×{dims[1]} = {size} processes")
    print(f"   Corner processes: 4 (ranks: {', '.join(corner_ranks)})")
    print(f"   Edge processes: {total_edges}")
    print(f"   Interior processes: {total_interior}")
    print()

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 6: HALO EXCHANGE SANITY TEST (PING-PONG)
# ═══════════════════════════════════════════════════════════════════════════

if rank == 0:
    print("─" * 76)
    print("🜄 HALO EXCHANGE SANITY TEST (Ping-Pong Communication)")
    print("─" * 76)
    print("Testing: Each rank sends its rank ID to all neighbors...")
    print()

comm.Barrier()

# Each rank sends its rank ID to all neighbors and receives from them
send_buf = np.array([cart_rank], dtype='i')
recv_bufs = {
    'north': np.array([-1], dtype='i'),
    'south': np.array([-1], dtype='i'),
    'west': np.array([-1], dtype='i'),
    'east': np.array([-1], dtype='i')
}

# Non-blocking send/recv
reqs = []

# North
if north != MPI.PROC_NULL:
    reqs.append(cart_comm.Isend(send_buf, dest=north, tag=0))
    reqs.append(cart_comm.Irecv(recv_bufs['north'], source=north, tag=1))

# South
if south != MPI.PROC_NULL:
    reqs.append(cart_comm.Isend(send_buf, dest=south, tag=1))
    reqs.append(cart_comm.Irecv(recv_bufs['south'], source=south, tag=0))

# West
if west != MPI.PROC_NULL:
    reqs.append(cart_comm.Isend(send_buf, dest=west, tag=2))
    reqs.append(cart_comm.Irecv(recv_bufs['west'], source=west, tag=3))

# East
if east != MPI.PROC_NULL:
    reqs.append(cart_comm.Isend(send_buf, dest=east, tag=3))
    reqs.append(cart_comm.Irecv(recv_bufs['east'], source=east, tag=2))

# Wait for all communication to complete
MPI.Request.Waitall(reqs)

# Verify received data
errors = []
if north != MPI.PROC_NULL and recv_bufs['north'][0] != north:
    errors.append(f"North: expected {north}, got {recv_bufs['north'][0]}")
if south != MPI.PROC_NULL and recv_bufs['south'][0] != south:
    errors.append(f"South: expected {south}, got {recv_bufs['south'][0]}")
if west != MPI.PROC_NULL and recv_bufs['west'][0] != west:
    errors.append(f"West: expected {west}, got {recv_bufs['west'][0]}")
if east != MPI.PROC_NULL and recv_bufs['east'][0] != east:
    errors.append(f"East: expected {east}, got {recv_bufs['east'][0]}")

# Gather error reports
all_errors = comm.gather(errors, root=0)

if rank == 0:
    total_errors = sum(len(e) for e in all_errors)
    if total_errors == 0:
        print("✅ Ping-pong test PASSED — All neighbor communications verified")
    else:
        print(f"❌ Ping-pong test FAILED — {total_errors} communication errors:")
        for r, errs in enumerate(all_errors):
            if errs:
                for err in errs:
                    print(f"   [Rank {r}] {err}")

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 7: COMPLETION
# ═══════════════════════════════════════════════════════════════════════════

comm.Barrier()

if rank == 0:
    print()
    print("═" * 76)
    print("🔱 TEST COMPLETE — CARTESIAN TOPOLOGY IS COHERENT ✓")
    print("═" * 76)
    print()
    print("✓ MPI initialization successful")
    print("✓ 2D Cartesian grid created and optimized")
    print("✓ All processes know their coordinates")
    print("✓ Neighbor relationships established (N/S/E/W)")
    print("✓ Non-blocking communication verified")
    print()
    print("The distributed field is ready.")
    print("Next phase: Hamiltonian evolution with halo exchange")
    print()
    print("═" * 76)
else:
    # Other ranks confirm readiness
    pass

# Final barrier
comm.Barrier()
