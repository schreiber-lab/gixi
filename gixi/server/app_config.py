from pathlib import Path
from collections import OrderedDict
from .config import Config

PROGRAM_PATH = Path(__file__).parents[2].expanduser().absolute()


class ContrastConfig(Config):
    limit: float = 2000
    coef: float = 5000
    log: bool = True
    disable: bool = False

    CONF_NAME = 'Contrast Correction'

    PARAM_DESCRIPTIONS = dict(
        limit='Relative clip value (CLAHE parameter)',
        coef='Normalization value (CLAHE parameter)',
        log='Apply logarithm to images before CLAHE (recommended)',
        turn_off='Disable contrast correction'
    )


class QSpaceConfig(Config):
    z0: int
    y0: int

    size_x: int
    size_y: int

    wavelength: float

    pixel_size: float
    distance: float

    incidence_angle: float

    q_xy_max: float
    q_z_max: float

    q_xy_num: int
    q_z_num: int

    flip_y: bool = False
    flip_x: bool = False

    CONF_NAME = 'Q Space Parameters'

    PARAM_DESCRIPTIONS = dict(
        z0='Vertical beam center coordinate',
        y0='Horizontal beam center coordinate',
        size_x='Horizontal raw image size',
        size_y='Vertical raw image size',
        wavelength='Wavelength in angstroms',
        pixel_size='Pixel size in mm',
        distance='Sample-detector distance in mm',
        incidence_angle='Incidence angle in deg',
        q_xy_max='Max q parallel value in angstroms',
        q_z_max='Max q z value in angstroms',
        q_xy_num='Number of pixels for Q map (horizontal)',
        q_z_num='Number of pixels for Q map (vertical)',
        flip_y='Flip image vertically',
        flip_x='Flip image horizontally',
    )


class GeneralConfig(Config):
    sum_images: int = 10
    real_time: bool = False
    timeout: float = 120
    sleep_time: float = 0.1

    CONF_NAME = 'General'

    PARAM_DESCRIPTIONS = dict(
        sum_images='Number of consecutive images to sum up',
        real_time='Real-time measurements (wait for new data)',
        timeout='Timeout (sec) for new images to appear'
    )


class PostProcessingConfig(Config):
    nms_level: float = 0.1
    score_level: float = 0.6

    CONF_NAME = 'Postprocessing Parameters'

    PARAM_DESCRIPTIONS = dict(
        nms_level='IOU level for non-maximum suppression',
        score_level='Minimal score level'
    )


class PolarConversionConfig(Config):
    angular_size: int = 512
    q_size: int = 1024
    algorithm: int = 1

    CONF_NAME = 'Polar Conversion Parameters'

    PARAM_DESCRIPTIONS = dict(
        angular_size='Angular size (pixels)',
        q_size='Q size (pixels)',
    )


class ParallelConfig(Config):
    parallel_computation: bool = False
    max_batch: int = 64

    CONF_NAME = 'Multithreading'

    PARAM_DESCRIPTIONS = dict(
        parallel_computation='Use multithreading to accelerate computations',
        max_batch='Max batch size for ML detection model',
    )


class ClusterConfig(Config):
    partition: str = 'allgpu'
    reservation: str = ''
    time: str = '00:30:00'
    nodes: int = 1
    chdir: str = '~/maxwell_output/'
    use_cuda: bool = False

    CONF_NAME = 'Cluster Configuration'

    PARAM_DESCRIPTIONS = dict(
        partition='Job partition',
        reservation='Name of the reservation (if exists)',
        time='Max job time in format HH:MM:SS',
        chdir='Directory to store job logs',
        use_cuda='Use CUDA acceleration (use only for partitions with gpu support)',
    )

    @property
    def timeout(self) -> int:
        hours, minutes, seconds = map(int, self.time.split(':'))
        return seconds + minutes * 60 + hours * 3600


class SaveConfig(Config):
    save_img: bool = True
    save_polar_img: bool = True
    save_scores: bool = True


class ProgramPathsConfig(Config):
    local_env: bool = False

    CONF_NAME = 'Program Paths'

    PARAM_DESCRIPTIONS = dict()


class ModelConfig(Config):
    name: str = 'save_only_largest_2'

    CONF_NAME = 'Model Config'

    PARAM_DESCRIPTIONS = dict(
        name='Model name',
    )


class JobConfig(Config):
    folder_name: str
    data_dir: str
    dest_name: str
    config_path: str
    name: str = 'GIXD_ML'

    CONF_NAME = 'Data Paths'

    PARAM_DESCRIPTIONS = dict(
        folder_name='Raw data folder name (relative to data_dir/raw/)',
        data_dir='Path to the root directory of the measurements (data_dir)',
        dest_name='H5 file name for storing the results (stored to data_dir/processed/)',
        config_path='Path to the configuration file (relative to program_dir/)',
        name='Name of the job',
    )


class AppConfig(Config):
    general: GeneralConfig
    job_config: JobConfig
    cluster_config: ClusterConfig
    q_space: QSpaceConfig
    contrast: ContrastConfig
    parallel: ParallelConfig
    polar_config: PolarConversionConfig
    postprocessing_config: PostProcessingConfig
    save_config: SaveConfig
    model_config: ModelConfig = ModelConfig()
    program_paths_config: ProgramPathsConfig = ProgramPathsConfig()

    GUI_CONFIG_GROUPS = OrderedDict(
        job_config=JobConfig,
        general=GeneralConfig,
        save_config=SaveConfig,
        cluster_config=ClusterConfig,
        q_space=QSpaceConfig,
        contrast=ContrastConfig,
        parallel=ParallelConfig,
        polar_config=PolarConversionConfig,
        postprocessing_config=PostProcessingConfig,
        model_config=ModelConfig,
    )

    def copy(self):
        return AppConfig(**{name: getattr(self, name).copy() for name in self.__annotations__.keys()})

    @classmethod
    def from_dict(cls, conf_dict: dict):
        return cls(*[
            conf_type(**conf_dict.get(conf_name, {}))
            for conf_name, conf_type in cls.__annotations__.items()
        ])

    def asdict(self):
        return {name: getattr(self, name).asdict() for name in self.__annotations__.keys()}

    @property
    def src_path(self) -> Path:
        jc = self.job_config
        path = Path(jc.data_dir).expanduser()
        if not self.program_paths_config.local_env:
            path = path / 'raw'
        path = path / jc.folder_name
        return path

    @property
    def dest_path(self) -> Path:
        jc = self.job_config
        path = Path(jc.data_dir).expanduser()
        if not self.program_paths_config.local_env:
            path = path / 'processed'
        path = path / jc.dest_name
        return path

    @property
    def device(self):
        return 'cuda' if self.cluster_config.use_cuda else 'cpu'
