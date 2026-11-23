# Changelog

All notable changes to the AssetUtilities project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

<!-- New entries go under [Unreleased]; cutting a release is described in docs/releasing.md -->

## [Unreleased]

## [0.2.0] - tag `v0.2.0` (pending)

First git-tagged release. Consumers (digitalmodel, worldenergydata) pin this tag
instead of a branch or an untagged commit. The `0.1.1` version string was carried
by many different `main` commits and is not tagged; the minor bump also covers the
behavior change below.

### Units

- Output templates match complete Pint dimensionality using dimension names such
  as `pressure` and `length`. Unit-name keys such as `pascal` and `psi`, and partial
  names, no longer select templates; unmatched quantities use the default format.
  Empty or whitespace-only template names now raise `ValueError` on registration.
