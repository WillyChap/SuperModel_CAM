#!/usr/bin/env bash


# type "source ./setup.sh" to run this script first

### example setup script, or if you are using this on NSF-NCAR's Derecho machine:
#PATH=$(echo "$PATH" | sed -e 's,/glade\/work\/wchapman\/miniconda3/[^:]\+\(:\|$\),,g')
#PATH=$(echo "$PATH" | sed -e 's,/glade\/u\/home\/wchapman\/anaconda/[^:]\+\(:\|$\),,g')
#module load conda
#conda activate /glade/work/wchapman/conda-envs/supermodel_cam
#export CESM_ROOT=/glade/work/wchapman/supermodel_derecho_conda/

#edit this for your machine:
module load conda
conda activate /path/to/your/supermodel_env/

export CESM_ROOT=/path/to/your/cesm2.1.5/ROOT/
chmod +x init_supermodel.py 
