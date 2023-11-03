#!/bin/bash
#PBS -N multi_mpi
#PBS -A P54048000              
#PBS -l walltime=12:00:00
#PBS -q regular
#PBS -j oe
#PBS -l select=13:ncpus=36:mpiprocs=36

module purge
module load ncarenv/1.3 intel/19.0.5 ncarcompilers/0.5.0 mpt/2.22 netcdf/4.7.3 nco/4.9.5 ncl/6.6.2 python/2.7.16
module load python/3.7.9
ncar_pylib


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
