#!/bin/zsh
#SBATCH --ntasks=40
#SBATCH --job-name=Template

. ~/.zshrc

srun -n 1 python testcode.py

echo "Return value was $?"
