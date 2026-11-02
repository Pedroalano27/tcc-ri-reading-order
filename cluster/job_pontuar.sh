#!/usr/bin/env bash
#SBATCH --job-name=pontuar_lm
#SBATCH --account=default
#SBATCH --partition=hpc-spark-45-ephem
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=/beegfs/home/%u/tcc/logs/%x-%j.out
# Pontua os pares de linhas (resultados/ordem_lm/pares) com um LM causal no conteiner NGC.
# Uso: sbatch cluster/job_pontuar.sh Qwen/Qwen3-8B [args extras do pontuar_pares_lm.py]
# Retomavel: reenviar o mesmo comando pula as paginas ja pontuadas.
set -euo pipefail
MODELO=${1:?informe o modelo HF}; shift || true
H=/beegfs/home/${USER}
srun --container-image="$H/images/pytorch.sqsh" --container-mounts="$H:$H" \
     --container-workdir="$H/tcc/ordem_lm" bash -c '
set -euo pipefail
# PYTHONNOUSERSITE: ~/.local tem pacotes x86_64 do no de login; no no aarch64 quebram o import do torch.
export HF_HOME='"$H"'/tcc/hf PIP_CACHE_DIR='"$H"'/tcc/pip_cache PYTHONUNBUFFERED=1 PYTHONNOUSERSITE=1
V='"$H"'/tcc/venv_lm
[ -d "$V" ] || python -m venv --system-site-packages "$V"
source "$V/bin/activate"
pip install -q -r requisitos_pontuar.txt
nvidia-smi --query-gpu=name,memory.total --format=csv
python -B pontuar_pares_lm.py --entrada pares --saida escores --modelo "$@"
' bash "$MODELO" --dtype bfloat16 --lote 8 --dispositivo cuda "$@"
