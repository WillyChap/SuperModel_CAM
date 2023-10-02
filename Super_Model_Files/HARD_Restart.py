#!/usr/bin/env python

import glob
import os
import pandas as pd
import datetime
import shutil
import sys

cesmroot = os.environ.get('CESM_ROOT')

if cesmroot is None:
    raise SystemExit("ERROR: CESM_ROOT must be defined in environment")

_LIBDIR = os.path.join(cesmroot,"cime","scripts","Tools")
sys.path.append(_LIBDIR)
_LIBDIR = os.path.join(cesmroot,"cime","scripts","lib")
sys.path.append(_LIBDIR)

import datetime, glob, shutil
import CIME.build as build
from standard_script_setup import *
from CIME.case             import Case
from CIME.utils            import safe_copy
from argparse              import RawTextHelpFormatter
from CIME.locked_files          import lock_file, unlock_file

scratch_path = '/path/to/scratch/directory/' #replace path
psuedo_obs_dir='/path/to/work/directory/pseudoobs_CAM5_MODNAME_CAM6_MODNAME' #replace path
archive_dir = '/path/to/scratch/directory/store_super_cam5_cam6' #replace path
cam5_path = scratch_path+'/CAM5_MODNAME/run/' #replace path
cam6_path = scratch_path+'/CAM6_MODNAME/run/'#replace path


def replace_all_strings_in_file(file_path, search_string, replace_string):
    # Open the file in read mode
    with open(file_path, 'r') as file:
        # Read the content of the file
        content = file.read()
    
    # Replace all occurrences of the search string with the replace string
    modified_content = content.replace(search_string, replace_string)
    
    # Open the file in write mode
    with open(file_path, 'w') as file:
        # Write the modified content back to the file
        file.write(modified_content)


def write_line_to_file(file_path, line):
    with open(file_path, 'w') as file:
        file.write(line + '\n')
        
def remove_nc_bin(scratch_path):
    
    for f in glob.glob(scratch_path+"/*.nc"):
        os.remove(f)
        
    for f in glob.glob(scratch_path+"/*.bin"):
        os.remove(f)

def remove_pseudo_nc(pseudo_path):
    for f in glob.glob(pseudo_path+"/*_UVT.h1.*.nc"):
        os.remove(f)
        
def update_current_time(curr_time_str,modname):
    write_line_to_file(curr_time_str,modname+'.cam.r.1979-01-01-00000.nc')
    return True

def CONTINUE_RUN_FALSE(baseroot,basecasename):
    caseroot = os.path.join(baseroot,basecasename)
    case = Case(caseroot, read_only=False)
    print('#######copy and paste this:')
    print("cd ",caseroot)
    print("./xmlchange CONTINUE_RUN=FALSE")
    print("cd ..")
    print('#######')
    case.set_value("CONTINUE_RUN",False)
    return True


def _main_func(description):
    
    
    user_input = input("!WARNING! YOU ARE ABOUT TO ERASE EVERYTHING AND START OVER... CONTINUE?!?!?!? (y/n): ")
    
    if user_input.lower() == "n":
        print("Bailing out of the program...")
        # Add any additional cleanup or exit code here if needed
        exit()
        
        
    if user_input.lower() == "y":
        print("...Doing a hard restart...")
        # Add any additional cleanup or exit code here if needed

    
        baseroot="/path/to/this/directory" #replace path
        basecasename5="CAM5_MODNAME"

        baseroot="/path/to/this/directory" #replace path
        basecasename6="CAM6_MODNAME"

        remove_nc_bin(cam5_path)
        remove_nc_bin(cam6_path)
        remove_pseudo_nc(psuedo_obs_dir)

        update_current_time(cam5_path+'/current_time_file.txt','CAM5_MODNAME')
        update_current_time(cam6_path+'/current_time_file.txt','CAM6_MODNAME')

        CONTINUE_RUN_FALSE(baseroot,basecasename5)
        CONTINUE_RUN_FALSE(baseroot,basecasename6)

        print('...done hard restart...')
        print('... now: qsub submit_models.sh ...')

        return True 
    else: 
        print('you have to type "y" or "n"... quit being obstinate')
        exit()

if __name__ == "__main__":
    _main_func(__doc__)

