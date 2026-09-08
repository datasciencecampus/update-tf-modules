# Changelog

## [0.3.0](https://github.com/datasciencecampus/update-tf-modules/compare/v0.2.1...v0.3.0) (2026-09-08)


### Features

* resolve updater_ref to commit SHA for reproducibility ([cadf084](https://github.com/datasciencecampus/update-tf-modules/commit/cadf08432f63ba3127535adcfbfba8d49ac730d4))


### Bug Fixes

* **ci:** incorporate moving major tag as a step in release pipeline ([30d45f6](https://github.com/datasciencecampus/update-tf-modules/commit/30d45f6e4a58d39613fd63bdc8253a8d6f3ead5c))
* **ci:** skip major-tag push when already up to date ([8cadcc9](https://github.com/datasciencecampus/update-tf-modules/commit/8cadcc9150069c8596f268b96d2798f0947513ca))
* ensure major release tags (vX) are reliably moved on publish ([eee0bd5](https://github.com/datasciencecampus/update-tf-modules/commit/eee0bd597db0f7cec1e1795f485e4b30c6296366))


### Documentation

* add major-tag verification guidance ([9da2d33](https://github.com/datasciencecampus/update-tf-modules/commit/9da2d33c68c42064dbf0875c4174ebc815c7e00e))


### Refactoring

* **ci:** use release-please outputs for major-tag update ([66e548a](https://github.com/datasciencecampus/update-tf-modules/commit/66e548a5d5751c39f89e0330337b7a2e4732ce75))

## [0.2.1](https://github.com/datasciencecampus/update-tf-modules/compare/v0.2.0...v0.2.1) (2026-09-03)


### Refactoring

* **logging:** replace package print statements with module-level… ([f552bb7](https://github.com/datasciencecampus/update-tf-modules/commit/f552bb78ae1e509d53a7a82b95d7d8f82522972a))

## [0.2.0](https://github.com/datasciencecampus/update-tf-modules/compare/v0.1.1...v0.2.0) (2026-08-26)


### Features

* **logging:** add ModuleOutcome dataclass and run summary ([9864042](https://github.com/datasciencecampus/update-tf-modules/commit/986404235003d7de4fb4f94437506c69bcee84d3))
* **logging:** add per-module progress and outcome messages ([3948693](https://github.com/datasciencecampus/update-tf-modules/commit/39486936b29ebbb10e76bd039a521eacc9dc5458))
* **logging:** add structured lifecycle output ([00aabce](https://github.com/datasciencecampus/update-tf-modules/commit/00aabce0fbfdb187a6317b079f89acb721477116))
* **logging:** add structured progress output and stdlib logging ([dcb72e5](https://github.com/datasciencecampus/update-tf-modules/commit/dcb72e5b76ac4c6c97a6afa59d8bf47c7a4d0e98))
* **logging:** add zero-replacement cause hints for unchanged modules ([b421f6b](https://github.com/datasciencecampus/update-tf-modules/commit/b421f6b9d15ce4f471c0e6ea627492651701bcec))


### Bug Fixes

* **ci:** default updater_ref to v0, preflight-validate ref, and align docs ([0228310](https://github.com/datasciencecampus/update-tf-modules/commit/0228310094da6382adf8f5f22de2a66cbec75773))
* **updaters:** count only actual module source changes ([e3ff9f5](https://github.com/datasciencecampus/update-tf-modules/commit/e3ff9f5abfcd04132f75e9090d6fb13636cdf7fd))
* **workflow:** default updater_ref to v0 and validate ref before checkout ([48d5306](https://github.com/datasciencecampus/update-tf-modules/commit/48d530674048806f4e824ce3b6229318e5d3e069))


### Refactoring

* **logging:** migrate log.py to stdlib logging, update tests to caplog ([9124e60](https://github.com/datasciencecampus/update-tf-modules/commit/9124e607bffcb12214f15214a780472f670b0276))
* **logging:** use standard module loggers and remove wrapper ([1d8a2cd](https://github.com/datasciencecampus/update-tf-modules/commit/1d8a2cd95dec380a2c62fc164d7aa1901c00dde4))

## [0.1.1](https://github.com/datasciencecampus/update-tf-modules/compare/v0.1.0...v0.1.1) (2026-06-17)


### Documentation

* clarify release tag semantics and mutability policy ([35e3e2a](https://github.com/datasciencecampus/update-tf-modules/commit/35e3e2a082c30168e941fd00d78952493bbf7b90))
