#!/bin/bash

#-------------------------------------------------------------------------
#SBATCH -N 1                   # number of nodes
#SBATCH -n 45                  # number of "tasks" (default: allocates 1 core per task)
#SBATCH -t 0-02:00:00          # time in d-hh:mm:ss
#SBATCH -p htc                 # partition 
#SBATCH -o ./jobs/slurm.%j.out # file to save job's STDOUT (%j = JobId)
#SBATCH -e ./jobs/slurm.%j.err # file to save job's STDERR (%j = JobId)
#SBATCH --mail-type=END,FAIL   # Send an e-mail when a job stops, or fails
#SBATCH --mail-user=%u@asu.edu # Mail-to address
#SBATCH --export=NONE          # Purge the job-submitting shell environment
#-------------------------------------------------------------------------


#-------------------------------------------------------------------------
# Please change the following variables based on your needs
timesteps=2
graph_path=~/Documents/honda/JP3854600008_honda.graphml
rules_yaml_path=pyreason/examples/example_yamls/rules.yaml
facts_yaml_path=pyreason/examples/example_yamls/facts.yaml
labels_yaml_path=pyreason/examples/example_yamls/labels.yaml
ipl_yaml_path=pyreason/examples/example_yamls/ipl.yaml
output_file_name=pyreason_output
#-------------------------------------------------------------------------


#-------------------------------------------------------------------------
# Initialize conda environment
module load anaconda/py3
echo Checking if PYREASON conda environment exists
if conda env list | grep ".*PYREASON.*" >/dev/null 2>&1
then
    echo PYREASON environment exists
    source activate PYREASON
else
    echo Creating PYREASON conda environment
    conda create -n PYREASON python=3.8
    source activate PYREASON
    echo Installing necessary packages
    pip install -r requirements.txt
fi


# Run pyreason
python3 -u -m pyreason.scripts.diffuse --graph_path $graph_path --timesteps $timesteps --rules $rules_yaml_path  --facts $facts_yaml_path --labels $labels_yaml_path --ipl $ipl_yaml_path --output_to_file --output_file $output_file_name
#-------------------------------------------------------------------------


