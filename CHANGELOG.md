# Changelog

## Unreleased

## Released

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
