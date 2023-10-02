#!/usr/bin/env python

# ## also make sure to chmod +x this_script.py

import os, sys
import pandas as pd
import datetime
import shutil
import time
import glob
import xarray as xr
import numpy as np

# to_do:
# - make a "current_time" file in the run directories.
# - make a HARD reset file ... which brings everything back to 1979
# - - Remove *.bin and *.nc from both /scratch/mod/run/ directories
# - - set CONTINUE_RUN=FALSE
# - - reset current_time.txt in both /scratch/mod/run/ directories
# - - remove files *.nc from pseudoobs_V2 

#Probably smart to do: 
# create a new pseudoobs_dir with each new git instance named after the models.


class MaxAttemptsExceeded(Exception):
    pass

def inc_hours(current_time,inc_amount):
    print('time in current file: ', current_time)
    
    increment_time = str(pd.to_datetime(current_time[0:-6]+' '+str(datetime.timedelta(seconds=float(current_time[-5:]))))+datetime.timedelta(hours=inc_amount))
    
    # Extract the time component from the incremented timestamp
    ts = str(increment_time)[-8:]

    # Convert the time component from HH:MM:SS to seconds
    secs = sum(int(x) * 60 ** i for i, x in enumerate(reversed(ts.split(':')))) #change seconds to HH:MM:SS 

    inc_time_string = str(increment_time)[:10]+'-'+f'{secs:05}'
    return inc_time_string 

def wait_for_files(file1_path, file2_path):
    max_attempts = 30
    attempts = 0
    
    print('searching for 1: ', file1_path)
    print('searching for 2: ', file2_path)

    while attempts < max_attempts:
        if os.path.exists(file1_path) and os.path.exists(file2_path):
            time.sleep(20) 
            print(f"Both files '{file1_path}' and '{file2_path}' exist!")
            return True
        attempts += 1
        time.sleep(15)  # Wait for 5 seconds

    raise MaxAttemptsExceeded("Maximum number of attempts reached. Files not found.... it must have crashed, try restarting.")
    sys.exit(1)
    return False

def average_two_files(ps_fp,file1,file2,inc_str):
    
    DS_f1 = xr.open_dataset(file1)
    DS_f2 = xr.open_dataset(file2)
    
    DS_template = xr.open_dataset(ps_fp+'/Template_Nudging_File.nc',decode_times=False)
    
    DS_template['U'][:] =  ((DS_f1['U'] + DS_f2['U'])/2).values.squeeze()
    DS_template['V'][:] =  ((DS_f1['V'] + DS_f2['V'])/2).values.squeeze()
    
    
    DS_template['T'][:] =  ((DS_f1['T'] + DS_f2['T'])/2).values
    DS_template['Q'][:] =  ((DS_f1['Q'] + DS_f2['Q'])/2).values
    DS_template['PS'][:] =  ((DS_f1['PS'] + DS_f2['PS'])/2).values
 
    fout = ps_fp+'/test_pseudoobs_UVT.h1.'+inc_str+'.nc'
    DS_template.to_netcdf(fout,format="NETCDF3_CLASSIC",mode='w')
   
    return fout 

def check_nudging_file(ps_fp,file1,file2,inc_str):
    
    lev_set = np.array([  3.64346569,   7.59481965,  14.35663225,  24.61222   ,
        35.92325002,  43.19375008,  51.67749897,  61.52049825,
        73.75095785,  87.82123029, 103.31712663, 121.54724076,
       142.99403876, 168.22507977, 197.9080867 , 232.82861896,
       273.91081676, 322.24190235, 379.10090387, 445.9925741 ,
       524.68717471, 609.77869481, 691.38943031, 763.40448111,
       820.85836865, 859.53476653, 887.02024892, 912.64454694,
       936.19839847, 957.48547954, 976.32540739, 992.55609512])
 
    fout = ps_fp+'test_pseudoobs_UVT.h1.'+inc_str+'.nc'
    
    DS = xr.open_dataset(fout,decode_times=False)
    lev_check = np.array(DS['lev'])
        
    close = np.allclose(lev_set, lev_check)
   
    return close 

def add_dummy_path(psuedo_obs_dir,inc_int):
    list_of_files = glob.glob(psuedo_obs_dir+'/test_pseudoobs_UVT*.nc') # get the latest file in the pseudo obs ...
    latest_file = max(list_of_files, key=os.path.getctime)
    
    latest_file_tim = latest_file.split('.')[-2]

    # Extract the relevant timestamp information from the latest file name
    # and calculate a new timestamp with an increment of XX hours
    increment_time_6h = inc_hours(latest_file_tim,inc_int)
    # Copy the latest file with a modified filename based on the incremented timestamp
    print('orig file to copy to dummy: ', latest_file)
    print('making dummy file: ', latest_file.split('.h1.')[0]+'.h1.'+increment_time_6h+'.nc')
    shutil.copy(latest_file,latest_file.split('.h1.')[0]+'.h1.'+increment_time_6h+'.nc') #copy files 
    
    increment_time_6h = inc_hours(increment_time_6h,inc_int)
    # Copy the latest file with a modified filename based on the incremented timestamp
    print('orig file to copy to dummy: ', latest_file)
    print('making dummy file: ', latest_file.split('.h1.')[0]+'.h1.'+increment_time_6h+'.nc')
    shutil.copy(latest_file,latest_file.split('.h1.')[0]+'.h1.'+increment_time_6h+'.nc') #copy files 


    

def archive_old_files(dir_search ,store_combined_path):
    
    dir_search=dir_search +'/test_pseudoobs_UVT*.nc'
    
    list_of_files = sorted(glob.glob(dir_search)) # get the latest file in the pseudo obs ...
    latest_file = max(list_of_files, key=os.path.getctime)
    print(latest_file)
    
    latest_file.split('.')[-2]

    #time stamp latest files
    ts_latest= pd.to_datetime(latest_file.split('.')[-2][0:-6]+' '+str(datetime.timedelta(seconds=float(latest_file.split('.')[-2][-5:]))))

    mv_dict={}
    for fn in sorted(glob.glob(dir_search)):
        try: 
            time_file = pd.to_datetime(fn.split('.')[-2][0:-6]+' '+str(datetime.timedelta(seconds=float(fn.split('.')[-2][-5:]))))
            mv_dict[time_file]=fn
            #move the file if they are four days older than the current time
            if time_file<(ts_latest - datetime.timedelta(days=3)):
                #save the combined states, discard the h1 files (they are repeated in the scract)
                if 'test_pseudoobs_UVT' in fn:
                    print('archiving file: ',fn)
                    if not os.path.exists(store_combined_path):
                        os.makedirs(store_combined_path)
                    shutil.move(fn,store_combined_path+os.path.basename(fn))
                else:
                    os.remove(fn)

        except ValueError:
            print('file name is: ',fn)
            print('NC file in the work directory cannot be moved')


def replace_string_in_file(input_file, output_file, search_string, replace_string):
    with open(input_file, 'r') as file_in, open(output_file, 'w') as file_out:
        for line in file_in:
            modified_line = line.replace(search_string, replace_string)
            file_out.write(modified_line)

def replace_string_in_file_overwrite(input_file, search_string, replace_string):
    with open(input_file, 'r+') as file:
        lines = file.readlines()
        file.seek(0)  # Move the file pointer to the beginning
        for line in lines:
            modified_line = line.replace(search_string, replace_string)
            file.write(modified_line)
        file.truncate()  # Truncate the remaining content (if any)

def update_current_time(curr_time_str,inc_str):
    
    with open(curr_time_str, 'r') as file:
        data = file.read().replace('\n', '')
    curr_time = data.split('.')[-2]
    
    #curr_time_str2 = curr_time_str.split('.txt')[0]+'_V2.txt'
    print('update ct: ',curr_time)
    print('update is: ',inc_str)
    replace_string_in_file_overwrite(curr_time_str,curr_time,inc_str)
    
    return curr_time,inc_str

def _main_func(description):
    
    inc_int = 6
    store_combined_path = '/path/to/scratch/directory/store_super_cam5_cam6/'
    psuedo_obs_dir = '/path/to/work/directory/pseudoobs_CAM5_MODNAME_CAM6_MODNAME/'

    ###################################
    #cam5 block
    ###################################
    
    """
    This block is used to read the current_time_file 
    and the increment the file by X hours (defined as variable inc_int).
    It then defines a CAM restart file to wait to arrive
    """
    
    Pause_init_file = '/path/to/scratch/directory/CAM6_MODNAME/run/PAUSE_INIT'
    
    if os.path.exists(Pause_init_file):
        print("Path exists. Exiting the program.")
        os.remove(Pause_init_file)
        #os.remove('/path/to/scratch/directory/CAM6_MODNAME/run/PAUSE')
        #sys.exit(0)  # Exit with a success status code
    else:
        print("Path does not exist. Continuing with the program.")

    
    
    curr_time_cam5_str = '/path/to/scratch/directory/CAM5_MODNAME/run/current_time_file.txt'
    run_dir_path_cam5 = '/path/to/scratch/directory/CAM5_MODNAME/run/'
    
    with open(curr_time_cam5_str, 'r') as file:
        data = file.read().replace('\n', '')
    print('current time file cam5:',data)
    curr_time_cam5 = data.split('.')[-2]
    
    #this is our increment time.
    inc_str_cam5 = inc_hours(curr_time_cam5,inc_int)
    
    #we are waiting for this file!! 
    rpoint_wait_cam5 = run_dir_path_cam5 + 'CAM5_MODNAME.cam.h1.'+inc_str_cam5+'.nc'
    
    for dat_path in sorted(glob.glob(run_dir_path_cam5+'/rpointer*')):
        with open(dat_path, 'r') as file:
            data = file.read().replace('\n', '')
        rpoint_in_run = data.split('.')[-2]
        
    print('cam5 rpointer.atm is currently at: ', rpoint_in_run)
    ###################################
    ###################################

    ###################################
    #cam6 block
    ###################################
    """
    This block is used to read the current_time_file 
    and the increment the file by X hours (defined as variable inc_int).
    It then defines a CAM restart file to wait to arrive
    """
    curr_time_cam6_str = '/path/to/scratch/directory/CAM6_MODNAME/run/current_time_file.txt'
    run_dir_path_cam6 = '/path/to/scratch/directory/CAM6_MODNAME/run/'

    
    with open(curr_time_cam6_str, 'r') as file:
        data = file.read().replace('\n', '')
    print('current time file cam6:',data)
    curr_time_cam6 = data.split('.')[-2]
    
    #this is our increment time.
    inc_str_cam6 = inc_hours(curr_time_cam6,inc_int)
    
    #we are waiting for this file!! 
    rpoint_wait_cam6 = run_dir_path_cam6 + 'CAM6_MODNAME.cam.h1.'+inc_str_cam6+'.nc'
    
    for dat_path in sorted(glob.glob(run_dir_path_cam6+'/rpointer*')):
        with open(dat_path, 'r') as file:
            data = file.read().replace('\n', '')
        rpoint_in_run = data.split('.')[-2]
    print('cam6 rpointer.atm is currently at: ', rpoint_in_run)
    
    ###################################
    ###################################
   
    #wait for the files to arrive... raise exception if they don't.
    print('....searching for files....')    
    try:
        found = wait_for_files(rpoint_wait_cam5,rpoint_wait_cam6)
        print(found)
    except MaxAttemptsExceeded as e:
        print(e)
        sys.exit(1)
        
        
    """
    If the files are found.. continue on...
    """  
        
    if found:
        
        #get h1 files:
        h1_cam5 = rpoint_wait_cam5.replace(".cam.h1.",".cam.h1.")
        h1_cam6 = rpoint_wait_cam6.replace(".cam.h1.",".cam.h1.")
        
        print('h1_file5: ',h1_cam5)
        print('h1_file6: ',h1_cam6)
        print('inc_str_cam6: ',inc_str_cam6)
        print('inc_str_cam5: ',inc_str_cam5)
        
        bb = average_two_files(psuedo_obs_dir,h1_cam5,h1_cam6,inc_str_cam6)
        print(bb)
        the_goods_are_good = check_nudging_file(psuedo_obs_dir,h1_cam5,h1_cam6,inc_str_cam6) #check the nudging file for errors
        count_avg=0
        
        while count_avg < 50 and not the_goods_are_good:
            print('had to remake the average nudging file'+str(count_avg))
            time.sleep(5) 
            bb = average_two_files(psuedo_obs_dir,h1_cam5,h1_cam6,inc_str_cam6)
            the_goods_are_good = check_nudging_file(psuedo_obs_dir,h1_cam5,h1_cam6,inc_str_cam6) #check the nudging file for errors
            count_avg+=1
       
        add_dummy_path(psuedo_obs_dir,inc_int) #needs testing.
        #archive_old_files(psuedo_obs_dir,store_combined_path)
        print(update_current_time(curr_time_cam6_str,inc_str_cam6))
        print(update_current_time(curr_time_cam5_str,inc_str_cam5))
        print('To Do:')
        print('3) remove the dummy path in change the current_time_file.txt')
        print('4) add dummy time to the pseudo obs folder')
        print('5) stage the source mod files for build... MAYBE DONE..TEST')
        time.sleep(5) 
        os.remove('/path/to/scratch/directory/CAM6_MODNAME/run/PAUSE')
    
    return True


if __name__ == "__main__":
    _main_func(__doc__)
