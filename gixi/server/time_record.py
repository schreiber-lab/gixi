from collections import defaultdict
from typing import Callable
from time import perf_counter
from functools import wraps
from contextlib import contextmanager
from pathlib import Path

from torch import save, load

from numpy import mean


def _ignore_if_no_record(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if args[0].no_record:
            return
        return func(*args, **kwargs)

    return wrapper


class TimeRecorder(object):
    def __init__(self, name: str, no_record: bool = False, records: dict = None):
        self.name = name
        self.no_record = no_record
        self.records = defaultdict(list)
        self._start_time = None
        self._record_name = ''

        if records:
            self.records.update(records)

    def iterate(self, iterator, name: str = ''):
        if self.no_record:
            return iterator

        iterator = iter(iterator)

        while True:
            try:
                with self(name):
                    yield next(iterator)
            except StopIteration:
                return

    @contextmanager
    def __call__(self, name: str = ''):
        self.start_record(name)
        yield
        self.end_record()

    @_ignore_if_no_record
    def start_record(self, name: str = ''):
        self._start_time = perf_counter()
        self._record_name = name

    @_ignore_if_no_record
    def end_record(self, name: str = ''):
        try:
            record = perf_counter() - self._start_time
        except TypeError:
            raise TypeError(f'Have to call start_record before calling end_record.')

        self.records[self._get_record_name(name)].append(record)
        self.clear_record()

    def _get_record_name(self, end_name: str = ''):
        names = [self.name]
        if self._record_name:
            names.append(self._record_name)
        if end_name:
            names.append(end_name)

        name = '/'.join(names)
        return name

    def clear_record(self):
        self._start_time = None
        self._record_name = ''

    def clear(self):
        self.records.clear()
        self.clear_record()

    def add_records(self, records: dict):
        _add_records(self.records, records)

    def __iadd__(self, other: 'TimeRecorder'):
        if not isinstance(other, TimeRecorder):
            return NotImplemented

        _add_records(self.records, other.records)

        return self

    def __add__(self, other: 'TimeRecorder'):
        if not isinstance(other, TimeRecorder):
            return NotImplemented
        records = _add_records(self.records.copy(), other.records)

        return TimeRecorder(self.name, self.no_record, records=dict(records))

    def asdict(self):
        return dict(name=self.name, no_record=self.no_record, records=dict(self.records))

    def save(self, path: str or Path):
        save(self.asdict(), path)

    @classmethod
    def load(cls, path: str or Path):
        return cls(**load(path))

    def mean_records(self, reduce: bool = False, reduce_func: Callable = None):
        return self._apply(mean, reduce, reduce_func)

    def total_records(self, reduce: bool = False, reduce_func: Callable = None):
        return self._apply(sum, reduce, reduce_func)

    def num_records(self, reduce: bool = False, reduce_func: Callable = None):
        return self._apply(len, reduce, reduce_func)

    def _apply(self, func: Callable, reduce: bool = False, reduce_func: Callable = None):
        res = {keys: func(records) for keys, records in self.records.items()}

        if reduce:
            reduce_func = reduce_func or func
            res = reduce_func(list(res.values()))
        return res

    @property
    def total_number_of_records(self):
        return self.num_records(reduce=True, reduce_func=sum)

    @property
    def total_time(self):
        return self.total_records(reduce=True, reduce_func=sum)

    def get_table_str(self):
        return _get_table_str(self.to_table())

    def to_table(self):
        total_records = self.total_records()
        mean_records = self.mean_records()
        num_records = self.num_records()

        heads = ['', 'Num records', 'Mean (s)', 'Total (s)']
        keys = sorted(self.records.keys())

        table = [heads] + [
            [k, str(num_records[k]), '{:.2e}'.format(mean_records[k]), '{:.2e}'.format(total_records[k])]
            for k in keys
        ]

        return table

    def __repr__(self):
        total_num_records = self.total_number_of_records
        return f'TimeRecorder(name={self.name}, records_num={total_num_records}): \n' + self.get_table_str()


def _join_names(*names):
    return '/'.join(names)


def _add_records(records, other_records):
    for k, v in other_records.items():
        records[k].extend(v)
    return records


def _get_table_str(table):
    longest_cols = [
        max([len(str(row[i])) for row in table]) + 3
        for i in range(len(table[0]))
    ]

    row_format = "".join(["{:>" + str(longest_col) + "}" for longest_col in longest_cols])

    table_str = '\n'.join(row_format.format(*row) for row in table)

    return table_str


if __name__ == '__main__':
    import time


    def iterator_func(num):
        for i in range(num):
            time.sleep(0.01)
            yield i


    first_recorder = TimeRecorder('first_recorder')
    first_recorder.start_record('first record')
    first_recorder.end_record('failed branch')

    second_recorder = TimeRecorder('second_recorder')

    for i in second_recorder.iterate(iterator_func(10), 'iterator'):
        print(i)

    for i in range(10):
        with second_recorder('test'):
            time.sleep(0.01)

    first_recorder += second_recorder

    third_recorder = TimeRecorder('first_recorder')
    third_recorder.start_record('first record')
    time.sleep(0.01)
    third_recorder.end_record('failed branch')
    third_recorder.start_record('first record')
    time.sleep(0.01)
    third_recorder.end_record('successful branch')
    first_recorder += third_recorder
    print(first_recorder)
