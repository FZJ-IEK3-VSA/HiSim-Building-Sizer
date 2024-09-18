#!/bin/bash
#SBATCH --job-name=hisim_building_sizer
#SBATCH --ntasks=3
#SBATCH --cpus-per-task=3
#SBATCH --array=1
#SBATCH --output=/fast/home/k-rieck/HiSim-Building-Sizer/cluster_requests/slurm_output_files/out_%A_%a.txt
#SBATCH --error=/fast/home/k-rieck/HiSim-Building-Sizer/cluster_requests/slurm_output_files/err_%A_%a.txt
#SBATCH --exclude=cn[33-55]
#SBATCH --nice=10

# Run python in HiSim-Building-Sizer/building_sizer: sbatch /fast/home/k-rieck/HiSim-Building-Sizer/cluster_requests/job_array_start_building_sizer.sh
python start_building_sizer_no_utsp.py
