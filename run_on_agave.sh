#!/bin/bash

#-------------------------------------------------------------------------
#SBATCH -N 1                   # number of nodes
#SBATCH -n 1                   # number of "tasks" (default: allocates 1 core per task)
#SBATCH -t 0-00:02:00          # time in d-hh:mm:ss
#SBATCH -p serial              # partition 
#SBATCH -q normal              # QOS
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
rules_yaml_path=mancalog/examples/example_yamls/rules.yaml
facts_yaml_path=mancalog/examples/example_yamls/facts.yaml
labels_yaml_path=mancalog/examples/example_yamls/labels.yaml
profile=true
profile_out=agave_1cpu_1core.txt
#-------------------------------------------------------------------------


#-------------------------------------------------------------------------
# Initialize conda environment
module load anaconda/py3
echo Checking if MANCALOG conda environment exists
if conda env list | grep ".*MANCALOG.*" >/dev/null 2>&1
then
    echo MANCALOG environment exists
    source activate MANCALOG
else
    echo Creating MANCALOG conda environment
    conda create -n MANCALOG
    source activate MANCALOG
    echo Installing necessary packages
    pip install -r requirements.txt
fi


# Run mancalog
python3 -m mancalog.scripts.diffuse --graph_path $graph_path --timesteps $timesteps --rules_yaml_path $rules_yaml_path  --facts_yaml_path $facts_yaml_path --labels_yaml_path $labels_yaml_path --profile $profile --profile_out $profile_out
#-------------------------------------------------------------------------


