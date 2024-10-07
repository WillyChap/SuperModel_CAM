#!/usr/bin/env bash


# type "source ./setup.sh" to run this script first

PATH=$(echo "$PATH" | sed -e 's,/glade\/work\/wchapman\/miniconda3/[^:]\+\(:\|$\),,g')
PATH=$(echo "$PATH" | sed -e 's,/glade\/u\/home\/wchapman\/anaconda/[^:]\+\(:\|$\),,g')

module load conda
conda activate /glade/work/wchapman/conda-envs/supermodel_cam

export CESM_ROOT=/glade/work/wchapman/supermodel_derecho_conda/
chmod +x init_supermodel.py 
