# Changelog

## [0.11.2](https://github.com/nsphung/mcp-snowflake-server/compare/v0.11.1...v0.11.2) (2026-05-06)


### Bug Fixes

* Remove provenance setting in publish.yml ([#34](https://github.com/nsphung/mcp-snowflake-server/issues/34)) ([62f911a](https://github.com/nsphung/mcp-snowflake-server/commit/62f911ae39954e755ec1f94f97c0d2d9e6bbab98))

## [0.11.1](https://github.com/nsphung/mcp-snowflake-server/compare/v0.11.0...v0.11.1) (2026-05-06)


### Features

* Enable caching and additional metadata in publish.yml ([#32](https://github.com/nsphung/mcp-snowflake-server/issues/32)) ([5f65ee2](https://github.com/nsphung/mcp-snowflake-server/commit/5f65ee225a4a22bc2db58ec992e3e509aa95a943))


### Miscellaneous Chores

* release 0.11.1 ([3620a9f](https://github.com/nsphung/mcp-snowflake-server/commit/3620a9f841371f632232d34323d8be4cbf10d158))

## [0.11.0](https://github.com/nsphung/mcp-snowflake-server/compare/v0.10.1...v0.11.0) (2026-05-06)


### Features

* Manage update with dependabot ([#26](https://github.com/nsphung/mcp-snowflake-server/issues/26)) ([778d14f](https://github.com/nsphung/mcp-snowflake-server/commit/778d14fa4ad657f93c0e43b97fcd091156264d0f))


### Bug Fixes

* chore(deps): update package + sec update ([#31](https://github.com/nsphung/mcp-snowflake-server/issues/31)) ([7bd1aa3](https://github.com/nsphung/mcp-snowflake-server/commit/7bd1aa30df064561bc75f87866caa5daaec5f6fe))

## [0.10.1](https://github.com/nsphung/mcp-snowflake-server/compare/v0.10.0...v0.10.1) (2026-05-06)


### Features

* Add docker gate via gh env / wait pypi before mcp publish ([7888c63](https://github.com/nsphung/mcp-snowflake-server/commit/7888c63d4b63bc42a17a3a731c75b680f06f5382))
* Warm docker cache for PR ([7bc2b3a](https://github.com/nsphung/mcp-snowflake-server/commit/7bc2b3a111fd3497e9502be94719d1052edbbb24))


### Documentation

* Add url docker ([ce68bfb](https://github.com/nsphung/mcp-snowflake-server/commit/ce68bfb6e1c4a2f5869e91fd675b18db16381ac2))


### Miscellaneous Chores

* release 0.10.1 ([fa5a3e5](https://github.com/nsphung/mcp-snowflake-server/commit/fa5a3e536b6d2a34a3a8810ff12cdbce1ef9783c))

## [0.10.0](https://github.com/nsphung/mcp-snowflake-server/compare/v0.9.5...v0.10.0) (2026-05-06)


### Features

* Guard release + manual retries steps ([4a6caa4](https://github.com/nsphung/mcp-snowflake-server/commit/4a6caa450ed1dfc05aa326ab4c611d6e171c4e81))

## [0.9.5](https://github.com/nsphung/mcp-snowflake-server/compare/v0.9.4...v0.9.5) (2026-05-06)


### Features

* add --exclude-json-results CLI option ([da75726](https://github.com/nsphung/mcp-snowflake-server/commit/da75726e402b5c0aacb4e6650791dd84400acba7))
* Add --exclude-json-results to reduce context window usage ([f5e2022](https://github.com/nsphung/mcp-snowflake-server/commit/f5e2022abba75a49440b5c42995cbcd70517e16f))
* Add context7.json with server URL and public key ([#12](https://github.com/nsphung/mcp-snowflake-server/issues/12)) ([1549d8d](https://github.com/nsphung/mcp-snowflake-server/commit/1549d8d2acab8f0384903f780cbbac0e4de6abdb))
* Add gh actions lint ([6f7f0c2](https://github.com/nsphung/mcp-snowflake-server/commit/6f7f0c281630a5e3b2a0ec7298fab8f413c2e62c))
* add mypy / tests / test coverage ([58c7e9a](https://github.com/nsphung/mcp-snowflake-server/commit/58c7e9a6c676696f528b0ff8fafc40d50ea4c25f))
* Add OAuth 2.0 Client Credentials flow Snowflake ([#11](https://github.com/nsphung/mcp-snowflake-server/issues/11)) ([3831899](https://github.com/nsphung/mcp-snowflake-server/commit/38318998274e17c1f37645c1777bbcc4c6d5f71a))
* Add oxfmt for json, toml, md & yml ([#17](https://github.com/nsphung/mcp-snowflake-server/issues/17)) ([fb12ec7](https://github.com/nsphung/mcp-snowflake-server/commit/fb12ec7c81b2eedfe3c333462f6dcb20658adbf9))
* Add prek as pre-commit drop-in ([#16](https://github.com/nsphung/mcp-snowflake-server/issues/16)) ([9b43e0c](https://github.com/nsphung/mcp-snowflake-server/commit/9b43e0cc8e9b6c003163b8ead556a29b6419718a))
* Add pypi publish ([d2a92e9](https://github.com/nsphung/mcp-snowflake-server/commit/d2a92e9716a1ac40289436680c928497cde5468d))
* Add PyPI shields ([6f58434](https://github.com/nsphung/mcp-snowflake-server/commit/6f58434e85b690b143d400db4ce24a1e1e361cd0))
* Add release / Tag as 0.5.0 ([31c05aa](https://github.com/nsphung/mcp-snowflake-server/commit/31c05aac7f92b3b0fff77dec05a497756192080e))
* Add ruff / mypy / pre-commit / tests / tests coverage ([2bf6dd8](https://github.com/nsphung/mcp-snowflake-server/commit/2bf6dd805ca072db4baf76c83df9b35de54c836b))
* Add ruff format/lint ([c2d5eba](https://github.com/nsphung/mcp-snowflake-server/commit/c2d5eba20d65b8b454a40901b7683b56cb7d63be))
* Add Snowflake Key Pair Auth ([1ae1b72](https://github.com/nsphung/mcp-snowflake-server/commit/1ae1b72f246283b97d04c64efe9b7caeb04dc0b3))
* Add Snowflake Key Pair Auth ([6e787bf](https://github.com/nsphung/mcp-snowflake-server/commit/6e787bfaf78927e42e6ece0b5853fdec2e103176))
* Conform to LICENCE ([93ab9b2](https://github.com/nsphung/mcp-snowflake-server/commit/93ab9b2a9e9359f8977d06a7330e91ea7693240f))
* Docker fix / harden / publish ([#18](https://github.com/nsphung/mcp-snowflake-server/issues/18)) ([ae08b0f](https://github.com/nsphung/mcp-snowflake-server/commit/ae08b0f19f228dbf54a89bbbc9567e54366592b2))
* Improve test coverage / fix release-please for uv ([f0bd7e9](https://github.com/nsphung/mcp-snowflake-server/commit/f0bd7e954da58e8955fd61513d1a4c23d6ae1864))
* Publish in MCP registry ([20864c6](https://github.com/nsphung/mcp-snowflake-server/commit/20864c6454c5479dc2e1651dd344e710b871a692))


### Bug Fixes

* distribution name ([257f72a](https://github.com/nsphung/mcp-snowflake-server/commit/257f72afc409825f0edaa2c0e10e641d7af0409c))
* fix release please component in tag ([1c6cb25](https://github.com/nsphung/mcp-snowflake-server/commit/1c6cb254a65b10644db28326c1a74b3f8200001c))
* Ignore changelog in oxfmt for release-please ([1852f36](https://github.com/nsphung/mcp-snowflake-server/commit/1852f3648afa50b1313c39a76f28c80415f7b617))
* prek for release-please ([55f8b8f](https://github.com/nsphung/mcp-snowflake-server/commit/55f8b8f43581f3b32868f664c1dd42d5e7d35c67))
* registryBaseUrl server.json manifest ([74887a0](https://github.com/nsphung/mcp-snowflake-server/commit/74887a0b0f21b70b8ee2ac96f1332fe093336e6b))
* remove old gh actions ([a68f554](https://github.com/nsphung/mcp-snowflake-server/commit/a68f5549358b36d71e3461f6f9be82e3db5aa405))
* server.json manifest version ([90a99fd](https://github.com/nsphung/mcp-snowflake-server/commit/90a99fd8e6bde94880a0785b9b92893b6c0a2dcd))
* Validate server.json local/ci ([b6f5906](https://github.com/nsphung/mcp-snowflake-server/commit/b6f5906d2f31f9ea60271f2321a499dca41f5626))


### Documentation

* Add shields ([28dbd04](https://github.com/nsphung/mcp-snowflake-server/commit/28dbd04f60d82d9271125b3cf1a27a21a39365e3))
* Add VScode / OpenCode setup ([f7c1602](https://github.com/nsphung/mcp-snowflake-server/commit/f7c160279d3d26334e0652819be259f7b810f0ca))
* Add vscode install badge ([f0006fc](https://github.com/nsphung/mcp-snowflake-server/commit/f0006fc73fec352b5592ab83a744d9aea28973bc))
* Change to MIT License ([4234914](https://github.com/nsphung/mcp-snowflake-server/commit/42349145df1d8004ed6ef5cf088d921205c937ba))
* fix links ([92a0e14](https://github.com/nsphung/mcp-snowflake-server/commit/92a0e14eeb5d321b1bbe46d115ab3a24d2ab8323))
* Revise README badges and section formatting ([#15](https://github.com/nsphung/mcp-snowflake-server/issues/15)) ([ed2e724](https://github.com/nsphung/mcp-snowflake-server/commit/ed2e72404722ec99beebeb9ad3f81b906dd56237))
* Update doc ([8550234](https://github.com/nsphung/mcp-snowflake-server/commit/8550234f905797614eb72e69cd339f8022876145))
* Update NOTICE / README links ([9153e92](https://github.com/nsphung/mcp-snowflake-server/commit/9153e92e2f68a85e83ec45cc6fb703f87892927e))


### Miscellaneous Chores

* release 0.5.0 ([8d1dcd2](https://github.com/nsphung/mcp-snowflake-server/commit/8d1dcd2bbbe05bfa254633e315626d70b4111d8b))
* release 0.5.1 ([d3dab53](https://github.com/nsphung/mcp-snowflake-server/commit/d3dab53bd036740c4b4fff7fa3735c73a8751c41))
* release 0.9.2 ([aaaf430](https://github.com/nsphung/mcp-snowflake-server/commit/aaaf43002bab54eb1f3aa9dd35bbcbb7343d149a))
* release 0.9.5 ([f0497d2](https://github.com/nsphung/mcp-snowflake-server/commit/f0497d22220cd6f72ddb1fb04fd3120fb17b909c))

## [0.9.4](https://github.com/nsphung/mcp-snowflake-server/compare/v0.9.3...v0.9.4) (2026-05-06)


### Bug Fixes

* server.json manifest version ([90a99fd](https://github.com/nsphung/mcp-snowflake-server/commit/90a99fd8e6bde94880a0785b9b92893b6c0a2dcd))

## [0.9.3](https://github.com/nsphung/mcp-snowflake-server/compare/v0.9.2...v0.9.3) (2026-05-06)


### Bug Fixes

* registryBaseUrl server.json manifest ([74887a0](https://github.com/nsphung/mcp-snowflake-server/commit/74887a0b0f21b70b8ee2ac96f1332fe093336e6b))

## [0.9.2](https://github.com/nsphung/mcp-snowflake-server/compare/v0.9.1...v0.9.2) (2026-05-06)


### Miscellaneous Chores

* release 0.9.2 ([aaaf430](https://github.com/nsphung/mcp-snowflake-server/commit/aaaf43002bab54eb1f3aa9dd35bbcbb7343d149a))

## [0.9.1](https://github.com/nsphung/mcp-snowflake-server/compare/v0.9.0...v0.9.1) (2026-05-06)


### Bug Fixes

* Ignore changelog in oxfmt for release-please ([1852f36](https://github.com/nsphung/mcp-snowflake-server/commit/1852f3648afa50b1313c39a76f28c80415f7b617))

## [0.9.0](https://github.com/nsphung/mcp-snowflake-server/compare/v0.8.0...v0.9.0) (2026-05-06)


### Features

* Add context7.json with server URL and public key ([#12](https://github.com/nsphung/mcp-snowflake-server/issues/12)) ([1549d8d](https://github.com/nsphung/mcp-snowflake-server/commit/1549d8d2acab8f0384903f780cbbac0e4de6abdb))
* Add oxfmt for json, toml, md & yml ([#17](https://github.com/nsphung/mcp-snowflake-server/issues/17)) ([fb12ec7](https://github.com/nsphung/mcp-snowflake-server/commit/fb12ec7c81b2eedfe3c333462f6dcb20658adbf9))
* Add prek as pre-commit drop-in ([#16](https://github.com/nsphung/mcp-snowflake-server/issues/16)) ([9b43e0c](https://github.com/nsphung/mcp-snowflake-server/commit/9b43e0cc8e9b6c003163b8ead556a29b6419718a))
* Docker fix / harden / publish ([#18](https://github.com/nsphung/mcp-snowflake-server/issues/18)) ([ae08b0f](https://github.com/nsphung/mcp-snowflake-server/commit/ae08b0f19f228dbf54a89bbbc9567e54366592b2))


### Bug Fixes

* prek for release-please ([55f8b8f](https://github.com/nsphung/mcp-snowflake-server/commit/55f8b8f43581f3b32868f664c1dd42d5e7d35c67))


### Documentation

* Add vscode install badge ([f0006fc](https://github.com/nsphung/mcp-snowflake-server/commit/f0006fc73fec352b5592ab83a744d9aea28973bc))
* Change to MIT License ([4234914](https://github.com/nsphung/mcp-snowflake-server/commit/42349145df1d8004ed6ef5cf088d921205c937ba))
* Revise README badges and section formatting ([#15](https://github.com/nsphung/mcp-snowflake-server/issues/15)) ([ed2e724](https://github.com/nsphung/mcp-snowflake-server/commit/ed2e72404722ec99beebeb9ad3f81b906dd56237))

## [0.8.0](https://github.com/nsphung/mcp-snowflake-server/compare/v0.7.0...v0.8.0) (2026-04-30)

### Features

- Add OAuth 2.0 Client Credentials flow Snowflake ([#11](https://github.com/nsphung/mcp-snowflake-server/issues/11)) ([3831899](https://github.com/nsphung/mcp-snowflake-server/commit/38318998274e17c1f37645c1777bbcc4c6d5f71a))

### Documentation

- Update NOTICE / README links ([9153e92](https://github.com/nsphung/mcp-snowflake-server/commit/9153e92e2f68a85e83ec45cc6fb703f87892927e))

## [0.7.0](https://github.com/nsphung/mcp-snowflake-server/compare/v0.6.1...v0.7.0) (2026-04-28)

### Features

- Add PyPI shields ([6f58434](https://github.com/nsphung/mcp-snowflake-server/commit/6f58434e85b690b143d400db4ce24a1e1e361cd0))
- Publish in MCP registry ([20864c6](https://github.com/nsphung/mcp-snowflake-server/commit/20864c6454c5479dc2e1651dd344e710b871a692))

### Documentation

- Add VScode / OpenCode setup ([f7c1602](https://github.com/nsphung/mcp-snowflake-server/commit/f7c160279d3d26334e0652819be259f7b810f0ca))

## [0.6.1](https://github.com/nsphung/mcp-snowflake-server/compare/v0.6.0...v0.6.1) (2026-04-27)

### Bug Fixes

- distribution name ([257f72a](https://github.com/nsphung/mcp-snowflake-server/commit/257f72afc409825f0edaa2c0e10e641d7af0409c))

## [0.6.0](https://github.com/nsphung/mcp-snowflake-server/compare/v0.5.1...v0.6.0) (2026-04-27)

### Features

- Add pypi publish ([d2a92e9](https://github.com/nsphung/mcp-snowflake-server/commit/d2a92e9716a1ac40289436680c928497cde5468d))

### Bug Fixes

- fix release please component in tag ([1c6cb25](https://github.com/nsphung/mcp-snowflake-server/commit/1c6cb254a65b10644db28326c1a74b3f8200001c))

### Documentation

- fix links ([92a0e14](https://github.com/nsphung/mcp-snowflake-server/commit/92a0e14eeb5d321b1bbe46d115ab3a24d2ab8323))

## [0.5.1](https://github.com/nsphung/mcp-snowflake-server/compare/v0.5.0...v0.5.1) (2026-04-27)

### Features

- add --exclude-json-results CLI option ([da75726](https://github.com/nsphung/mcp-snowflake-server/commit/da75726e402b5c0aacb4e6650791dd84400acba7))
- Add --exclude-json-results to reduce context window usage ([f5e2022](https://github.com/nsphung/mcp-snowflake-server/commit/f5e2022abba75a49440b5c42995cbcd70517e16f))
- Add gh actions lint ([6f7f0c2](https://github.com/nsphung/mcp-snowflake-server/commit/6f7f0c281630a5e3b2a0ec7298fab8f413c2e62c))
- add mypy / tests / test coverage ([58c7e9a](https://github.com/nsphung/mcp-snowflake-server/commit/58c7e9a6c676696f528b0ff8fafc40d50ea4c25f))
- Add release / Tag as 0.5.0 ([31c05aa](https://github.com/nsphung/mcp-snowflake-server/commit/31c05aac7f92b3b0fff77dec05a497756192080e))
- Add ruff / mypy / pre-commit / tests / tests coverage ([2bf6dd8](https://github.com/nsphung/mcp-snowflake-server/commit/2bf6dd805ca072db4baf76c83df9b35de54c836b))
- Add ruff format/lint ([c2d5eba](https://github.com/nsphung/mcp-snowflake-server/commit/c2d5eba20d65b8b454a40901b7683b56cb7d63be))
- Add Snowflake Key Pair Auth ([1ae1b72](https://github.com/nsphung/mcp-snowflake-server/commit/1ae1b72f246283b97d04c64efe9b7caeb04dc0b3))
- Add Snowflake Key Pair Auth ([6e787bf](https://github.com/nsphung/mcp-snowflake-server/commit/6e787bfaf78927e42e6ece0b5853fdec2e103176))
- Conform to LICENCE ([93ab9b2](https://github.com/nsphung/mcp-snowflake-server/commit/93ab9b2a9e9359f8977d06a7330e91ea7693240f))
- Improve test coverage / fix release-please for uv ([f0bd7e9](https://github.com/nsphung/mcp-snowflake-server/commit/f0bd7e954da58e8955fd61513d1a4c23d6ae1864))

### Bug Fixes

- remove old gh actions ([a68f554](https://github.com/nsphung/mcp-snowflake-server/commit/a68f5549358b36d71e3461f6f9be82e3db5aa405))

### Documentation

- Add shields ([28dbd04](https://github.com/nsphung/mcp-snowflake-server/commit/28dbd04f60d82d9271125b3cf1a27a21a39365e3))
- Update doc ([8550234](https://github.com/nsphung/mcp-snowflake-server/commit/8550234f905797614eb72e69cd339f8022876145))

### Miscellaneous Chores

- release 0.5.0 ([8d1dcd2](https://github.com/nsphung/mcp-snowflake-server/commit/8d1dcd2bbbe05bfa254633e315626d70b4111d8b))
- release 0.5.1 ([d3dab53](https://github.com/nsphung/mcp-snowflake-server/commit/d3dab53bd036740c4b4fff7fa3735c73a8751c41))

## 0.5.0 (2026-04-27)

### Features

- add --exclude-json-results CLI option ([da75726](https://github.com/nsphung/mcp-snowflake-server/commit/da75726e402b5c0aacb4e6650791dd84400acba7))
- Add --exclude-json-results to reduce context window usage ([f5e2022](https://github.com/nsphung/mcp-snowflake-server/commit/f5e2022abba75a49440b5c42995cbcd70517e16f))
- add mypy / tests / test coverage ([58c7e9a](https://github.com/nsphung/mcp-snowflake-server/commit/58c7e9a6c676696f528b0ff8fafc40d50ea4c25f))
- Add release / Tag as 0.5.0 ([31c05aa](https://github.com/nsphung/mcp-snowflake-server/commit/31c05aac7f92b3b0fff77dec05a497756192080e))
- Add ruff / mypy / pre-commit / tests / tests coverage ([2bf6dd8](https://github.com/nsphung/mcp-snowflake-server/commit/2bf6dd805ca072db4baf76c83df9b35de54c836b))
- Add ruff format/lint ([c2d5eba](https://github.com/nsphung/mcp-snowflake-server/commit/c2d5eba20d65b8b454a40901b7683b56cb7d63be))
- Add Snowflake Key Pair Auth ([1ae1b72](https://github.com/nsphung/mcp-snowflake-server/commit/1ae1b72f246283b97d04c64efe9b7caeb04dc0b3))
- Add Snowflake Key Pair Auth ([6e787bf](https://github.com/nsphung/mcp-snowflake-server/commit/6e787bfaf78927e42e6ece0b5853fdec2e103176))
- Conform to LICENCE ([93ab9b2](https://github.com/nsphung/mcp-snowflake-server/commit/93ab9b2a9e9359f8977d06a7330e91ea7693240f))

### Bug Fixes

- remove old gh actions ([a68f554](https://github.com/nsphung/mcp-snowflake-server/commit/a68f5549358b36d71e3461f6f9be82e3db5aa405))

### Documentation

- Add shields ([28dbd04](https://github.com/nsphung/mcp-snowflake-server/commit/28dbd04f60d82d9271125b3cf1a27a21a39365e3))

### Miscellaneous Chores

- release 0.5.0 ([8d1dcd2](https://github.com/nsphung/mcp-snowflake-server/commit/8d1dcd2bbbe05bfa254633e315626d70b4111d8b))
