# Release Engineering

## Minor Version Bumps

### Address Pinned Dependencies

Check `requirements.txt` for any dependencies pinned to a specific version,
upgrade them to their most stable release (where possible).

### Update Static Libraries

Update the following static libraries to their most recent stable release:

* Bootstrap 4
* Font Awesome Icons
* Select2
* jQuery

---

## All Releases

### Update Requirements

Every release should refresh `requirements.txt` so that it lists the most
recent stable release of each package. To do this:

1. Create a new virtual environment
2. Install the latest version of all required packages
  `pip install -U -r requirements.txt`
3. Run all tests and check that the UI and API function as expected
4. Review each requirement's release notes for any breaking or otherwise
  noteworthy changes
5. Update the package versions in `requirements.txt` as appropriate.

In cases where upgrading a dependency to its most recent release is breaking,
it should be pinned to its current minor version in `requirements.txt` (with
an explanatory comment) and revisited for the next major release.

### Verify CI Build Status

Ensure that continuous integration testing on the `main` branch is completing
successfully.

### Update Version and Changelog

* Update the `VERSION` constant in `settings.py` to the new release version.
* List all changes of the version inside `CHANGELOG.md` making sections for
important features and changes.

Commit these changes to the `main` branch.

### Create a New Release

Draft a
[new release](https://github.com/peering-manager/peering-manager/releases/new)
with the following parameters.

* **Tag:** Current version (e.g. `v2.4.4`)
* **Target:** `main`
* **Title:** Version and nickname (e.g. `Version 1.4.4 | MARK I`)

Copy the description from the pull request to the release.

### Update the Development Version

On the `main` branch, update `VERSION` in `settings.py` to point to the next
release. For example, if you just released v1.4.4, set:

```
VERSION = "v1.4.5-dev"
```