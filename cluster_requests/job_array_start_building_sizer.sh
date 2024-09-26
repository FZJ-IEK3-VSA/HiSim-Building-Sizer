#!/bin/bash
#SBATCH --job-name=hisim_building_sizer
#SBATCH --ntasks=3
#SBATCH --cpus-per-task=3
#SBATCH --array=1-3
#SBATCH --output=/fast/home/k-rieck/HiSim-Building-Sizer/cluster_requests/slurm_output_files/out_%A_%a.txt
#SBATCH --error=/fast/home/k-rieck/HiSim-Building-Sizer/cluster_requests/slurm_output_files/err_%A_%a.txt
#SBATCH --exclude=cn[33-55]
#SBATCH --nice=10

# Specify the path to the config file
config=/fast/home/k-rieck/HiSim-Building-Sizer/building_sizer_preparation/bs_job_arrays/bs_job_array_20240926-0953.csv

# Extract the config path for the current $SLURM_ARRAY_TASK_ID
bs_config_path=$(awk -F',' -v ArrayTaskID=$SLURM_ARRAY_TASK_ID '$1==ArrayTaskID {print $2}' $config)

# Run python in HiSim-Building-Sizer/building_sizer_execution: sbatch /fast/home/k-rieck/HiSim-Building-Sizer/cluster_requests/job_array_start_building_sizer.sh
python start_building_sizer_no_utsp.py ${bs_config_path}
