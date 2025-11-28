# Data Sources

A data source represents an external repository of data which Peering
Manager can consume, such as a git repository. Files within the data source
are synchronised by saving them in the database as [data file](./datafile.md)
objects.

## Fields

### Name

The data source's human-friendly name.

### Type

The type of data source. Supported options include:

* Local directory
* Git repository

### URL

The URL identifying the remote source. Some examples are included below.

| Type      | Example URL                                        |
|-----------|----------------------------------------------------|
| Local     | file:///path/to/my/data/                           |
| git       | https://github.com/my-organisation/my-repo         |

### Status

The source's current synchronisation status. Note that this cannot be set
manually: it is updated automatically when the source is synchronised.

### Enabled

If false, synchronisation will be disabled.

### Ignore Rules

A set of rules (one per line) identifying filenames to ignore during
synchronisation. Some examples are provided below. See Python's [`fnmatch()`
documentation](https://docs.python.org/3/library/fnmatch.html) for a complete
reference.

| Rule           | Description                              |
|----------------|------------------------------------------|
| `README`       | Ignore any files named `README`          |
| `*.txt`        | Ignore any files with a `.txt` extension |
| `data???.json` | Ignore e.g. `data123.json`               |

### Last Synchronised

The date and time at which the source was most recently synchronised
successfully.
