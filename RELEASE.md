# Release Process

Configure `~/.pypirc` with pypi repo credentials. This file should look
like as following:

```
[distutils]
index-servers=pypi

[pypi]
username = <username>
password = <password>
```

You will need following python release utilities:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade build
python3 -m pip install --upgrade twine
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
