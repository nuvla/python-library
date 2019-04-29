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
