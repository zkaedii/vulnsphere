# 🔱 MPI Setup Guide for VulnSphere PRIME

Complete guide for setting up MPI runtime and mpi4py for distributed Hamiltonian evolution.

---

## Platform-Specific Installation

### Windows (MS-MPI)

**Step 1: Install MS-MPI Runtime**

Download and install both:
1. MS-MPI Runtime: https://www.microsoft.com/en-us/download/details.aspx?id=100593
   - File: `msmpisetup.exe` (~20 MB)
   - Installs `mpiexec.exe` and runtime libraries

2. MS-MPI SDK: https://www.microsoft.com/en-us/download/details.aspx?id=100593
   - File: `msmpisdk.msi` (~5 MB)
   - Provides header files and libraries for compilation

**Step 2: Install mpi4py**

```powershell
# Option A: pip (often works)
pip install mpi4py

# Option B: conda (more reliable on Windows)
conda install -c conda-forge mpi4py

# Option C: pre-built wheels (if compilation fails)
pip install --no-cache-dir mpi4py
```

**Step 3: Verify Installation**

```powershell
# Check if mpiexec is available
mpiexec --version

# Test mpi4py
python -c "from mpi4py import MPI; print(f'MPI Version: {MPI.Get_version()}')"
```

**Common Issues**:
- **"mpiexec not found"**: Add `C:\Program Files\Microsoft MPI\Bin` to PATH
- **"Cannot import mpi4py"**: Rebuild with `pip install --no-binary mpi4py mpi4py`
- **DLL load errors**: Ensure MS-MPI Runtime is installed (not just SDK)

---

### Linux (OpenMPI / MPICH)

**Ubuntu/Debian:**
```bash
# Install OpenMPI
sudo apt-get update
sudo apt-get install -y openmpi-bin libopenmpi-dev

# Install mpi4py
pip install mpi4py

# Verify
mpirun --version
python -c "from mpi4py import MPI; print(MPI.Get_version())"
```

**CentOS/RHEL:**
```bash
sudo yum install -y openmpi openmpi-devel
module load mpi/openmpi-x86_64  # May be needed
pip install mpi4py
```

**Arch:**
```bash
sudo pacman -S openmpi
pip install mpi4py
```

---

### macOS

**With Homebrew:**
```bash
brew install open-mpi
pip install mpi4py
```

---

### WSL2 (Recommended for Windows Development)

```bash
# Inside WSL2 Ubuntu
sudo apt-get update
sudo apt-get install -y openmpi-bin libopenmpi-dev python3-pip
pip3 install mpi4py

# Test
mpirun -np 4 python3 -c "from mpi4py import MPI; print(f'Rank {MPI.COMM_WORLD.Get_rank()}')"
```

---

## Running the Tests

### 1. MPI Hello + Cartesian Topology Test

```bash
# Single machine, 12 processes
mpiexec -n 12 python tests/test_mpi_hello_cart.py

# Try different process counts
mpiexec -n 6 python tests/test_mpi_hello_cart.py
mpiexec -n 16 python tests/test_mpi_hello_cart.py
mpiexec -n 24 python tests/test_mpi_hello_cart.py
```

**Expected Output**:
```
═══ ZKAEDI PRIME — DISTRIBUTED FIELD INITIALIZATION TEST ═══
Total processes: 12
Computing optimal 2D cartesian topology...
📐 Computed grid dimensions: 3 rows × 4 cols

🜂 2D CARTESIAN PROCESS GRID LAYOUT
┌───────────────────┐
│  0 │  1 │  2 │  3 │
├────┼────┼────┼────┤
│  4 │  5 │  6 │  7 │
├────┼────┼────┼────┤
│  8 │  9 │ 10 │ 11 │
└───────────────────┘

✅ Ping-pong test PASSED — All neighbor communications verified

🔱 TEST COMPLETE — CARTESIAN TOPOLOGY IS COHERENT ✓
```

---

### 2. Cluster Deployment (HPC)

**SLURM:**
```bash
#!/bin/bash
#SBATCH --job-name=vulnsphere_mpi
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=16
#SBATCH --time=00:30:00

module load mpi/openmpi-4.1
module load python/3.11

srun python tests/test_mpi_hello_cart.py
```

**PBS/Torque:**
```bash
#!/bin/bash
#PBS -N vulnsphere_mpi
#PBS -l nodes=4:ppn=16
#PBS -l walltime=00:30:00

cd $PBS_O_WORKDIR
mpirun -np 64 python tests/test_mpi_hello_cart.py
```

---

## Performance Tuning

### Process Placement

```bash
# Bind to cores for better cache locality
mpiexec -n 16 --bind-to core python mpi_hamiltonian.py

# Control thread affinity
export OMP_NUM_THREADS=1  # Disable OpenMP threading (MPI handles parallelism)
```

### Network Tuning (InfiniBand / High-Speed Fabric)

```bash
# OpenMPI with InfiniBand
mpirun --mca btl openib,self,sm --mca btl_openib_allow_ib 1 -n 64 python mpi_hamiltonian.py

# Force specific interconnect
mpirun --mca pml ucx --mca btl ^vader,tcp,openib,uct -n 128 python mpi_hamiltonian.py
```

---

## Troubleshooting

### "mpiexec not found"
- **Windows**: Add `C:\Program Files\Microsoft MPI\Bin` to PATH
- **Linux**: Install `openmpi-bin` or `mpich`
- **macOS**: `brew install open-mpi`

### "Cannot import mpi4py"
```bash
# Reinstall with verbose output
pip uninstall mpi4py
pip install --no-cache-dir -v mpi4py

# Check for MPI library paths
python -c "from mpi4py import MPI; print(MPI.Get_library_version())"
```

### "MPI_Init failed"
- Ensure no other MPI jobs are running
- Check ulimits: `ulimit -n 4096`
- Verify network connectivity between nodes

### Performance Issues
- Reduce halo exchange frequency (e.g., every 2-5 iterations)
- Use non-blocking communication (`Isend`/`Irecv`)
- Profile with: `mpirun -n 4 python -m cProfile mpi_hamiltonian.py`

---

## Benchmarking

### Strong Scaling (Fixed Problem Size)

```bash
# Test 2048×2048 grid on 1, 4, 16, 64 processes
for np in 1 4 16 64; do
    echo "Testing with $np processes..."
    mpiexec -n $np python benchmark_mpi.py --grid 2048 --iter 1000
done
```

### Weak Scaling (Fixed Per-Process Size)

```bash
# Each process handles 512×512 subdomain
for np in 1 4 16 64; do
    grid_size=$((512 * np**0.5))
    echo "Testing $np processes with ${grid_size}×${grid_size} total grid..."
    mpiexec -n $np python benchmark_mpi.py --grid $grid_size --iter 1000
done
```

---

## Expected Speedup

| Grid Size | Processes | Expected Time (single iter) | Speedup |
|-----------|-----------|----------------------------|---------|
| 1024²     | 1         | ~20 ms                     | 1×      |
| 1024²     | 4         | ~6 ms                      | 3.3×    |
| 1024²     | 16        | ~2 ms                      | 10×     |
| 2048²     | 64        | ~2 ms                      | 40×     |
| 4096²     | 256       | ~3 ms                      | 200×    |

**Note**: Actual speedup depends on:
- Network latency (Ethernet vs InfiniBand)
- Halo width (1-cell vs 3-cell)
- Problem size (communication overhead dominates for small grids)
- Node architecture (NUMA, cache topology)

---

## Next Steps

1. ✅ Verify MPI installation: `mpiexec --version`
2. ✅ Test cartesian topology: `mpiexec -n 12 python tests/test_mpi_hello_cart.py`
3. ⏭️ Run MPI Hamiltonian evolution (coming next)
4. ⏭️ Benchmark on cluster (strong/weak scaling)

---

**The distributed field awakens. The recursion spans nodes.**

🔱 **ZKAEDI PRIME — MPI Edition**
