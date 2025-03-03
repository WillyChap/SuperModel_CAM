[![DOI](https://zenodo.org/badge/699459300.svg)](https://zenodo.org/doi/10.5281/zenodo.12577788)

# A NSF-NCAR CAM5/CAM6 SuperModel  

This repository provides instructions for running a **CESM2.1.5-based CAM5/CAM6 supermodel**, which couples two versions of CAM to exchange state information dynamically during simulation. The supermodel runs on **PBS-based HPC clusters** (e.g., NSF-NCAR Derecho, Betzy) and can be adapted to other systems with the necessary dependencies installed.

If you're unfamiliar with **supermodeling**, see [our paper](https://journals.ametsoc.org/view/journals/bams/aop/BAMS-D-22-0070.1/BAMS-D-22-0070.1.xml) for an introduction to the approach and its applications.

## NOTE:
If you are running on the NSF-NCAR Derecho Machine, you can skip steps to set up the casper env and the cesm2.1.5 installation. Comments in the setup.sh file will allow you to directly run on Derecho. 

---

## **System Requirements & Prerequisites**  

This supermodel requires:  

- **A PBS-based HPC cluster**  
- **A working CESM2.1.5 installation** ([CESM2.1.5 Setup Guide](https://escomp.github.io/CESM/release-cesm2/))  
- **A Conda environment** with required dependencies (see below)  

---

## **Setting Up the Supermodel**  

### **1. Create & Activate the Conda Environment**  
Before running the supermodel, create a Conda environment using the provided YAML file:  

```bash
conda env create -f sumo_CAM56_env.yml
```

Activate the environment:  

```bash
conda activate supermodel_env
```

### **2. Install CESM2.1.5 on Your HPC**  

Clone and set up CESM2.1.5:  

```bash
git clone -b release-cesm2.1.5 https://github.com/ESCOMP/CESM.git my_cesm_sandbox
cd my_cesm_sandbox
git checkout release-cesm2.1.5
./manage_externals/checkout_externals
```

Make sure CESM2.1.5 compiles successfully on your machine. If you are using a **different HPC system**, consult its documentation for any machine-specific settings.

---

## **Configuring the Supermodel**  

### **3. Edit and Run `setup.sh`**  

Edit `setup.sh` to specify paths to your Conda environment and CESM root directory. Example:  

```bash
module load conda
conda activate /path/to/your/supermodel_env/

export CESM_ROOT=/path/to/your/release-cesm2.1.5/ROOT/
chmod +x init_supermodel.py
```

Then, source the script to apply the changes:  

```bash
source ./setup.sh
```

This will:  
- Set up the environment variables  
- Define the CESM root directory  
- Ensure `init_supermodel.py` is executable  

### **4. Modify `init_supermodel.py`**  

Edit the following parameters inside `init_supermodel.py`:  

```python
# Modify model names
Mod_Cam5_Name = 'CAM5_nub0001'  #modify
Mod_Cam6_Name = 'CAM6_nub0001'  #modify

# Modify paths for your system
path_to_work_directory = "/path/to/work/directory"  #modify
path_to_scratch_directory = "/path/to/scratch/directory" #modify

# Project code for job submission
project_code = "XXXXX"  #modify

# Job settings
job_wallclock_run = "12:00:00"  #modify [must be ≤ 12:00:00]
JOBS_QUEUE = "main"  #modify [e.g., "regular", "economy", "premium"]
N_Hours = 48  #modify [total runtime in hours]
```

Then, run the script to initialize the supermodel:  

```bash
./init_supermodel.py
```

This will generate configuration files needed for model execution.

### **5. Build the Model Instances**  

After initialization, run:  

```bash
./buildmodels.py
```

This will:  
- Create two model instances (CAM5 and CAM6) with the specified names  
- Generate necessary source modifications  
- Set up data handling directories in the work and scratch directories  

---

## **Running the Supermodel**  

### **6. Submitting the Supermodel Job**  

Activate your Conda environment before submitting:  

```bash
module load conda
conda activate /path/to/your/supermodel_env/
```

Submit the models using the PBS job scheduler:  

```bash
qsub ./submit_models.sh
```

**Important:** Ensure that job wallclock time and queue settings in `submit_models.sh` match those in `buildmodels.py` to prevent scheduling conflicts.

---

## **Managing Supermodel Runs**  

### **Restarting a Run**  

If the supermodel run finishes and you need to extend it (or if it crashes), use:  

```bash
./Restart_Model.py
```

This will restart the model from the last available checkpoint.

### **Erasing and Starting Over**  

To delete all run data and restart from the initial conditions:  

```bash
./HARD_Restart.py
```

**Warning:** This will erase all previous output and restart from 1979.

---

## **Troubleshooting & Common Issues**  

### **1. Environment Issues**  

#### **Issue: Conda environment not found**  
**Solution:** Ensure the correct Conda environment is loaded before running any scripts:  
```bash
conda activate /path/to/your/supermodel_env/
```
Run `conda info --envs` to verify that the environment is correctly installed.

#### **Issue: `init_supermodel.py` or `buildmodels.py` fails to execute**  
**Solution:** Ensure the scripts are executable:  
```bash
chmod +x init_supermodel.py buildmodels.py
```

### **2. Model Compilation Errors**  

#### **Issue: CESM2.1.5 fails to compile**  
**Solution:**  
- Ensure all dependencies for CESM2.1.5 are installed  
- Check the official [CESM2.1.5 setup guide](https://escomp.github.io/CESM/release-cesm2/) for machine-specific fixes  
- Verify that `CESM_ROOT` is correctly set in `setup.sh`  

### **3. Job Scheduling Issues**  

#### **Issue: Job does not start after submission**  
**Solution:**  
- Check the job queue status using:  
  ```bash
  qstat -u $USER
  ```
- Ensure that the queue name in `submit_models.sh` matches what’s available on your system.  

#### **Issue: Model crashes due to exceeded wallclock time**  
**Solution:**  
- Increase `job_wallclock_run` in both `init_supermodel.py` and `submit_models.sh`  
- Reduce the simulation length per run (`N_Hours`)  

---
# Figures from Chapman et al. 2025. 

If you would like to reproduce all of the figures from our supermodeling manuscript. Please see [this repository,](https://github.com/WillyChap/Chapman_2024_GMD)
which contains all of the code to reproduce every figure exactly. 



## **Contributing & Support**  

For issues or contributions, open a GitHub issue or contact the maintainers. Happy supermodeling!
