# Changelog

## Unreleased

## Released

## [4.0.2](https://github.com/nuvla/python-library/compare/4.0.1...4.0.2) (2024-08-21)


### Dependencies

* requests version &gt;= 2.32.3 and updated other dependencies ([6ae74d6](https://github.com/nuvla/python-library/commit/6ae74d602bf28d293fa4dd94967b879bf39afc00))
* Update indirect dependencies ([a8bc9d3](https://github.com/nuvla/python-library/commit/a8bc9d3cc9b166360b3685511ca5d105e5dba7ba))

## [4.0.1](https://github.com/nuvla/python-library/compare/4.0.0...4.0.1) (2024-05-08)


### Bug Fixes

* remove redundant ID retrieval from edit operation ([#43](https://github.com/nuvla/python-library/issues/43)) ([b1b7ad1](https://github.com/nuvla/python-library/commit/b1b7ad10847fc43b1888337a991aa3a2a1df7c40))

## [4.0.0](https://github.com/nuvla/python-library/compare/3.0.9...4.0.0) (2024-04-18)


### ⚠ BREAKING CHANGES

* Trigger major version release

### Features

* Remove build CI maven (in favor of Poetry) and synchronise release workflow ([#41](https://github.com/nuvla/python-library/issues/41)) ([7e50d70](https://github.com/nuvla/python-library/commit/7e50d70077779786e40c888d15c069146ffb8c9c))
* Trigger major version release ([88285e3](https://github.com/nuvla/python-library/commit/88285e3cbc4102cc090f031e18723ea7cc58549b))

## [3.0.9] - 2023-07-18

### Changed

- Update PyYAML from 6.0 to 6.0.1

## [3.0.8] - 2022-05-10

### Added

- Hook operation support

### Changed

- Release - push package with twine
- API - sanitise Nuvla endpoint (remove forward slashes)

## [3.0.7] - 2022-03-30

### Added

- Search - helper to build filters

## [3.0.6] - 2022-03-21

### Added

- Date - helper module around dates

## [3.0.5] - 2021-12-16

### Added

- Compression - New option to compress json sent to server
- Accept gzip encoding by default

### Changed

- Remove not portable and redundant call to setuptools.find_packages.

## [3.0.3] - 2021-03-24

### Added

- Bulk operation support

## [3.0.2] - 2020-07-01

### Changed

- Minor refactors in credential resource wrapper to support provisioning of COE
  on CSPs in job-engine.

## [3.0.1] - 2020-03-27

### Changed

- Add DeploymentParameter warapper resource, fix Deployment credential_id
  method, and Credential methods addition.

## [3.0.0] - 2020-03-25

### Changed

- Removed support of Python 2.

## [2.1.2] - 2020-03-25

### Changed

- Added wrapper resources on top of CIMI for deployment, callback, credential,
  module, notification.

## [2.1.1] - 2019-10-10

### Added

- Bulk delete support

## [2.1.0] - 2019-06-07

### Added

- Allow nuvla-authn-info header to be set with all requests.

### Changed

- Release script fix

## [2.0.0] - 2019-04-29

- Initial, production release of nuvla-api.

### Changed

- Updates of versions, no functional changes

## [0.0.6] - 2019-04-18

Test of release process.

### Changed

- release of nuvla-api 0.0.6
