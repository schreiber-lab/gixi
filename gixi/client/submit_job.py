from typing import Tuple
from pathlib import Path
import subprocess

from gixi.server.app_config import AppConfig, PROGRAM_PATH


def generate_sh_str(config: AppConfig) -> str:
    if config.cluster_config.reservation:
        partition = f'#SBATCH --reservation={config.cluster_config.reservation}'
    else:
        partition = f'#SBATCH --partition={config.cluster_config.partition}'

    if config.cluster_config.use_cuda:
        constraint = f'#SBATCH --constraint=GPU'
    else:
        constraint = ''

    python_args = str(config.job_config.config_path)
    return f'''#!/bin/bash
{partition}
#SBATCH --chdir {str(Path(config.cluster_config.chdir).expanduser())}
#SBATCH --nodes={config.cluster_config.nodes}
#SBATCH --job-name {config.job_config.id_name}
#SBATCH --time={config.cluster_config.time}
#SBATCH --output {get_conf_out(config)}
#SBATCH --error {get_conf_err(config)}
{constraint}

cd {str(PROGRAM_PATH)}
export DATA_DIR={config.job_config.data_dir}
python -m gixi.server {python_args}
'''


def save_sh_file(conf: AppConfig) -> Path:
    sh_str = generate_sh_str(conf)
    path = get_conf_path(conf)

    with open(str(path), 'w') as f:
        f.write(sh_str)
    return path


def get_conf_out(conf: AppConfig) -> str:
    return f'{conf.job_config.name}_{conf.job_config.folder_name}.out'


def get_conf_err(conf: AppConfig) -> str:
    return f'{conf.job_config.name}_{conf.job_config.folder_name}.err'


def get_conf_path(conf: AppConfig) -> Path:
    return PROGRAM_PATH / 'sbatch_scripts' / f'{conf.job_config.name}.sh'


def submit_job(conf: AppConfig) -> Tuple[str, str]:
    path = save_sh_file(conf)
    process = subprocess.Popen(
        ['sbatch', str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = process.communicate()
    return stdout.decode(), stderr.decode()
