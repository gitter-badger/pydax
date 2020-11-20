#
# Copyright 2020 IBM Corp. All Rights Reserved.
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

from http.server import HTTPServer, SimpleHTTPRequestHandler
from tempfile import TemporaryDirectory
import threading
import uuid

import pytest

from pydax import load_schemata
from pydax.dataset import Dataset


@pytest.fixture
def tmp_sub_dir(tmp_path):
    "A ``pathlib.Path`` object that points to a temporary dir, created as a subdir of ``tmp_path``."

    with TemporaryDirectory(dir=tmp_path) as d:
        yield d


@pytest.fixture
def tmp_symlink_dir(tmp_path, tmp_sub_dir):
    "A ``pathlib.Path`` object that points to a temporary symlink to ``tmp_sub_dir``. It always sits in ``tmp_dir``."

    while True:
        symlink_dir = tmp_path / str(uuid.uuid4())
        # A collision is extremely unlikely, but for the sake of completeness, this check never hurts.
        if not symlink_dir.exists():
            break

    symlink_dir.symlink_to(tmp_sub_dir, target_is_directory=True)

    yield symlink_dir

    symlink_dir.unlink()


@pytest.fixture
def loaded_schemata():
    return load_schemata(dataset_url='./tests/schemata/datasets.yaml',
                         format_url='./tests/schemata/formats.yaml',
                         license_url='./tests/schemata/licenses.yaml')


@pytest.fixture
def gmb_schema(loaded_schemata):
    return loaded_schemata.schemata['dataset_schema'].export_schema('datasets', 'gmb', '1.0.2')


@pytest.fixture
def wikitext103_schema(loaded_schemata):
    return loaded_schemata.schemata['dataset_schema'].export_schema('datasets', 'wikitext103', '1.0.1')


@pytest.fixture(scope='session')
def local_http_server():
    "A local http server that serves the source directory."

    with HTTPServer(("", 8080), SimpleHTTPRequestHandler) as httpd:
        # Start a new thread, because httpd.serve_forever is blocking
        threading.Thread(target=httpd.serve_forever, name='Local Http Server', daemon=True).start()
        yield httpd


@pytest.fixture
def http_schema_file_url(local_http_server):
    "The base of remote http schema file URLs."

    return f"http://{local_http_server.server_address[0]}:{local_http_server.server_address[1]}/tests/schemata/"


@pytest.fixture
def downloaded_wikitext103_dataset(wikitext103_schema):
    with TemporaryDirectory() as tmp_data_dir:
        yield Dataset(wikitext103_schema, data_dir=tmp_data_dir, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
