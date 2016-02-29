# hpcc_tools
Scripts to help make HPCC work easier. Created for use at MSU, though could potentially apply to any hpcc facility.


dimexp.cpp
---------
Command line tool to be used in submission scripts for array jobs, wherein you want to map that array ID (1-N) to some set of parameters such as mapping 1-N to your 3 simulation parameters controlling group size, arena size, and data output iterations, which are respectively: 5-10, 16-32, and 1-5. Thus you are mapping 1-510 onto these three variables. This tool takes the arrayID as input, the ranges for each variables, and returns the parameter for each variable.

#####Example
Say I have 3 parameters as input to my simulation, with ranges respectively: 5-10, 16-32, and 1-5. I know the arrayID range for the submission script will need to be:

```bash
$> dimexp q 5:10 16:32 1:5
510
```

In the simulation script, each of the variables may be obtained by:

```bash
VARS=$(dimexp ${PBS_ARRAYID} 5:10 16:32 1:5)
VAR1=$(echo ${VARS} | cut -d ' ' -f1)
VAR2=$(echo ${VARS} | cut -d ' ' -f2)
VAR3=$(echo ${VARS} | cut -d ' ' -f3)
```

queue.py
--------
Command line tool submission manager to get around submission array size limitations. Write your submission file as normal, and this will split up your requested array (-t 1-N) into manageable sizes. Configuration is in the first few lines of the .py file. This tool will manage jobs in a hidden .queue dir in your scratch space. In event of something strange happening, either remove that dir manually, or issue `./queue.py resume`.

#####Example
```bash
$> ./queue.py myGiantSubmission.qsub.sh
```


collectend.sh and collectlod.sh
---------------------------------
Scripts to aid collecting many replicate data files into one, skipping N rows if desired, and visually displaying a horizontal progress bar since this can potentially take a long time.

#####Example
```bash
$> ./collectend.sh experiment1dir experiment2dir ...
```
