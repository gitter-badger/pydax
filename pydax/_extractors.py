#
# Copyright 2020--2021 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"Dataset unarchiving and uncompressing functionality."


import json
import mimetypes
import pathlib
import tarfile


def tar_extractor(path: pathlib.Path, data_dir: pathlib.Path, file_list_file: pathlib.Path):
    """Handles: ``.tar``, ``.tar.gz``, ``.tar.bz2``, ``.tar.xz``

    :param path: Path to the tar archive.
    :param data_dir: Path to the data dir to extract data files to.
    :file_list_file: Path to the file that stores the list of files in the downloaded dataset.
    :raises tarfile.ReadError:
    """
    print('1: tar')

    try:
        tar = tarfile.open(path)
    except tarfile.ReadError as e:
        raise tarfile.ReadError(f'Failed to unarchive "{path}"\ncaused by:\n{e}')
    with tar:
        members = {}
        for member in tar.getmembers():
            members[member.name] = {'type': int(member.type)}
            if member.isreg():  # For regular files, we also save its size
                members[member.name]['size'] = member.size
        with open(file_list_file, mode='w') as f:
            # We do not specify 'utf-8' here to match the default encoding used by the OS, which also likely
            # uses this encoding for accessing the filesystem.
            json.dump(members, f, indent=2)
        tar.extractall(path=data_dir)


def zip_extractor(path: pathlib.Path):
    print('1: zip')
    # ('application/zip', None)


def gzip_extractor(path: pathlib.Path):
    print('2: gzip')
    # ('text/csv', 'gzip')
    # ('text/plain', 'gzip')


def bzip2_extractor(path: pathlib.Path):
    print('2: bzip2')
    # ('text/csv', 'bzip2')
    # ('text/plain', 'bzip2')


def lzma_extractor(path: pathlib.Path):
    print('2: lzma')
    # ('text/csv', 'xz')
    # ('text/plain', 'xz')


# ftype
archives = {
    'application/x-tar': tar_extractor,
    'application/zip': zip_extractor
}

# fencoding
compressions = {
    'gzip': gzip_extractor,
    'bzip2': bzip2_extractor,
    'xz': lzma_extractor
}


# We first run the extractor determined by guess_type
# if that returns an error or guess_type doesn’t know the type try all extractors
# if none of the extractors work raise an error that says file type unsupported

# For each extractor, wrap open() in try-except e.g. like how tarfile.open(path) does it
# Change except keywords to take a tuple of exceptions occurring during file open

def extract_data_files(path: pathlib.Path, data_dir: pathlib.Path, file_list_file: pathlib.Path):

    extractor_map = {**archives, **compressions}
    ftype, fencoding = mimetypes.guess_type(path)

    # 1. Check if mimetypes.guess_type guesses a working extractor
    if any(key in extractor_map.keys() for key in (ftype, fencoding)):
        # Check if file is an archive, otherwise file is assumed to be a compressed flat file
        extractor = extractor_map.get(ftype, extractor_map.get(fencoding))
        try:
            extractor(path, data_dir, file_list_file)
        except Exception:
            pass
        else:
            return

    # 2. Otherwise try all extractors and see if one works
    # What about situation where gzip is accidentally used to uncompress a .tar.gz?
    for extractor in extractor_map.values():
        try:
            extractor(path, data_dir, file_list_file)
        except Exception:
            pass
        else:
            return

    # 3. Otherwise assume unsupported flat file or compression/archive type
    raise RuntimeError('Filetype not supported')
