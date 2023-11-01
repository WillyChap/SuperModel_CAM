#!/usr/bin/env python
import os, sys
import shutil

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

###FIX THIS
def stage_source_mods(case, user_mods_dir,modnam):
    print('Work in Progress... check to see if this works.')
    caseroot = case.get_value("CASEROOT")
    for usermod in glob.iglob(user_mods_dir+"/*.F90"):
        
        if modnam =="CAM5_nub1": 
            if "cam6" in usermod:
                continue
            elif "cam5" in usermod:
                safe_copy(usermod, caseroot+'/SourceMods/src.cam/')
                os.rename(caseroot+'/SourceMods/src.cam/nudging_cam5.F90', caseroot+'/SourceMods/src.cam/nudging.F90')
                
            else:
                safe_copy(usermod, caseroot+'/SourceMods/src.cam/')
                
        if modnam =="CAM6_nub1": 
            if "cam6" in usermod:
                safe_copy(usermod, caseroot+'/SourceMods/src.cam/')
                os.rename(caseroot+'/SourceMods/src.cam/nudging_cam6.F90', caseroot+'/SourceMods/src.cam/nudging.F90')
            elif "cam5" in usermod:
                continue
            else:
                safe_copy(usermod, caseroot+'/SourceMods/src.cam/')

def create_directory(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")
    else:
        print(f"Directory '{directory_path}' already exists.")

def write_line_to_file(file_path, line):
    with open(file_path, 'w') as file:
        file.write(line + '\n')

def stage_current_time(rundir,modname):
    fn_curr_time = rundir +'/current_time_file.txt'
    points_len = sorted(glob.glob(rundir+'/rpointer*'))
    
    if len(points_len) > 0:
        for dat_path in sorted(glob.glob(rundir+'/rpointer*')):
            with open(dat_path, 'r') as file:
                data = file.read().replace('\n', '')
            rpoint_dat = data.split('.')[-2]
        write_line_to_file(fn_curr_time,modname+'.cam.r.'+rpoint_dat+'.nc')
    else: 
        write_line_to_file(fn_curr_time,modname+'.cam.r.1979-01-01-00000.nc')

def per_run_case_updates(case, user_mods_dir, rundir,modnam):
    caseroot = case.get_value("CASEROOT")
    basecasename = os.path.basename(caseroot)
    unlock_file("env_case.xml",caseroot=caseroot)
    casename = basecasename
    case.set_value("CASE",casename)
    case.flush()
    lock_file("env_case.xml",caseroot=caseroot)
    case.set_value("CONTINUE_RUN",False)
    case.set_value("PROJECT","P54048000") #replace path
    # restage user_nl files for each run
    for usermod in glob.iglob(user_mods_dir+"/user*"):
        safe_copy(usermod, caseroot)
    case.case_setup()
    
    stage_source_mods(case, user_mods_dir,modnam)


def build_base_case(baseroot, basecasename,res, compset, overwrite,
                    user_mods_dir,psuedo_obs_dir, project, pecount=None,inc_int=6):
    
    caseroot = os.path.join(baseroot,basecasename)

    if overwrite and os.path.isdir(caseroot):
        shutil.rmtree(caseroot)
            
    with Case(caseroot, read_only=False) as case:
        if not os.path.isdir(caseroot):
            
            case.create(os.path.basename(caseroot), cesmroot, compset, res,
                        run_unsupported=True, answer="r",walltime="12:00:00",
                        user_mods_dir=user_mods_dir, pecount=pecount, project=project,machine_name="cheyenne")
            
            # make sure that changing the casename will not affect these variables
         
            #xml change all of our shit

            if basecasename =="CAM5_MODNAME": 
                case.set_value("CAM_CONFIG_OPTS","-phys cam5 -nlev 32")
                case.set_value("NTASKS", 72)
                
            if basecasename =="CAM6_MODNAME":
                case.set_value("NTASKS", 216)
            
            case.set_value("DOUT_S",False)
            case.set_value("STOP_OPTION","nhours")
            case.set_value("STOP_N", 6900420)
            case.set_value("JOB_QUEUE", "regular")
            case.set_value("ROF_NCPL", "$ATM_NCPL")
            case.set_value("GLC_NCPL", "$ATM_NCPL")
            case.set_value("NTHRDS", 1)
            case.set_value("GLC_NCPL", "$ATM_NCPL")
            case.set_value("BATCH_SYSTEM","none")
            #see https://github.com/ESMCI/cime/issues/3209
            
            #user_namelist_cam:
            #case.set_value("CLM_NAMELIST_OPTS", "use_init_interp=.true.")

        rundir = case.get_value("RUNDIR")
        per_run_case_updates(case, user_mods_dir, rundir,basecasename)
        update_namelist(baseroot,basecasename,psuedo_obs_dir,inc_int)
        stage_current_time(rundir,basecasename)
        print('...building case...')
        #print(caseroot)
        #print(case)
        build.case_build(caseroot, case=case, save_build_provenance=False)
        print('...done build...')

        return caseroot

def update_namelist(baseroot,basecasename,psuedo_obs_dir,inc_int):
    
    caseroot = os.path.join(baseroot,basecasename)
    fn_nl = caseroot+'/user_nl_cam'
    
    lines =[" ",
        "nhtfrq = 0, -"+str(inc_int),
        "mfilt = 1, 1",
        "ndens = 2, 2",
        "fincl2 = 'U:A','V:A', 'Q:A', 'T:A', 'PS:A', 'Nudge_U', 'Nudge_V', 'Nudge_T', 'Target_U', 'Target_V', 'Target_T'",
        "&nudging_nl",
         " Nudge_Model        =.true.",
         " Nudge_Path         ='"+psuedo_obs_dir+"'",
         " Nudge_File_Template='/test_pseudoobs_UVT.h1.%y-%m-%d-%s.nc'",
         " Nudge_Beg_Year =1979",
         " Nudge_Beg_Month=1",
         " Nudge_Beg_Day=1",
         " Nudge_End_Year =2019",
         " Nudge_End_Month=8",
         " Nudge_End_Day  =31",
         " Nudge_Uprof =2",
         " Nudge_Vprof =2",
         " Nudge_Tprof =2",
         " Nudge_Qprof =0",
         " Nudge_PSprof =0",
         " Nudge_Ucoef =1.0",
         " Nudge_Vcoef =1.0",
         " Nudge_Tcoef =1.0",
         " Nudge_Qcoef =0.0",
         " Nudge_Force_Opt = 1",
         " Nudge_Times_Per_Day = 4",
         " Model_Times_Per_Day = 48",
         " Nudge_TimeScale_Opt = 0",
         " Nudge_Vwin_Lindex = 6.",
         " Nudge_Vwin_Ldelta = 0.001",
         " Nudge_Vwin_Hindex = 33.",
         " Nudge_Vwin_Hdelta = 0.001",
         " Nudge_Vwin_Invert = .false.",
         " Nudge_Hwin_lat0     = 0.",
         " Nudge_Hwin_latWidth = 999.",
         " Nudge_Hwin_latDelta = 1.0",
         " Nudge_Hwin_lon0     = 180.",
         " Nudge_Hwin_lonWidth = 999.",
         " Nudge_Hwin_lonDelta = 1.0",
         " Nudge_Hwin_Invert   = .false.",
        ]
    
    with open(fn_nl, "a") as file:
        for line in lines:
            file.write(line + "\n")

def make_findtime(baseroot,basecasename,rundir):
    print("this is not done")
    lines=[""]
    
    fn_ft = rundir+'/find_time.txt'
    
    with open(fn_nl, "a") as file:
        for line in lines:
            file.write(line + "\n")

def _main_func(description):
    inc_int=6
    psuedo_obs_dir='/path/to/work/directory/pseudoobs_CAM5_MODNAME_CAM6_MODNAME' #replace path !!!must be your work dir!!!
    create_directory(psuedo_obs_dir)
    safe_copy('/path/to/this/directory/Pseudo_Obs_Files/Template_Nudging_File.nc',psuedo_obs_dir) #replace path git
    
    archive_dir = '/path/to/scratch/directory/store_super_cam5_cam6' #replace path !!!must be your scratch dir!!!
    create_directory(archive_dir)
    
    #one -- CAM5
    baseroot="/path/to/this/directory" #replace path
    basecasename5="CAM5_MODNAME"
    res = "f09_g16"
    compset= "HIST_CAM50_CLM50%SP_CICE%PRES_DOCN%DOM_MOSART_SGLC_SWAV"
    user_mods_dir="/path/to/this/directory/Source_Mod_Files" #replace path to git directory
    overwrite = True
    caseroot = build_base_case(baseroot, basecasename5, res,
                            compset, overwrite, user_mods_dir,psuedo_obs_dir,project="P54048000",inc_int=inc_int) #replace path /project code
    
    #two -- CAM6
    baseroot="/path/to/this/directory" #replace path
    basecasename6="CAM6_MODNAME"
    res = "f09_g16"
    compset= "FHIST"
    user_mods_dir="/path/to/this/directory/Source_Mod_Files" #replace path
    overwrite = True
    caseroot = build_base_case(baseroot, basecasename6, res,
                            compset, overwrite, user_mods_dir,psuedo_obs_dir,project="P54048000",inc_int=inc_int) #replace path /project code
    
    #to do! 
    #replace all of the file paths in the "Fake_DA.py" path and write it to this directory. 
    
    shutil.copy2(baseroot+'/Fake_DA.py', '/path/to/scratch/directory/CAM6_MODNAME/run/')
    shutil.copy2(baseroot+'/Fake_DA_CAM5.py', '/path/to/scratch/directory/CAM5_MODNAME/run/')

    

if __name__ == "__main__":
    _main_func(__doc__)
