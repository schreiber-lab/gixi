from abc import abstractmethod
from enum import Enum, auto
from typing import Union, Dict, Tuple
from functools import wraps
from numbers import Number

import torch
from torch import Tensor

NumberProperty = Union[Number, 'PropertyDistribution']
Size = Union[int, Tuple[int, ...]]


class Distributions(Enum):
    CONSTANT = auto()
    UNIFORM = auto()
    NORMAL = auto()
    LOG_NORMAL = auto()
    POISSON = auto()
    RAND_INT = auto()


def _size_to_tuple(func):
    @wraps(func)
    def wrapper(self, size=None):
        if size is None:
            size = (1,)
        elif isinstance(size, int):
            size = (size,)
        return func(self, size)

    return wrapper


class PropertyDistribution(object):
    __slots__ = ('_params',)

    def __init__(self, **kwargs: NumberProperty):
        self._params: Dict[str, NumberProperty] = kwargs

    @property
    def device(self):
        return self._params.get('device', 'cuda')

    def __getitem__(self, item) -> Number:
        value = self._params[item]
        if isinstance(value, PropertyDistribution):
            value = value().item()
        return value

    def __setitem__(self, key, value):
        self._params[key] = value

    def __iter__(self):
        yield from self._params.items()

    @property
    def params(self):
        yield from self._params.keys()

    @abstractmethod
    def __call__(self, size: Size = None) -> Tensor:
        pass

    def __repr__(self):
        params_dict = dict(self._params)
        params_dict['device'] = self.device
        args = ', '.join(f'{k}={v}' for k, v in params_dict.items())
        return f'{self.__class__.__name__}({args})'


class DistributionDecorator(PropertyDistribution):
    def __init__(self, distribution: PropertyDistribution, **kwargs):
        super().__init__(**kwargs)
        self.distribution: PropertyDistribution = distribution

    @abstractmethod
    def __call__(self, size: Size = None):
        pass

    def __repr__(self):
        return f'{super().__repr__()[:-1]}, distribution={self.distribution})'


class ClipProperty(DistributionDecorator):
    def __init__(self, distribution: PropertyDistribution, min: float = None, max: float = None):
        super().__init__(distribution, min=min, max=max)

    def __call__(self, size: Size = None):
        return torch.clamp(self.distribution(size), min=self['min'], max=self['max'])


class Binomial(PropertyDistribution):
    def __init__(self, p: float, **kwargs):
        super().__init__(p=p, **kwargs)

    @_size_to_tuple
    def __call__(self, size: Size = None):
        probabilities = torch.ones(size, device=self.device) * self['p']
        return torch.bernoulli(probabilities)


class ZeroPercent(DistributionDecorator):
    def __init__(self, main_distribution: PropertyDistribution, zero_probability: float):
        super().__init__(main_distribution)
        self._binomial = Binomial(1 - zero_probability, device=main_distribution.device)

    @_size_to_tuple
    def __call__(self, size: Size = None):
        return self._binomial(size) * self.distribution(size)


class IntDistribution(DistributionDecorator):
    def __init__(self, distribution: PropertyDistribution):
        super().__init__(distribution)

    def __call__(self, size: Size = None):
        res = self.distribution(size)
        if isinstance(res, Tensor):
            return self.distribution(size).type(int)
        else:
            return int(res)


class Constant(PropertyDistribution):
    def __init__(self, value: float or int, **kwargs):
        super().__init__(value=value, **kwargs)

    def __call__(self, size: Size = None):
        return self['value'] if not size else torch.ones(size, device=self.device) * self['value']


class Normal(PropertyDistribution):
    def __init__(self, mean: float = 0, sigma: float = 1, **kwargs):
        super().__init__(mean=mean, sigma=sigma, **kwargs)

    @_size_to_tuple
    def __call__(self, size: Size = None):
        return torch.normal(self['mean'], self['sigma'], size=size, device=self.device)


class LogNormal(Normal):
    @_size_to_tuple
    def __call__(self, size: Size = None):
        return torch.exp(torch.normal(self['mean'], self['sigma'], size=size, device=self.device))


class Poisson(PropertyDistribution):
    def __init__(self, mean: float = None, **kwargs):
        super().__init__(mean=mean, **kwargs)

    def __call__(self, size: Size = None):
        if not isinstance(size, Tensor):
            if not self['mean']:
                raise ValueError('Mean is not defined.')
            if not size:
                size = 1
            means = torch.ones(size, device=self.device) * self['mean']
        else:
            means = size

        return torch.poisson(means)


class Uniform(PropertyDistribution):
    def __init__(self, low: float = 0, high: float = 1, **kwargs):
        super().__init__(low=low, high=high, **kwargs)

    @_size_to_tuple
    def __call__(self, size: Size = None):
        return torch.rand(*size, device=self.device) * (self['high'] - self['low']) + self['low']


class RandInt(Uniform):
    @_size_to_tuple
    def __call__(self, size: Size = None):
        return torch.randint(self['low'], self['high'], size=size, device=self.device)


_DISTRIBUTIONS_DICT: dict = {
    Distributions.CONSTANT: Constant,
    Distributions.UNIFORM: Uniform,
    Distributions.NORMAL: Normal,
    Distributions.LOG_NORMAL: LogNormal,
    Distributions.POISSON: Poisson,
    Distributions.RAND_INT: RandInt,
}


def get_distribution(distribution: Distributions, *args, **kwargs) -> PropertyDistribution:
    """
    A distribution factory. Returns distribution based on type and properties.

    :param distribution: type of the distribution.
    :param args: args passed to the distribution constructor.
    :param kwargs: kwargs passed to the distribution constructor.
    :return: PropertyDistribution instance.

    Examples:
    >>> constant = get_distribution(Distributions.CONSTANT, 2, device='cpu')
    >>> constant
    Constant(value=2, device=cpu)
    >>> constant()
    2
    >>> constant(size=3)
    tensor([2., 2., 2.])

    >>> get_distribution(Distributions.UNIFORM, high=Uniform(3, 4), low=2)
    Uniform(low=2, high=Uniform(low=3, high=4, device=cuda), device=cuda)

    >>> get_distribution(Distributions.LOG_NORMAL, 0, sigma=2)
    LogNormal(mean=0, sigma=2, device=cuda)

    """
    try:
        return _DISTRIBUTIONS_DICT[distribution](*args, **kwargs)
    except KeyError:
        raise KeyError(f'Unknown distribution type {distribution}.')


if __name__ == '__main__':
    u = ClipProperty(Normal(mean=Uniform(low=2, high=10), scale=3), min=0.5)
    print(sum([u(100).mean().item() for _ in range(100)]) / 100)
