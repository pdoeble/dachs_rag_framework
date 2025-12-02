# JupyterHub on bwUniCluster & DACHS  

(Full transcription of all slides including text from embedded images)  
fileciteturn4file0

---

## Slide 30 – JupyterHub  

**Image text:**  
“JupyterHub on bwUniCluster & DACHS”

---

## Slide 31 – JupyterHub on bwUniCluster 3.0 and DACHS (1/2)

JupyterHub is a Web-frontend to Jupyter Notebooks (Julia, Python & R) providing interactive Python w/ formatting in a Web-Browser (saved as JSON)

With an account – and having logged in once to create Your home – use:

```
https://uc3-jupyter.scc.kit.edu
https://dachs-jupyter.hs-esslingen.de
```

**Image transcription:**  
Left panel shows bwUniCluster login screen, labelled “Föderierte Dienste am KIT”, login button “Login über Profil wählen”.  
Right panel shows **Resource Selection** popup with elements:

- Number of processes  
- Memory (GB)  
- Time (hours)  
- GPU selection checkbox  
- “Spawn” button

---

## Slide 32 – JupyterHub on bwUniCluster 3.0 and DACHS (2/2)

A word about resources:

- This submits the jupyterhub-spawner on Your behalf  
- If You select GPU: **one whole node** for yourself, otherwise shared!  
- For this Workshop today, we have 20 nodes reserved for now…

Please be considerate: at Resource selection, check # of free nodes  
Remember: Interactive use is the least efficient usage!

If You need a number of nodes for a lecture at specific times/dates:  
Please write an email to: `dachs-admin@hs-esslingen.de`

Currently, there’s no interactive Jupyter access to multi-GPU nodes

**Image:** identical text as above.

---

## Slide 33 – JupyterHub: First steps (1/3)

**Image transcription:**  
Left panel: Jupyter file browser  

- Tabs: *File*, *Edit*, *View*, *Run*, *Kernel*, *Tabs*, *Settings*, *Help*  
- Directories listed:  
  - DEEPNORMALS  
  - FORTAN  
  - JUPYTERHUB  
  - PICTURES  
  - PYTHON  
  - R  
  - SPATIAL  
  - bin, *.gz files

Right panel: Jupyter Launcher with icons:  

- Notebook  
- Console  
- Python 3 (Kernel)  
- Terminal

Jupyter Extensions shown:  

```
jupyter-matplotlib
```

Loaded & Available Modules pane shows list on left.

The default module `jupyter/ai` loads:  

- CUDA  
- Torch & Tensorflow  
- Pandas  
- SciKit-Learn  
- Seaborn  
- and more  

For other modules: Wiki.

---

## Slide 34 – JupyterHub: First steps (2/3)

For example for best practice (on Jupyter, Python, Visualization, …):

```
git clone https://github.com/hpcraink/workshop-parallel-jupyter
```

In a new terminal:

```
es_rakeller@reg312:~$ git clone https://github.com/hpcraink/workshop-parallel-jupyter
```

(It will show up in the file browser in a few seconds)

Then click on the cloned directory and open:

```
1_Start.ipynb
```

**Image transcription:**  
Left file tree shows new directory `workshop-parallel-jupyter`.

---

## Slide 35 – JupyterHub: First steps (3/3)

The Interactive Python Notebook File (*.ipynb) contains Markup, Python code and executed results and stores visualization to be displayed in the Browser.

**Image transcription:**  
Cell execution indicators:

- *Execute all statements*  
- *Execute current statement*  
- “File changed, needs saving” indicator  
- While a statement executes, the block will be marked as `[ * ]`  
- Once it has finished, it will be numbered consecutively `[1]`, `[2]`, …

The results will be inserted directly below the code cell.

Files included in the example repository:

- `2_Fundamentals` – explains Python programming  
- `3_Numpy` – basic matrix operations with NumPy  
- `4_Pandas` – working with large Parquet files  
- `5_Machine_Learning` – SciKit-Learn with visualization

---

## Slide 36 – JupyterHub: Best practices

Using a GPU node, check in Terminal the output of:

```
nvidia-smi
```

When using PyTorch, check the output of:

```python
import torch
print("Torch Version: ", torch.__version__)
print("CUDA version: ", torch.version.cuda)
print("CUDA avail? ", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Device count: ", torch.cuda.device_count())
    print("Device name: ", torch.cuda.get_device_name())
    print("Device capability: ", torch.cuda.get_device_capability())
    print("Device properties: ", torch.cuda.get_device_properties())
    print("CUDA bf16? ", torch.cuda.is_bf16_supported())
```

The Contextual Help is of great help, when editing (right mouse click).

**Image transcription:**  
Two screenshots showing contextual documentation popups inside Jupyter.

---

## Slide 37 – JupyterHub on bwUniCluster: Please Stop Server

On bwUniCluster **Prior to logging out**, end session to free resource.

**Image transcription:**  
Menu path:

File → Hub Control Panel →  
Buttons:  

- **Stop My Server** (red button)  
- **My Server** (blue button)

---

# Where and how to learn MPI  

Full transcription of all slides including screenshots and all code  
fileciteturn5file0

---

## Slide 38 – Title  

**Text:**  
Where and how to learn MPI  

---

## Slide 39 – Parallelization with OpenMP and OpenMPI  

A cluster consists of multiple nodes (computers) connected by a fast network (e.g., fibre optic).  
A node has many cores (in case of DACHS’ AMD 9254 / 9454: 48 / 96 cores).

Inside a node:  

- We can run a program in parallel with **Multithreading: OpenMP**

Across multiple nodes:  

- We can use **Multiprocessing combined with network communication: OpenMPI**

**Image transcription (diagram):**  

- Boxes labeled “node (computer)”  
- Inside each node → multiple cores  
- Arrows between nodes via “switch” boxes  
- Labels:  
  - “2nd process of the 3rd node communicates with the 2nd process of the 4th node”  
- Bottom captions:  
  - “OpenMP Multithreading inside a single node (communication over shared memory)”  
  - “OpenMPI Multiprocessing over multiple nodes (communication over shared memory and network)”

---

## Slide 40 – Simple example program (serial)

**Code from screenshot (complete):**

```c
#include <stdio.h>
#include <stdlib.h>

#define NUM_SAMPLES (1000*1000*1000)

int main(int argc, char* argv[])
{
    long count = 0;
    double pi;

    for(int i = 0; i < NUM_SAMPLES; i++) {
        double x = rand() / (double)RAND_MAX;
        double y = rand() / (double)RAND_MAX;
        if( (x*x + y*y) < 1.0 )
            count++;
    }
    pi = 4.0 * (double)count / (double)NUM_SAMPLES;

    printf("estimated pi = %12.10f\n", pi);
    return 0;
}
```

**Accompanying text:**  

- Estimating Pi with Monte Carlo  
- Generate random points  
- Count hits inside circle  
- Compute Pi = 4 * (hits / samples)  
- Print Pi with 10 decimal places  

---

## Slide 41 – Simple example program with OpenMP 1/3  

OpenMP specification has been defined by a consortium of industry and research since 1997.  
OpenMP 5.0 was released in 2018.  
Implemented in compiler via directives.  

In C/C++:  

```
#pragma omp
```

In Fortran:  

```
!$OMP
```

Enables multithreading.

---

## Slide 42 – Simple example program with OpenMP 2/3  

**Full code from screenshot:**

```c
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

#define NUM_SAMPLES (1000*1000*1000)

int main(int argc, char* argv[])
{
    long count = 0;
    double pi;

    #pragma omp parallel
    {
        unsigned int seed = omp_get_thread_num();
        #pragma omp for reduction(+:count)
        for(int i = 0; i < NUM_SAMPLES; i++) {
            double x = rand_r(&seed) / (double)RAND_MAX;
            double y = rand_r(&seed) / (double)RAND_MAX;
            if( (x*x + y*y) < 1.0 )
                count++;
        }
    }
    pi = 4.0 * (double)count / (double)NUM_SAMPLES;
    printf("estimated pi = %12.10f\n", pi);
    return 0;
}
```

**Comments transcribed:**  

- `omp header`  
- Variables accessible by each thread  
- Start of parallel region: creates threads  
- `omp_get_thread_num()` gives thread ID  
- Loop split across threads, reduction collects results  
- Use only thread-safe functions (`rand_r`)  
- End of parallel region  

---

## Slide 43 – Simple example program with OpenMP 3/3  

**Batch script and runs from screenshot:**

```bash
#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --time=00:10:00
#SBATCH --partition=gpu1

module load mpi/openmpi/5.0.5-gnu-13.3
gcc -c -fopenmp monte_carlo_omp.c -o monte_carlo_omp.o
gcc -o monte_carlo_omp monte_carlo_omp.o

OMP_NUM_THREADS=1   ./monte_carlo_omp
OMP_NUM_THREADS=2   ./monte_carlo_omp
OMP_NUM_THREADS=4   ./monte_carlo_omp
OMP_NUM_THREADS=8   ./monte_carlo_omp
OMP_NUM_THREADS=16  ./monte_carlo_omp
OMP_NUM_THREADS=32  ./monte_carlo_omp
```

**Performance table:**  

```
threads:       1     2     4     8    16    32
time in s:   9.25  4.63  2.33  1.17  0.59  0.30
```

---

## Slide 44 – Simple example program with OpenMPI 1/4  

MPI specification since 1994.  
MPI 4.1 released 2023.  
Implemented as libraries (OpenMPI).  
C and Fortran API.  
Enables multiprocessing + network communication.

---

## Slide 45 – Simple example program with OpenMPI 2/4  

**Full code from screenshot:**

```c
#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>

#define NUM_SAMPLES (1000*1000*1000*10)

int main(int argc, char* argv[])
{
    long rank, size;
    long count = 0;
    double pi;

    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    long local_samples = NUM_SAMPLES / size;
    unsigned int seed = rank;

    for(long i = 0; i < local_samples; i++) {
        double x = rand_r(&seed) / (double)RAND_MAX;
        double y = rand_r(&seed) / (double)RAND_MAX;
        if( (x*x + y*y) < 1.0 )
            count++;
    }

    long global_count = 0;
    MPI_Reduce(&count, &global_count, 1, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    if(rank == 0) {
        pi = 4.0 * (double)global_count / (double)NUM_SAMPLES;
        printf("estimated pi = %12.10f\n", pi);
    }

    MPI_Finalize();
    return 0;
}
```

**Notes from slide:**  

- Must split loops manually  
- Workload must exceed MPI overhead  

---

## Slide 46 – Simple example program with OpenMPI 3/4  

Notes:  

- No threading → non-thread-safe functions (`rand`) OK  
- Rank 0 = root process  
- `MPI_Reduce` collects results  
- Root prints result  
- `MPI_Finalize` terminates all processes  

---

## Slide 47 – Simple example program with OpenMPI 4/4  

**Batch script from screenshot:**

```bash
#!/bin/bash
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=48
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --partition=gpu1

module load mpi/openmpi/5.0.5-gnu-13.3
mpicc -o monte_carlo_pi_openmpi monte_carlo_pi_openmpi.c

/usr/bin/time mpirun -np 1  ./monte_carlo_pi_openmpi
/usr/bin/time mpirun -np 2  ./monte_carlo_pi_openmpi
/usr/bin/time mpirun -np 4  ./monte_carlo_pi_openmpi
/usr/bin/time mpirun -np 8  ./monte_carlo_pi_openmpi
/usr/bin/time mpirun -np 16 ./monte_carlo_pi_openmpi
/usr/bin/time mpirun -np 32 ./monte_carlo_pi_openmpi
/usr/bin/time mpirun -np 64 ./monte_carlo_pi_openmpi
```

**Performance table:**  

```
processes:           1      2      4      8     16     32     64
time (1B samples): 15.81   8.95   5.48   3.82   3.19   3.56   3.76
time (10B samples):140.44 71.43  37.17  19.44  11.13   7.78   5.87
```

---

## Slide 48 – Further Sources  

Best Practices:  
<https://wiki.bwhpc.de/e/Development/Parallel_Programming>  

OpenMP:  
<https://www.openmp.org/specifications/>  

OpenMPI:  
<https://www.open-mpi.org/>  

Further material:  
HLRS Parallel Programming Workshop  
<https://www.hlrs.de/training/hpc-training>  

bwHPC Training platform  
<https://training.bwhpc.de>  

bwHPC WIKI on Parallel Programming  
<https://wiki.bwhpc.de/e/Parallel_Programming>  

---

End of full transcription.
