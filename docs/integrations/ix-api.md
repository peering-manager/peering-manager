# IX-API

Coupled with IX-API, Peering Manager can display useful information about your
connections to an IXP such as services provided by the IXP (route servers),
what an IXP knows about your services (such as service IDs) and connections to
the IXP that you already have setup or not. It provides a way to quickly
import a connection found in IX-API to Peering Manager.

An IX-API instance can be linked to one or more IXPs inside Peering Manager.
To do so, an [IX-API object](../models/extras/ixapi.md) must be created inside
the `3rd Party > IX-API` section found on the left side bar. You'll have to
provide the URL, key and secret as well as an identity (once URL, key and
secret are valid) that corresponds to the entity you are representing (e.g.
your company). Once done, you'll have to edit the IXP that you want to use
IX-API with and select the newly created IX-API object from the
`IX-API endpoint` dropdown list. After saving, an `IX-API` tab will appear on
the IXP view.
