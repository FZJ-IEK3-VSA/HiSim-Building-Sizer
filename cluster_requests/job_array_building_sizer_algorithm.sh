#!/bin/bash
#SBATCH --job-name=bs_algorithm
#SBATCH --ntasks=3
#SBATCH --cpus-per-task=3
#SBATCH --array=1
#SBATCH --output=/fast/home/k-rieck/HiSim-Building-Sizer/cluster_requests/slurm_output_files/out_algo_%A_%a.txt
#SBATCH --error=/fast/home/k-rieck/HiSim-Building-Sizer/cluster_requests/slurm_output_files/err_algo_%A_%a.txt
#SBATCH --exclude=cn[33-55]
#SBATCH --nice=10

# Input parameters from Python script
input_param1=$1
input_param2=$2
# Your SLURM task command, for example, calling a Python script with the parameters
# This script is called in /fast/home/k-rieck/HiSim-Building-Sizer/building_sizer/start_building_sizer_no_utsp.py
python /fast/home/k-rieck/HiSim-Building-Sizer/building_sizer/building_sizer_algorithm_no_utsp.py "$input_param1" "$input_param2"
