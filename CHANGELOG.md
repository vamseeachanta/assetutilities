# Changelog

All notable changes to the AssetUtilities project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

<!-- New entries are prepended by scripts/release/cut-release.sh -->

## [Unreleased]

### Changed

- YAML placeholders now resolve scalar mapping lookups only. Jinja filters,
  control blocks, expressions and non-scalar substitutions remain literal.
  Compute these values before passing the configuration to the engine.
- Logging setup writes human-readable run logs, routes stdlib records into
  loguru without reverse propagation, and requires stdlib-recognized levels.
  JSON readers, named stdlib capture handlers and configurations using `TRACE`
  or `SUCCESS` need the migration steps in `docs/logging_loguru_migration.md`.
- Several incidental workflow-class re-exports and `de` and `fm` singleton instances
  were removed from `assetutilities.engine`. Import classes from their
  implementation modules and instantiate them explicitly.

### Fixed

- Concurrent workflow configuration tolerates another worker creating the log
  directory between observation and creation.
- YAML splitting accepts spaces, Unicode and integer keys while rejecting path
  separators and `..`; generated text is UTF-8 with LF line endings and no BOM.
- A null `yaml_options` value leaves placeholder resolution disabled.
