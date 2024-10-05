[![DOI](https://zenodo.org/badge/699459300.svg)](https://zenodo.org/doi/10.5281/zenodo.12577788)


# A NCAR CAM5/CAM6 SuperModel


Right now this only works on the NCAR machines and the Norwegian Machines (Betzy), if there is enough community interest, I would be happy to work on porting it to other systems. 
Clone this to your home directory ... and run with a bash shell please

# To SET UP the supermodel: 
<ins>FIRST:</ins>
```
$ source ./setup.sh
```
- this will set up your bash enviroment and set the CESM_ROOT (currently hardcoded to Wills Directory)

<ins>NEXT:</ins>

**IMPORTANT**: Change the settings in the file **"init_supermodel.py"** which are specified with the "#modify" comment and run this file 
```
$ ./init_supermodel.py
```
<ins>THEN:</ins>

a few python files should be written in the current git directory. Please run:

```
$ ./buildmodels.py
```

This will create two model instances of CAM5 and CAM6 that have the names you specified in the **setup.sh** script, as well as the necessary source mods and the fake Data Assimilation scripts additionally, folders are created in your work directory and scratch directory which do the data handling. 

# To Submit the supermodel:

With the update to Derecho we had to do one more trick thing: 

```
module load conda
conda activate /glade/work/wchapman/miniconda3.2/envs/cesmML3.10gpuPD
```

To submit both jobs on one active queue: 
```
qsub ./submit_models.sh
```

## What is a supermodel? 

[See our paper](https://journals.ametsoc.org/view/journals/bams/aop/BAMS-D-22-0070.1/BAMS-D-22-0070.1.xml). The modeling of weather and climate has been a success story. The skill of forecasts continues to improve and model biases continue to decrease. Combining the output of multiple models has further improved forecast skill and reduced biases. But are we exploiting the full capacity of state-of-the-art models in making forecasts and projections? Supermodeling is a recent step forward in the multi-model ensemble approach. Instead of combining model output after the simulations are completed, in a supermodel individual models exchange state information as they run, influencing each other’s behavior. By learning the optimal parameters that determine how models influence each other based on past observations, model errors are reduced at an early stage before they propagate into larger scales and affect other regions and variables. The models synchronize on a common solution that through learning remains closer to the observed evolution. Effectively a new dynamical system has been created, a supermodel, that optimally combines the strengths of the constituent models. The supermodel approach has the potential to rapidly improve current state-of-the-art weather forecasts and climate predictions. In this paper we introduce supermodeling, demonstrate its potential in examples of various complexity and discuss learning strategies. We conclude with a discussion of remaining challenges for a successful application of supermodeling in the context of state-of-the-art models. The supermodeling approach is not limited to the modeling of weather and climate, but can be applied to improve the prediction capabilities of any complex system, for which a set of different models exist. 

In this instance we have coupled CAM5 and CAM6 in order exchange state information. Happy supermodeling! 

## A BIG NOTE: 
THE PBS FILE (submit_models.sh) and the settings in the buildmodels.py have to match! So if you change Job_WALLCLOCK_TIME in one, then you must change it in the other)!!!

## IF you reach the end of a run and want to keep going or the model crashes
```
./Restart_Model.py
```
Run ***"./Restart_Model.py"*** and everything should be Gucci, submit the models again

## IF YOU WANT TO ERASE AND START OVER: 
```
./HARD_Restart.py
```
Run ***"./HARD_Restart.py"*** but warning this erases data and starts back in 1979


