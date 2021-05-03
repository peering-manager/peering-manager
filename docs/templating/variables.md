# Variables

Peering Manager provides a set of pre-defined variables depending on the type
of the template that you are writing. These variables holds data that
represents what is inside the database. As such, some variables are exposed as
SQL query results packed into Python objects allowing easy data processing and
consumption.

It is important to understand that most of the data in these variables is
**not** plain text and sometimes requires processing. Please refer to the
provided [Jinja2 filters](filters.md) to know what logics are already
available to you.

If you have troubles fetching or parsing data, even by using additional Jinja2
filters, please share them in an issue so they can be addressed.

## Configuration

When parsing a template to create a configuration, Peering Manager will use
the following variables and replace references to them by their values when
rendering the actual configuration.

The router, for which you are creating the configuration for, is the centre
piece of the puzzle. Every data will be fetched starting from the router
itself. If you want to have data regarding the router, it is exposed through
the `router` variable. For instance, to print the hostname of the router, you
can use `{{ router.hostname }}`.

To avoid having complex data fetching functions, the following variables
expose objects linked to the router either directly or not.

* `autonomous_systems`: holds remote autonomous systems, in a list-like
  object, that have at least one BGP session with the router. You can use
  filters like `iterate` to walk through the list.
* `bgp_groups`: holds BGP groups, in a list-like object, that can be setup on
  the router based on direct peering sessions to be configured. You can use
  filters like `iterate` to walk through the list.
* `communities`: holds **all** recorded communities in a list-like object. You
  can use filters like `iterate` to walk through the list.
* `internet_exchanges`: holds IXPs connected on the router in a list-like
  object. You can use filters like `iterate` to walk through the list.
* `local_as`: holds local autonomous system details that the router is
  belonging to. A router is always attached to an affiliated AS. This variable
  is an object and data can be fetch using the variable name and a field name
  separated by a dot like `{{ local_as.asn }}`.
* `routing_policies`: holds **all** recorded routing policies in a list-like
  object. You can use filters like `iterate` to walk through the list.

## Email