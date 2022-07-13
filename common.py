import os
import io
import hashlib
import pathlib
import argparse
import logging as lg
from typing import Union
from fnmatch import fnmatch
from datetime import datetime as dt
from collections.abc import Iterator, Iterable

ALGORITHMS_AVAILABLE = {'md5', 'sha1', 'sha256', 'sha512', 'blake2b'}
ALGORITHMS_SUFFIXES = {'.' + x for x in ALGORITHMS_AVAILABLE}

class ChecksumsArguments(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_argument('-R', dest='recursive', action='store_true',
            default=False, help='enable recursion')
        self.add_argument('--include-hidden', dest='include_hidden',
            action='store_true', default=False,
            help='include hidden files and dirs')
        self.add_argument('--filter-from', dest='filter_from', metavar='FILE',
            type=pathlib.Path, help='filter from file containing ' + \
            'shell-style wildcards')
        self.add_argument('--prefix', dest='prefix', type=str,
            default='.checksums', help='prefix to use for sumfiles')
        self.add_argument('-v', '--verbose', dest='verbose', action='store_true',
            default=False, help='be verbose')
            
        algorithm = self.add_mutually_exclusive_group()

        for a in ALGORITHMS_AVAILABLE:
            algorithm.add_argument(f'--{a}', dest='algorithm',
                action='store_const', const=a, help=f'uses {a}')

        self.set_defaults(algorithm='sha256')
        self.add_argument('path', metavar='PATH', type=pathlib.Path)

def format_log_message(message: str, path: pathlib.Path) -> str:
    return f'{message}:{path}'

def print_message(message: str, path: pathlib.Path):
    print(f'{message} {path}')

def print_error(e: Exception, path: pathlib.Path, *, root: pathlib.Path = None):
    print(f'{e.__class__.__name__} {path if root is None else path.relative_to(root)}')

def is_hidden(path: pathlib.Path) -> bool: # gonna include some windows stuff
    hidden = False

    if path.name.startswith('.'):
        hidden = True

    return hidden

def walk(path: pathlib.Path, *,
         recursive: bool = True,
         filters: list|None = None,
         include_hidden: bool = False) -> Iterator[pathlib.Path]:
    
    if (path / '.nochecksums').is_file(): # scan relative dirs within
        lg.debug(format_log_message('found .nochecksums', path))
        return

    if not os.access(path, os.R_OK):
        lg.debug(format_log_message('no read access', path))
        return # report error

    for i in path.iterdir():
        if not include_hidden and is_hidden(i):
            lg.debug(format_log_message('hidden', path))
            continue

        if filters and any((fnmatch(i, x) for x in filters)):
            lg.debug(format_log_message('matched filter', path))
            continue

        yield i.resolve()

        if recursive and i.is_dir():
            yield from walk(i, recursive=recursive, filters=filters,
                            include_hidden=include_hidden)

def idirs(path: pathlib.Path, *,
          filters: Iterable = None,
          include_hidden: bool = False) -> Iterator[pathlib.Path]:
    path = path.resolve()

    yield path

    for i in walk(path, recursive=True, filters=filters,
                  include_hidden=include_hidden):
        if not i.is_dir(): continue

        yield i

def ifiles(path: pathlib.Path, *,
           recursive: bool = False,
           filters: Iterable = None,
           include_hidden: bool = False) -> Iterator[pathlib.Path]:
    for i in walk(path, recursive=recursive, filters=filters,
                  include_hidden=include_hidden):
        if not i.is_file(): continue
        if i.suffix in ALGORITHMS_SUFFIXES: continue

        yield i

def read_file(path: pathlib.Path, *,
              delimiters: Iterable = ('  ', ' *', ' ')) -> dict:
    data = {}

    with open(path, 'r', encoding='utf-8') as fp:
        prev = ''
        mtime = dt.utcfromtimestamp(path.stat().st_mtime)

        for line in fp:
            line = line.strip()

            if line.startswith('#'):
                prev = line
                continue

            for d in delimiters:
                split = line.split(d, 1)

                if len(split) == 2:
                    break
            else:
                raise ValueError('could not parse sumfile') # better Exception w/ filename plz

            df = path.parent / split[1]

            if not df.is_file() or df.name != df.resolve().name: # match casing on all systems
                prev = line
                continue

            data[df] = {}
            data[df]['checksum'] = split[0].lower()

            if prev.startswith('#?'):
                try:
                    data[df]['created'] = dt.fromisoformat(prev.lstrip('#?'))
                except ValueError:
                    pass
            
            if data[df].get('created') is None: # fallback
                data[df]['created'] = mtime 

            prev = line

    return data

def write_file(path: pathlib.Path, data: dict, *,
               delimiter: str = '  '):
    with open(path, 'w', encoding='utf-8', newline='\n') as fp:
        for df in sorted(data.keys()):
            fp.write((
                f"#?{data[df]['created']}\n"
                f"{data[df]['checksum']}{delimiter}{df.name}\n"
            ))

def read_filter_file(path: pathlib.Path) -> list:
    filters = []

    with open(path, 'r', encoding='utf-8') as fp:
        for line in fp:
            if not line: continue
            filters.append(line.strip())

    return filters

def is_newer(path: pathlib.Path, than: dt):
    return than <= dt.utcfromtimestamp(path.stat().st_mtime)

def is_older(path: pathlib.Path, than: dt):
    return than >= dt.utcfromtimestamp(path.stat().st_mtime)

def find_files(path: pathlib.Path, algorithms: Union[set, None] = None) -> tuple:
    sumfiles = []

    for i in (x for x in path.iterdir() if x.is_file()):
        suffix = i.suffix.lstrip('.')

        if algorithms and suffix not in algorithms: continue
        if suffix in ALGORITHMS_AVAILABLE: sumfiles.append(i)

    return tuple(sumfiles)
    
def create_checksum(path: pathlib.Path(), algorithm: str) -> str:
    checksum = hashlib.new(algorithm)

    with open(path, 'rb') as fp:
        while chunk := fp.read(io.DEFAULT_BUFFER_SIZE):
            checksum.update(chunk)

    return checksum.hexdigest()
    