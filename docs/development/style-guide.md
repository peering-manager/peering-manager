# Style Guide

Peering Manager uses `black` combined with `isort` to enforce coding style.

## Enforcing Code Style

The `black` and `isort` utilities are used by the CI process to enforce code
style. It is strongly recommended to include as part of your commit process.

## Introducing New Dependencies

The introduction of a new dependency is best avoided unless it is absolutely
necessary. For small features, it's generally preferable to replicate
functionality rather than to introduce reliance on an external project. This
reduces both the burden of tracking new releases and the exposure to outside
bugs and attacks.

If there's a strong case for introducing a new dependency, it must meet the
following criteria:

* Its complete source code must be published and freely accessible without
  registration
* Its license must be conducive to inclusion in an open source project
* It must be actively maintained
* It must be available via the [Python Package Index](https://pypi.org/)

When adding a new dependency, a line specifying the package name pinned to the
current stable release must be added to `requirements.txt`. This ensures that
`pip` will install the known-good release and simplify support efforts.