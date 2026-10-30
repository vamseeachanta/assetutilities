# Changelog

All notable changes to the AssetUtilities project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

<!-- New entries are prepended by scripts/release/cut-release.sh -->

## [Unreleased]

### Units

- Output templates match complete Pint dimensionality using dimension names such
  as `pressure` and `length`. Unit-name keys such as `pascal` and `psi`, and partial
  names, no longer select templates; unmatched quantities use the default format.
  Empty or whitespace-only template names now raise `ValueError` on registration.
