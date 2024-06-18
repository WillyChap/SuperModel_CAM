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
import filecmp
from cdo import *
from scipy.interpolate import CubicSpline
import Ngl

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

def are_files_identical(file1_path, file2_path): #WEC-v2
    with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:

        content1 = file1.read()
        content2 = file2.read()
        if len(content1) == len(content2):
            time_cam5 = content1.split('.')[-2]
            time_cam6 = content2.split('.')[-2]
            print('same time: ',time_cam5,time_cam6)
        else:
            time_cam5 = 1
            time_cam6 = 2
            print('file not complete')
        #time_cam5 = content1.split('.')[-2]
        #time_cam6 = content2.split('.')[-2]
        #print('same time: ',time_cam5,time_cam6)

    return time_cam5 == time_cam6
    #return content1 == content2

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
    max_attempts = 3000
    attempts = 0
    
    print('searching for 1: ', file1_path)
    print('searching for 2: ', file2_path)

    while attempts < max_attempts:
        if os.path.exists(file1_path) and os.path.exists(file2_path) and are_files_identical(file1_path, file2_path):
            time.sleep(1) 
            print(f"Both files '{file1_path}' and '{file2_path}' exist!")
            return True
        attempts += 1
        time.sleep(2)  # Wait for 5 seconds

    raise MaxAttemptsExceeded("Maximum number of attempts reached. Files not found.... it must have crashed, try restarting.")
    sys.exit(1)
    return False

def average_two_files(ps_fp,file1,file2,file3,file4,file5,file6,file7,file8,inc_str): #WEC-v2
    
    DS_f1 = xr.open_dataset(file1)
    DS_f2 = xr.open_dataset(file2)
    DS_f3 = xr.open_dataset(file3)
    DS_f4 = xr.open_dataset(file4)
    DS_f5 = xr.open_dataset(file5)
    DS_f6 = xr.open_dataset(file6)
    DS_f7 = xr.open_dataset(file7)
    DS_f8 = xr.open_dataset(file8)
    
    DS_template = xr.open_dataset(ps_fp+'/Template_Nudging_File.nc',decode_times=False)
    
    DS_template['U'][:] =  ((DS_f1['U'] + DS_f2['U'])/2).values.squeeze()
    DS_template['V'][:] =  ((DS_f3['V'] + DS_f4['V'])/2).values.squeeze()
    DS_template['T'][:] =  ((DS_f5['T'] + DS_f6['T'])/2).values
    DS_template['Q'][:] =  ((DS_f7['Q'] + DS_f8['Q'])/2).values
    DS_template['PS'][:] =  ((DS_template['PS'] + DS_template['PS'])/2).values
 
    fout = ps_fp+'/test_pseudoobs_UVT.h1.'+inc_str+'.nc'
    DS_template.to_netcdf(fout,format="NETCDF3_CLASSIC",mode='w')
   
    return fout 

def write_to_pseudoobs(ps_fp_cam5,ps_fp_cam6,file1,file2,file3,file4,file5,file6,inc_str): #WEC-v2

    DS_f1 = xr.open_dataset(file1)
    DS_f2 = xr.open_dataset(file2)
    DS_f3 = xr.open_dataset(file3)
    DS_f4 = xr.open_dataset(file4)
    DS_f5 = xr.open_dataset(file5)
    DS_f6 = xr.open_dataset(file6)

    DS_template_cam5 = xr.open_dataset(ps_fp_cam5+'/Template_Nudging_File_CAM5.nc',decode_times=False)

    DS_template_cam5['U'][:] =  (DS_f1['U']).values.squeeze()
    DS_template_cam5['V'][:] =  (DS_f3['V']).values.squeeze()
    DS_template_cam5['T'][:] =  (DS_f5['T']).values

    fout_cam5 = ps_fp_cam5+'/test_pseudoobs_UVT.h1.'+inc_str+'.nc'
    DS_template_cam5.to_netcdf(fout_cam5,format="NETCDF3_CLASSIC",mode='w')
    
    DS_template_cam6 = xr.open_dataset(ps_fp_cam6+'/Template_Nudging_File_CAM6.nc',decode_times=False)

    DS_template_cam6['U'][:] =  (DS_f2['U']).values.squeeze()
    DS_template_cam6['V'][:] =  (DS_f4['V']).values.squeeze()
    DS_template_cam6['T'][:] =  (DS_f6['T']).values
    fout_cam6 = ps_fp_cam6+'/test_pseudoobs_UVT.h1.'+inc_str+'.nc'
    DS_template_cam6.to_netcdf(fout_cam6,format="NETCDF3_CLASSIC",mode='w')

    return fout_cam6

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


def nudge_to_6hr_earlier(psuedo_obs_dir):

    #Get the latest file in the pseudo obs directory
    list_of_files = glob.glob(psuedo_obs_dir+'/test_pseudoobs_UVT*.nc')
    latest_file = max(list_of_files, key=os.path.getctime)

    latest_file_tim = latest_file.split('.')[-2]

    # Copy latest file to dummy file 6 hours backwards in time
    print('Copy latest file to dummy 6 hours before: ', latest_file)
    shutil.copy(latest_file,'Data_6hr_before_dum.nc') #copy files
    time.sleep(2) #to make sure all has been copied
    # Copy file 6 hours before to current time
    if latest_file_tim != '1979-01-01-21600':
        shutil.copy('Data_6hr_before.nc',latest_file) #copy files
        time.sleep(2) #to make sure all has been copied
    # Copy dummy file to non dummy file
    shutil.copy('Data_6hr_before_dum.nc','Data_6hr_before.nc') #copy files    

    time.sleep(2) #to make sure all has been copied



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

def hor_ip_modtocom(file1,file2,file3,file4,file5,file6,file7,file8):
    cdo = Cdo()

    cdo.setgrid('grid_CAM5.txt', input = file1, output = 'CAM5_U_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_CAM6.txt', input = file2, output = 'CAM6_U_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_CAM5.txt', input = file3, output = 'CAM5_V_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_CAM6.txt', input = file4, output = 'CAM6_V_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_CAM5.txt', input = file5, output = 'CAM5_T_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_CAM6.txt', input = file6, output = 'CAM6_T_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_CAM5.txt', input = file7, output = 'CAM5_PS_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_CAM6.txt', input = file8, output = 'CAM6_PS_with_latlon.nc', options = '-f nc')

    cdo.remapbic('grid_ERA5.txt', input = 'CAM5_U_with_latlon.nc', output = 'Cam5_U_hor.nc')
    cdo.remapbic('grid_ERA5.txt', input = 'CAM6_U_with_latlon.nc', output = 'Cam6_U_hor.nc')
    cdo.remapbic('grid_ERA5.txt', input = 'CAM5_V_with_latlon.nc', output = 'Cam5_V_hor.nc')
    cdo.remapbic('grid_ERA5.txt', input = 'CAM6_V_with_latlon.nc', output = 'Cam6_V_hor.nc')
    cdo.remapbic('grid_ERA5.txt', input = 'CAM5_T_with_latlon.nc', output = 'Cam5_T_hor.nc')
    cdo.remapbic('grid_ERA5.txt', input = 'CAM6_T_with_latlon.nc', output = 'Cam6_T_hor.nc')
    cdo.remapbic('grid_ERA5.txt', input = 'CAM5_PS_with_latlon.nc', output = 'Cam5_PS_hor.nc')
    cdo.remapbic('grid_ERA5.txt', input = 'CAM6_PS_with_latlon.nc', output = 'Cam6_PS_hor.nc')

    fout = 'Cam6_T_hor.nc'
    return fout

def vert_ip_average(file1,file2,file3,file4,file5,file6,file7,file8):

    DS_U_cam5 = xr.open_dataset(file1)
    DS_U_cam6 = xr.open_dataset(file2)
    DS_V_cam5 = xr.open_dataset(file3)
    DS_V_cam6 = xr.open_dataset(file4)
    DS_T_cam5 = xr.open_dataset(file5)
    DS_T_cam6 = xr.open_dataset(file6)
    DS_PS_cam5 = xr.open_dataset(file7)
    DS_PS_cam6 = xr.open_dataset(file8)

    U_cam5 = DS_U_cam5['U'][:]
    U_cam6 = DS_U_cam6['U'][:]
    V_cam5 = DS_V_cam5['V'][:]
    V_cam6 = DS_V_cam6['V'][:]
    T_cam5 = DS_T_cam5['T'][:]
    T_cam6 = DS_T_cam6['T'][:]
    PS_cam5 = DS_PS_cam5['PS'][:]
    PS_cam6 = DS_PS_cam6['PS'][:]

    lat_cam5 = DS_U_cam5['latitude'][:]
    lon_cam5 = DS_U_cam5['longitude'][:]
    lat_cam6 = DS_U_cam6['latitude'][:]
    lon_cam6 = DS_U_cam6['longitude'][:]

    lev_CAM5 = np.array([ 3.54463800000001, 7.38881350000001, 13.967214, 23.944625, 
    37.2302900000001, 53.1146050000002, 70.0591500000003, 85.4391150000003, 
    100.514695, 118.250335, 139.115395, 163.66207, 192.539935, 226.513265, 
    266.481155, 313.501265000001, 368.817980000002, 433.895225000001, 
    510.455255000002, 600.524200000003, 696.796290000003, 787.702060000003, 
    867.160760000001, 929.648875000002, 970.554830000001, 992.5561])

    lev_CAM6 = np.array([  3.64346569,   7.59481965,  14.35663225,  24.61222   ,
        35.92325002,  43.19375008,  51.67749897,  61.52049825,
        73.75095785,  87.82123029, 103.31712663, 121.54724076,
       142.99403876, 168.22507977, 197.9080867 , 232.82861896,
       273.91081676, 322.24190235, 379.10090387, 445.9925741 ,
       524.68717471, 609.77869481, 691.38943031, 763.40448111,
       820.85836865, 859.53476653, 887.02024892, 912.64454694,
       936.19839847, 957.48547954, 976.32540739, 992.55609512])

    lev_ERA = np.array([1.000000e-01, 2.921000e-01, 5.104000e-01, 7.964000e-01, 1.150600e+00,
	 1.575300e+00, 2.076800e+00, 2.666400e+00, 3.362300e+00, 4.193000e+00,
	 5.201300e+00, 6.444300e+00, 7.984400e+00, 9.892500e+00, 1.225650e+01,
	 1.518560e+01, 1.881460e+01, 2.331080e+01, 2.888160e+01, 3.578360e+01,
	 4.433500e+01, 5.462360e+01, 6.662330e+01, 8.039680e+01, 9.597810e+01,
	 1.134212e+02, 1.327577e+02, 1.539952e+02, 1.771176e+02, 2.020859e+02,
 	 2.288387e+02, 2.573558e+02, 2.876384e+02, 3.196307e+02, 3.532256e+02,
	 3.882700e+02, 4.245707e+02, 4.618997e+02, 5.000000e+02, 5.385913e+02,
	 5.773754e+02, 6.160417e+02, 6.542731e+02, 6.917515e+02, 7.281631e+02,
	 7.632045e+02, 7.965878e+02, 8.280469e+02, 8.573419e+02, 8.842661e+02,
	 9.086506e+02, 9.303702e+02, 9.493494e+02, 9.655672e+02, 9.790633e+02,
	 9.899435e+02, 9.983854e+02, 1.004644e+03, 1.009056e+03, 1.012049e+03])

    hyam_CAM6 = np.array([0.00364346569404006, 0.00759481964632869, 0.0143566322512925, 
   	 0.0246122200042009, 0.0359232500195503, 0.0431937500834465, 
   	 0.0516774989664555, 0.0615204982459545, 0.0737509578466415, 
   	 0.0878212302923203, 0.103317126631737, 0.121547240763903, 
         0.142994038760662, 0.168225079774857, 0.178230673074722, 
         0.170324325561523, 0.161022908985615, 0.150080285966396, 
   	 0.137206859886646, 0.122061938047409, 0.104244712740183, 
   	 0.0849791541695595, 0.0665016956627369, 0.0501967892050743, 
   	 0.037188658490777, 0.028431948274374, 0.0222089774906635, 
   	 0.016407382208854, 0.0110745579004288, 0.00625495356507599, 
   	 0.00198940909467638, 0] )

    hybm_CAM6 = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0196774136275053, 
   	 0.062504293397069, 0.112887907773256, 0.172161616384983, 
   	 0.241894043982029, 0.323930636048317, 0.420442461967468, 
   	 0.524799540638924, 0.624887734651566, 0.713207691907883, 
   	 0.783669710159302, 0.831102818250656, 0.864811271429062, 
   	 0.896237164735794, 0.92512384057045, 0.951230525970459, 
   	 0.974335998296738, 0.992556095123291 ]) 

    hyam_CAM5 = np.array([0.00354463800000001, 0.00738881350000001, 0.013967214, 0.023944625, 
   	 0.0372302900000001, 0.0531146050000002, 0.0700591500000003, 
   	 0.0779125700000003, 0.0766070100000003, 0.0750710850000003, 
   	 0.0732641500000002, 0.071138385, 0.0686375349999999, 0.065695415, 
   	 0.0622341550000001, 0.0581621650000002, 0.0533716800000001, 
   	 0.0477359250000001, 0.041105755, 0.0333057, 0.02496844, 0.01709591, 
   	 0.01021471, 0.00480317500000001, 0.00126068, 0 ])

    hybm_CAM5 = np.array([0, 0, 0, 0, 0, 0, 0, 0.00752654500000002, 0.023907685, 0.04317925, 
   	 0.0658512450000003, 0.0925236850000004, 0.1239024, 0.16081785, 0.204247, 
   	 0.2553391, 0.315446300000001, 0.386159300000001, 0.469349500000002, 
   	 0.567218500000003, 0.671827850000003, 0.770606150000003, 
   	 0.856946050000001, 0.924845700000002, 0.969294150000001, 0.9925561 ])
    U_cam5_array = np.array(U_cam5)
    U_cam6_array = np.array(U_cam6)
    V_cam5_array = np.array(V_cam5)
    V_cam6_array = np.array(V_cam6)
    T_cam5_array = np.array(T_cam5)
    T_cam6_array = np.array(T_cam6)
#
    P_cam5 = np.zeros(shape=(26,241,480))
    U_cam5_ERA = np.zeros(shape=(26,241,480))
    U_cam6_ERA = np.zeros(shape=(26,241,480))
    V_cam5_ERA = np.zeros(shape=(26,241,480))
    V_cam6_ERA = np.zeros(shape=(26,241,480))
    T_cam5_ERA = np.zeros(shape=(26,241,480))
    T_cam6_ERA = np.zeros(shape=(26,241,480))
    P_cam6 = np.zeros(shape=(32,241,480))

#   Use same PS for calculating P_cam5 and P_cam6
    for lev in np.arange(0,26):
    	P_cam5[lev,:,:] = 1000. * hyam_CAM5[lev] + PS_cam6[:,:]*0.01 * hybm_CAM5[lev]
    for lev in np.arange(0,32):
    	P_cam6[lev,:,:] = 1000. * hyam_CAM6[lev] + PS_cam6[:,:]*0.01 * hybm_CAM6[lev]


    U_cam5_ERA = U_cam5_array
    V_cam5_ERA = V_cam5_array
    T_cam5_ERA = T_cam5_array

#   Use CAM5 as common vertical levels
    for lat in np.arange(0,241):
        for lon in np.arange(0,480):
            U_cam6_ERA[:,lat,lon] = Ngl.ftcurv(P_cam6[:,lat,lon],U_cam6_array[:,lat,lon],P_cam5[:,lat,lon])
            V_cam6_ERA[:,lat,lon] = Ngl.ftcurv(P_cam6[:,lat,lon],V_cam6_array[:,lat,lon],P_cam5[:,lat,lon])
            T_cam6_ERA[:,lat,lon] = Ngl.ftcurv(P_cam6[:,lat,lon],T_cam6_array[:,lat,lon],P_cam5[:,lat,lon])
    
    U_ave = np.zeros(shape=(26,241,480))
    V_ave = np.zeros(shape=(26,241,480))
    T_ave = np.zeros(shape=(26,241,480))
    U_ave = ((0.5 * U_cam5_ERA + 0.5 * U_cam6_ERA))
    V_ave = ((0.5 * V_cam5_ERA + 0.5 * V_cam6_ERA))
    T_ave = ((0.5 * T_cam5_ERA + 0.5 * T_cam6_ERA))


    U_cam5_array = U_ave
    V_cam5_array = V_ave
    T_cam5_array = T_ave
    


    for lat in np.arange(0,241):
        for lon in np.arange(0,480):
            U_cam6_array[:,lat,lon] = Ngl.ftcurv(P_cam5[:,lat,lon],U_ave[:,lat,lon],P_cam6[:,lat,lon])
            V_cam6_array[:,lat,lon] = Ngl.ftcurv(P_cam5[:,lat,lon],V_ave[:,lat,lon],P_cam6[:,lat,lon])
            T_cam6_array[:,lat,lon] = Ngl.ftcurv(P_cam5[:,lat,lon],T_ave[:,lat,lon],P_cam6[:,lat,lon])


    #Write to file
    filename_U_cam5 = 'Cam5_U_ver.nc'
    filename_U_cam6 = 'Cam6_U_ver.nc'
    filename_V_cam5 = 'Cam5_V_ver.nc'
    filename_V_cam6 = 'Cam6_V_ver.nc'
    filename_T_cam5 = 'Cam5_T_ver.nc'
    filename_T_cam6 = 'Cam6_T_ver.nc'

    data_U_cam5 = xr.DataArray(U_cam5_array, coords={'lev': lev_CAM5,'latitude': lat_cam5,'longitude': lon_cam5}, dims=["lev", "latitude", "longitude"])
    data_U_cam6 = xr.DataArray(U_cam6_array, coords={'lev': lev_CAM6,'latitude': lat_cam6,'longitude': lon_cam6}, dims=["lev", "latitude", "longitude"])
    data_V_cam5 = xr.DataArray(V_cam5_array, coords={'lev': lev_CAM5,'latitude': lat_cam5,'longitude': lon_cam5}, dims=["lev", "latitude", "longitude"])
    data_V_cam6 = xr.DataArray(V_cam6_array, coords={'lev': lev_CAM6,'latitude': lat_cam6,'longitude': lon_cam6}, dims=["lev", "latitude", "longitude"])
    data_T_cam5 = xr.DataArray(T_cam5_array, coords={'lev': lev_CAM5,'latitude': lat_cam5,'longitude': lon_cam5}, dims=["lev", "latitude", "longitude"])
    data_T_cam6 = xr.DataArray(T_cam6_array, coords={'lev': lev_CAM6,'latitude': lat_cam6,'longitude': lon_cam6}, dims=["lev", "latitude", "longitude"])
    
    data_U_cam5 = data_U_cam5.rename("U")
    data_U_cam6 = data_U_cam6.rename("U")
    data_V_cam5 = data_V_cam5.rename("V")
    data_V_cam6 = data_V_cam6.rename("V")
    data_T_cam5 = data_T_cam5.rename("T")
    data_T_cam6 = data_T_cam6.rename("T")


    data_U_cam5.to_netcdf(path=filename_U_cam5)
    data_U_cam6.to_netcdf(path=filename_U_cam6)
    data_V_cam5.to_netcdf(path=filename_V_cam5)
    data_V_cam6.to_netcdf(path=filename_V_cam6)
    data_T_cam5.to_netcdf(path=filename_T_cam5)
    data_T_cam6.to_netcdf(path=filename_T_cam6)


    fout = 'Cam6_T_ver.nc'
    return fout
        
def hor_ip_comtomod(file1,file2,file3,file4,file5,file6):

    cdo = Cdo()

    cdo.setgrid('grid_ERA5.txt', input = file1, output = 'CAM5_U_ERA_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_ERA5.txt', input = file2, output = 'CAM6_U_ERA_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_ERA5.txt', input = file3, output = 'CAM5_V_ERA_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_ERA5.txt', input = file4, output = 'CAM6_V_ERA_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_ERA5.txt', input = file5, output = 'CAM5_T_ERA_with_latlon.nc', options = '-f nc')
    cdo.setgrid('grid_ERA5.txt', input = file6, output = 'CAM6_T_ERA_with_latlon.nc', options = '-f nc')
    
    cdo.remapbic('grid_CAM5.txt', input = 'CAM5_U_ERA_with_latlon.nc', output = 'Cam5_U_ip.nc')
    cdo.remapbic('grid_CAM6.txt', input = 'CAM6_U_ERA_with_latlon.nc', output = 'Cam6_U_ip.nc')
    cdo.remapbic('grid_CAM5.txt', input = 'CAM5_V_ERA_with_latlon.nc', output = 'Cam5_V_ip.nc')
    cdo.remapbic('grid_CAM6.txt', input = 'CAM6_V_ERA_with_latlon.nc', output = 'Cam6_V_ip.nc')
    cdo.remapbic('grid_CAM5.txt', input = 'CAM5_T_ERA_with_latlon.nc', output = 'Cam5_T_ip.nc')
    cdo.remapbic('grid_CAM6.txt', input = 'CAM6_T_ERA_with_latlon.nc', output = 'Cam6_T_ip.nc')

    #cdo.remap('grid_CAM5.txt'+","+'weights_ERAtoCAM5.nc', input = 'CAM5_U_ERA_with_latlon.nc', output = 'Cam5_U_ip.nc')

    fout = 'Cam6_T_ip.nc'
    return fout


def _main_func(description):
    
    inc_int = 6
    store_combined_path = '/path/to/scratch/directory/store_super_cam5_cam6/'
    psuedo_obs_dir_cam5 = '/path/to/scratch/directory/../pseudoobs/pseudoobs_CAM5_MODNAME/'
    psuedo_obs_dir_cam6 = '/path/to/scratch/directory/../pseudoobs/pseudoobs_CAM6_MODNAME/'

    ###################################
    #cam5 block
    ###################################
    
    """
    This block is used to read the current_time_file 
    and the increment the file by X hours (defined as variable inc_int).
    It then defines a CAM restart file to wait to arrive
    """
    
    curr_time_cam5_str = '/path/to/scratch/directory/CAM5_MODNAME/run/curr_time_file_CAM5.txt' #WEC-v2
    curr_time_cam6_str = '/path/to/scratch/directory/CAM6_MODNAME/run/curr_time_file_CAM6.txt' #WEC-v2
    Pause_init_file = '/path/to/scratch/directory/CAM6_MODNAME/run/PAUSE_INIT' #WEC-v2
    run_dir_path_cam5 = '/path/to/scratch/directory/CAM5_MODNAME/run/'
    run_dir_path_cam6 = '/path/to/scratch/directory/CAM6_MODNAME/run/'
    
    if os.path.exists(Pause_init_file):
        print("Path exists. Exiting the program.")
        os.remove(Pause_init_file)
        os.remove(run_dir_path_cam6 + 'Cam6_dumpV.nc')
        os.remove(run_dir_path_cam6 + 'Cam6_dumpU.nc')
        os.remove(run_dir_path_cam6 + 'Cam6_dumpT.nc')
        os.remove(run_dir_path_cam6 + 'Cam6_dumpQ.nc')
        os.remove(curr_time_cam6_str)
        os.remove('/path/to/scratch/directory/CAM6_MODNAME/run/PAUSE')
        sys.exit(0)  # Exit with a success status code
    else:
        print("Path does not exist. Continuing with the program.")
        
    #wait for the files to arrive... raise exception if they don't. #WEC-v2 .... this needs to be moved up before reading the curr_time_file_XXX.txt files...
    print('....searching for files....')    
    try:
        found = wait_for_files(curr_time_cam5_str,curr_time_cam6_str)
        print(found)
    except MaxAttemptsExceeded as e:
        print(e)
        sys.exit(1)
    
    if not are_files_identical(curr_time_cam5_str,curr_time_cam6_str):
        print('FILES ARE NOT IDENTICAL BROKEN BROKEN BROKEN!!!!!!!!!')
    else:
        print('The TWO RUNS ARE IN THE SAME TEMPORAL SPOT')
    
    with open(curr_time_cam5_str, 'r') as file:
        data = file.read().replace('\n', '')
    print('current time file cam5:',data)
    curr_time_cam5 = data.split('.')[-2]
    
    #this is our increment time.
    inc_str_cam5 = inc_hours(curr_time_cam5,inc_int)
    
    #we are waiting for this file!! 
    rpoint_wait_cam5 = run_dir_path_cam5 + 'CAM5_MODNAME.cam.h1.'+inc_str_cam5+'.nc'
    
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

    with open(curr_time_cam6_str, 'r') as file:
        data = file.read().replace('\n', '')
    print('current time file cam6:',data)
    curr_time_cam6 = data.split('.')[-2]
    
    #this is our increment time.
    inc_str_cam6 = inc_hours(curr_time_cam6,inc_int)
    
    #we are waiting for this file!! 
    rpoint_wait_cam6 = run_dir_path_cam6 + 'CAM6_MODNAME.cam.h1.'+inc_str_cam6+'.nc'
    
    
    ###################################
    ###################################

    """
    If the files are found.. continue on...
    """  
        
    if found:
        
        #get h1 files:
        h1_cam5 = rpoint_wait_cam5.replace(".cam.h1.",".cam.h1.")
        h1_cam6 = rpoint_wait_cam6.replace(".cam.h1.",".cam.h1.")
        
        Tcam6 = run_dir_path_cam6 + 'Cam6_dumpT.nc'#WEC-v2
        Tcam5 = run_dir_path_cam5 + 'Cam5_dumpT.nc'#WEC-v2
        Ucam6 = run_dir_path_cam6 + 'Cam6_dumpU.nc'#WEC-v2
        Ucam5 = run_dir_path_cam5 + 'Cam5_dumpU.nc'#WEC-v2
        Vcam6 = run_dir_path_cam6 + 'Cam6_dumpV.nc'#WEC-v2
        Vcam5 = run_dir_path_cam5 + 'Cam5_dumpV.nc'#WEC-v2
        Qcam6 = run_dir_path_cam6 + 'Cam6_dumpQ.nc'#WEC-v2
        Qcam5 = run_dir_path_cam5 + 'Cam5_dumpQ.nc'#WEC-v2
        PScam6 = run_dir_path_cam6 + 'Cam6_dumpPS.nc'#WEC-v2
        PScam5 = run_dir_path_cam5 + 'Cam5_dumpPS.nc'#WEC-v2
       

        Tcam6_hor = 'Cam6_T_hor.nc'
        Tcam5_hor = 'Cam5_T_hor.nc'
        Ucam6_hor = 'Cam6_U_hor.nc'
        Ucam5_hor = 'Cam5_U_hor.nc'
        Vcam6_hor = 'Cam6_V_hor.nc'
        Vcam5_hor = 'Cam5_V_hor.nc'
        PScam6_hor = 'Cam6_PS_hor.nc'
        PScam5_hor = 'Cam5_PS_hor.nc'

        Tcam6_ver = 'Cam6_T_ver.nc'
        Tcam5_ver = 'Cam5_T_ver.nc'
        Ucam6_ver = 'Cam6_U_ver.nc'
        Ucam5_ver = 'Cam5_U_ver.nc'
        Vcam6_ver = 'Cam6_V_ver.nc'
        Vcam5_ver = 'Cam5_V_ver.nc'
        
        Tcam6_ip = 'Cam6_T_ip.nc'
        Tcam5_ip = 'Cam5_T_ip.nc'
        Ucam6_ip = 'Cam6_U_ip.nc'
        Ucam5_ip = 'Cam5_U_ip.nc'
        Vcam6_ip = 'Cam6_V_ip.nc'
        Vcam5_ip = 'Cam5_V_ip.nc'
 
        print('h1_file5: ',Tcam5)#WEC-v2
        print('h1_file6: ',Tcam6)#WEC-v2
        print('inc_str_cam6: ',inc_str_cam6)#WEC-v2
        print('inc_str_cam5: ',inc_str_cam5) #WEC-v2
      

        hip = hor_ip_modtocom(Ucam5,Ucam6,Vcam5,Vcam6,Tcam5,Tcam6,PScam5,PScam6)
        vip = vert_ip_average(Ucam5_hor,Ucam6_hor,Vcam5_hor,Vcam6_hor,Tcam5_hor,Tcam6_hor,PScam5_hor,PScam6_hor)
        vhip = hor_ip_comtomod(Ucam5_ver,Ucam6_ver,Vcam5_ver,Vcam6_ver,Tcam5_ver,Tcam6_ver)

        cc = write_to_pseudoobs(psuedo_obs_dir_cam5, psuedo_obs_dir_cam6,Ucam5_ip,Ucam6_ip,Vcam5_ip,Vcam6_ip,Tcam5_ip,Tcam6_ip,curr_time_cam6)
  
        #bb = average_two_files(psuedo_obs_dir,Ucam5,Ucam6,Vcam5,Vcam6,Tcam5,Tcam6,Qcam5,Qcam6,curr_time_cam6) #WEC-v2
        #print(bb)
        the_goods_are_good = check_nudging_file(psuedo_obs_dir_cam6,h1_cam5,h1_cam6,curr_time_cam6) #check the nudging file for errors #WEC-v2
        count_avg=0
        
        while count_avg < 50 and not the_goods_are_good:
            print('had to remake the average nudging file'+str(count_avg))
            time.sleep(1) 
            #bb = average_two_files(psuedo_obs_dir,Ucam5,Ucam6,Vcam5,Vcam6,Tcam5,Tcam6,Qcam5,Qcam6,curr_time_cam6) #WEC-v2
            the_goods_are_good = check_nudging_file(psuedo_obs_dir_cam6,h1_cam5,h1_cam6,curr_time_cam6) #check the nudging file for errors #WEC-v2
            count_avg+=1

	#Here we are going to nudge to 6hr before, pay attention!!
	#nudge_to_6hr_earlier(psuedo_obs_dir)
       
        #nudge_to_6hr_earlier(psuedo_obs_dir) #needs testing.
        add_dummy_path(psuedo_obs_dir_cam6,inc_int) #needs testing.
        #archive_old_files(psuedo_obs_dir,store_combined_path)
        #print(update_current_time(curr_time_cam6_str,inc_str_cam6))#WEC-v2
        #print(update_current_time(curr_time_cam5_str,inc_str_cam5))#WEC-v2
        print('To Do:')
        print('3) remove the dummy path in change the current_time_file.txt')
        print('4) add dummy time to the pseudo obs folder')
        print('5) stage the source mod files for build... MAYBE DONE..TEST')
        time.sleep(1) 
        os.remove('/path/to/scratch/directory/CAM6_MODNAME/run/PAUSE')
    
    return True


if __name__ == "__main__":
    _main_func(__doc__)
