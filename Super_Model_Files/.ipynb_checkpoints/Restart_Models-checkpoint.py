#!/usr/bin/env python

import glob
import os
import pandas as pd
import datetime
import shutil

scratch_path = '/path/to/scratch/directory/' #replace path
psuedo_obs_dir='/path/to/work/directory/pseudoobs_V2' #replace path
archive_dir = '/path/to/scratch/directory/store_super_cam5_cam6' #replace path
cam5_path = scratch_path+'/CAM5_MODNAME/run/' #replace path
cam6_path = scratch_path+'/CAM6_MODNAME/run/'#replace path


def get_time(fn):
    timstr = fn.split('.')[-2]
    dt_is = pd.to_datetime(timstr[0:-6]+' '+str(datetime.timedelta(seconds=float(timstr[-5:]))))
    
    return timstr, dt_is

def remove_files_greater(path_rem,date_str):
    
    dt_twant = pd.to_datetime(date_str[0:-6]+' '+str(datetime.timedelta(seconds=float(date_str[-5:]))))
    fns = sorted(glob.glob(cam5_path+'/*.nc'))
    
    for ff in fns:
        try:
            tmstr,dt_is = get_time(ff)
            if dt_twant<dt_is:
                print('removing file cause its greater time: ',ff)
                os.remove(ff)
        except: 
            print('could not remove: ',ff)
    return dt_twant

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
                    shutil.move(fn,store_combined_path+'/'+os.path.basename(fn))
                else:
                    os.remove(fn)

        except ValueError:
            print('file name is: ',fn)
            print('NC file in the work directory cannot be moved')

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

    for dat_path in sorted(glob.glob(cam5_path+'/rpointer*')):
        with open(dat_path, 'r') as file:
            data = file.read().replace('\n', '')
        rpoint_dat_cam5 = data.split('.')[-2]
    print(rpoint_dat_cam5)

    cam5_rpoint = pd.to_datetime(rpoint_dat_cam5[:10]+' '+str(datetime.timedelta(seconds=float(rpoint_dat_cam5[-5:]))))

    for dat_path in sorted(glob.glob(cam6_path+'/rpointer*')):
        with open(dat_path, 'r') as file:
            data = file.read().replace('\n', '')
        rpoint_dat_cam6 = data.split('.')[-2]

    cam6_rpoint = pd.to_datetime(rpoint_dat_cam6[:10]+' '+str(datetime.timedelta(seconds=float(rpoint_dat_cam6[-5:]))))
    print('cam5 rpoiner: ',cam5_rpoint)
    print('cam6 rpoiner: ',cam6_rpoint)

    #logical to see what is smaller. 
    if cam5_rpoint <= cam6_rpoint:
        cam_replace = cam5_rpoint
    else:
        cam_replace = cam6_rpoint

    # Extract the time component from the incremented timestamp
    ts = str(cam_replace)[-8:]
    # Convert the time component from HH:MM:SS to seconds
    secs = sum(int(x) * 60 ** i for i, x in enumerate(reversed(ts.split(':')))) #change seconds to HH:MM:SS 

    cam_replace_str = str(cam_replace)[:10]+'-'+f'{secs:05}'

    for dat_path in sorted(glob.glob(cam5_path+'/rpointer*')):
        with open(dat_path, 'r') as file:
            data = file.read()
            data = data.replace(rpoint_dat_cam5, cam_replace_str)

        with open(dat_path, 'w') as file:
            # Writing the replaced data in our
            # text file
            file.write(data)
    # Printing Text replaced
    print("Text replaced cam5")

    for dat_path in sorted(glob.glob(cam6_path+'/rpointer*')):
        with open(dat_path, 'r') as file:
            data = file.read()
            data = data.replace(rpoint_dat_cam6, cam_replace_str)

        with open(dat_path, 'w') as file:
            # Writing the replaced data in our
            # text file
            file.write(data)
    # Printing Text replaced
    print("Text replaced cam6")

    #archive files: 
    archive_old_files(psuedo_obs_dir,archive_dir)
    #replace current step
    update_current_time(cam5_path+'/current_time_file.txt',cam_replace_str)
    update_current_time(cam6_path+'/current_time_file.txt',cam_replace_str)
    
    #remove old files: 
    remove_files_greater(cam5_path,cam_replace_str)
    remove_files_greater(cam6_path,cam_replace_str)
    
    return True 

if __name__ == "__main__":
    _main_func(__doc__)

