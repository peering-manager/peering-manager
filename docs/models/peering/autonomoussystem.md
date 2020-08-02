# Autonomous System

An autonomous system, also known as AS, is a collection of connected Internet
Protocol resources managed by network operators. It represents a single
administrative entity which has clearly identified routing policies.

An AS is defined mainly by its number, called the ASN. It is a 32-bit integer
to each autonomous system. Some numbers are reserved for private use and must
not be routed on the Internet.

## In Peering Manager

Inside Peering Manager, you create autonomous systems that you want to peer
with. Your own ASN number must be provided as a setting called `MY_ASN`. For
each AS that you create, the following properties are to be provided (some are
however optional):

  * `ASN`: a unique autonomous system number of the entity.
  * `Name`: a human readable name attached to an AS.
  * `IRR AS-SET`: one or more words giving other autonomous systems that can be
    found, for a BGP speaker, behind this AS.
  * `IPv6 Max Prefixes`: a zero or positive integer which defines the maximum
    number of IPv6 prefixes to receive from the AS.
  * `IPv4 Max Prefixes`: a zero or positive integer which defines the maximum
    number of IPv4 prefixes to receive from the AS.
  * `Contact Name`: a name for a contact in charge of BGP/peering operations.
  * `Contact Phone`: a phone number to get in touch with the contact.
  * `Contact E-mail`: an e-mail address to get in touch with the contact.
  * `Import Routing Policies`: a list of routing policies to apply when
     receiving prefixes from the AS.
  * `Export Routing Policies`: a list of routing policies to apply when
     advertising prefixes to the AS.
  * `Properties To Synchonize From PeeringDB`: some properties such as the
    name, the IRR AS-SET and prefix limits can be synchronized from the
    AS' [PeeringDB](https://peeringdb.com/) record.
  * `Tags`: a list of tags to help identifying and searching for an AS.
  * `Comments`: some text that can be formatted in Markdown to record some
    notes about the AS.

Note that the best way to keep all of this properties up-to-date is to use the
PeeringDB integration that can synchronize some of them automatically.
