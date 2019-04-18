# Nuvla Python Client Library

[![Build Status](https://travis-ci.com/nuvla/python-library.svg?branch=master)](https://travis-ci.com/nuvla/python-library)

Nuvla client library to facilitate interaction with the Nuvla REST API
via the Python language.

## Artifacts

 - `nuvla-api` package: Available from
   [pypi](https://pypi.org/project/nuvla-api/).


## Documentation
You can get the full documentation by typing:

```python
from nuvla.api import Api
help(Api)
```

Or for a specific function:

```python
from nuvla.api import Api
help(Api.search)
```

## Usage

```python
  from nuvla.api import Api
  
  api = Api('https://nuvla.io')
  
  # Login with username & password
  api.login_password('username', 'password')
  # or
  # Login with api-key & secret
  api.login_apikey('credential/uuid', 'secret')

  api.search('user')

  # Logout
  api.logout()
  ```
## Release Process

Configure `~/.pypirc` with pypi repo credentials. This file should look
like as following:

```
[distutils]
index-servers=pypi

[pypi]
username = <username>
password = <password>
```

**Before** creating the release:

 - Decide what semantic version to use for this release and change the
   version, if necessary, in `code/project.clj` and all the `pom.xml`
   files.  (It should still have the "-SNAPSHOT" suffix.)

 - Update the `CHANGELOG.md` file.

 - Push all changes to GitHub, including the updates to
   `CHANGELOG.md`.

Again, be sure to set the version **before** tagging the release.

Check that everything builds correctly with:

    mvn clean install

To tag the code with the release version and to update the master
branch to the next snapshot version, run the command:

    ./release.sh true

If you want to test what will happen with the release, leave off the
"true" argument and the changes will only be made locally.


## Copyright

Copyright &copy; 2019, SixSq Sàrl

## License

Licensed under the Apache License, Version 2.0 (the "License"); you
may not use this file except in compliance with the License.  You may
obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
