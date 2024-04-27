#!/bin/bash
#PBS -N multi_mpi
#PBS -A P54048000              
#PBS -l walltime=12:00:00
#PBS -q regular
#PBS -j oe
#PBS -l select=13:ncpus=36:mpiprocs=36

module load conda
conda activate npl-2023b

touch /path/to/scratch/directory/CAM5_MODNAME/run/PAUSE_INIT
touch /path/to/scratch/directory/CAM6_MODNAME/run/PAUSE_INIT


# Find applications to run
DIRS=(/path/to/this/directory/CAM5_MODNAME  /path/to/this/directory/CAM6_MODNAME)

# Settings
PPA=(144 324)   # Change to be number of tasks for each job

# Run applications
LP=0

for N in $(seq 0 1); do
    cd ${DIRS[$N]}

    FP=$((LP + 1))
    LP=$((FP + ${PPA[$N]} - 1))

    sed -n "$FP,$LP p" $PBS_NODEFILE > my.nodefile

    echo "$(date -Is) - Starting application in ${DIRS[$N]}"
    
    PBS_NODEFILE=${DIRS[$N]}/my.nodefile ./case.submit --no-batch  &

    # do the da type stuff
done

wait

echo "$(date -Is) - All applications are finished"
