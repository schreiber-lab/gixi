from pathlib import Path
import yaml

CONFIG_FOLDER = Path(__file__).parents[2] / 'config_files'


class ExtendableNamedTuple(object):
    def __new__(cls, *args, **kwargs):
        if args:
            if len(args) > len(cls.__annotations__):
                raise ValueError(f'Wrong number of positional arguments.'
                                 f' Expected {len(cls.__annotations__)}, provided {len(args)}')
            for attr_value, attr_name in zip(args, cls.__annotations__.keys()):
                if attr_name in kwargs:
                    raise ValueError(f'Argument {attr_name} provided twice.')
                kwargs[attr_name] = attr_value

        for key in kwargs.keys():
            if key not in cls.__annotations__:
                raise ValueError(f'Unexpected keyword argument {key}')

        for attr_name, attr_type in cls.__annotations__.items():
            if attr_name in kwargs:
                pass
            elif attr_name in cls.__dict__:
                kwargs[attr_name] = getattr(cls, attr_name)
            else:
                raise ValueError(f'Missing non-default argument {attr_name}.')

        cls._update_init_dict(kwargs)

        instance = super().__new__(cls)
        for attr_name, attr_value in kwargs.items():
            setattr(instance, attr_name, attr_value)
        return instance

    @staticmethod
    def _update_init_dict(kwargs):
        pass

    def __setattr__(self, key, value):
        if key in self.__annotations__ and key in self.__dict__:
            raise AttributeError(f'Attempt to overwrite an existing attribute {key}.')
        super().__setattr__(key, value)

    def asdict(self):
        return {k: getattr(self, k) for k in self.__annotations__.keys()}

    def update(self, **kwargs):
        params = self.asdict()
        params.update(kwargs)
        return self.__class__(**params)

    def __repr__(self):
        attr_line = ", ".join([f"{k}={v}" if not isinstance(v, str) else f"{k}='{v}'"
                               for k, v in self.asdict().items()])
        return f'{self.__class__.__name__}({attr_line})'


class Config(ExtendableNamedTuple):
    PARAM_DESCRIPTIONS = {}

    CONF_NAME = ''

    def copy(self):
        return self.__class__(**self.asdict())

    def __reduce__(self):
        # we return a tuple of class_name to call,
        # and optional parameters to pass when re-creating
        return self.__class__, (self.asdict(),)

    @classmethod
    def from_config(cls, filename: str, default_config: dict or 'Config' = None):
        with open(str(cls.path(filename)), 'r') as f:
            conf_dict = yaml.load(f, Loader=yaml.SafeLoader)
            if default_config:
                if isinstance(default_config, Config):
                    default_config = default_config.asdict()
                default_config.update(conf_dict)
                conf_dict = default_config
            return cls.from_dict(conf_dict)

    @classmethod
    def from_dict(cls, conf_dict: dict):
        return cls(**conf_dict)

    @staticmethod
    def path(filename: str) -> Path:
        if '.' not in filename:
            filename = f'{filename}.yaml'
        return CONFIG_FOLDER / filename

    def save_to_config(self, path: Path):
        config_path = self.path(path.name)
        try:
            with open(str(config_path), 'w') as f:
                yaml.dump(self.asdict(), f)
        except FileNotFoundError:
            raise NotADirectoryError(f'Directory does not exist: {config_path.parent}')
