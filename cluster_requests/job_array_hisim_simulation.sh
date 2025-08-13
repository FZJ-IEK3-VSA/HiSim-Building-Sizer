#!/bin/bash
#SBATCH --job-name=hisim_simulation
#SBATCH --time=12:00:00
#SBATCH --ntasks=1
#SBATCH --mem=13G
#SBATCH --cpus-per-task=1
#SBATCH --array=1
#SBATCH --output=/fast/home/k-rieck/HiSim-Building-Sizer/cluster_requests/slurm_output_files/out_simu_%A_%a.txt
#SBATCH --error=/fast/home/k-rieck/HiSim-Building-Sizer/cluster_requests/slurm_output_files/err_simu_%A_%a.txt
#SBATCH --nice=10

# Input parameters from Python script
input_param1=$1
input_param2=$2
input_param3=$3
input_param4=$4
input_param5=$5
# # Your SLURM task command, for example, calling a Python script with the parameters
python /fast/home/k-rieck/HiSim-Building-Sizer/building_sizer_execution/hisim_simulation_no_utsp.py "$input_param1" "$input_param2" "$input_param3" "$input_param4" "$input_param5"

