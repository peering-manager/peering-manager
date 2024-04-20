# Synchronised Data

Some Peering Manager models support automatic synchronisation of certain
attributes from remote [data sources](../models/core/datasource.md), such as a
git repository . Data from the authoritative remote source is synchronised
locally in Peering Manager as [data files](../models/core/datafile.md).

!!! note "Permissions"
    A user must be assigned the
    `core | data source | Can synchronise data source` permission in order to
    synchronise local files from a remote data source.

!!! note "GitHub Authentication"
    For private git repositories hosted on GitHub, [personal access tokens][1]
    can be used to perform authentication. A personal access token should be
    set into the password field when creating/editing a data source.

The following features support the use of synchronised data:

* [Configuration and e-mail templates](../templating/index.md)
* [Configuration context data](../models/extras/configcontext.md)
* [Export templates](../models/extras/exporttemplate.md)

Device configuration supports retrieving template via a data source, but it
also supports committing and pushing a rendered configuration to a data
source.

A convenient CLI command called `datasource` is provided to synchronise data
sources regularly. It takes a `--all` to synchronise all known data sources or
the individual names of each data source to synchronise, space delimited.

[1]: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
