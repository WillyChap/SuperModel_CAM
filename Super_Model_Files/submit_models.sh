#!/bin/bash
#SBATCH --job-name="multi_mpi"
#SBATCH --account=nn9385k              
#SBATCH --time=0-00:10:0
#SBATCH --output=%x-%j.log
#SBATCH --nodes=8 --ntasks-per-node=128



touch /path/to/scratch/directory/CAM5_MODNAME/run/PAUSE_INIT
touch /path/to/scratch/directory/CAM6_MODNAME/run/PAUSE_INIT


# Find applications to run
DIRS=(/path/to/this/directory/CAM5_MODNAME  /path/to/this/directory/CAM6_MODNAME)


# Settings
PPA=(512 512)   # Change to be number of tasks for each job
NNODES=(4 4)    # number of nodes for each job

# Run applications
LP=0
for N in $(seq 0 1); do
    cd ${DIRS[$N]}
    
    echo "$(date -Is) - Starting application in ${DIRS[$N]}"
    SLURM_NTASKS=${PPA[$N]} SLURM_NNODES=${NNODES[$N]} SLURM_DISTRIBUTION=block,Pack ./case.submit --no-batch &

    # do the da type stuff
done

wait

echo "$(date -Is) - All applications are finished"
