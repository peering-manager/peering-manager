# HiddenPeer

A HiddenPeer is used to track potential peers to hide from the available peer
list. This can be useful when a potential peer has refused to peer for various
reasons, allowing you to hide them so they won't appear in the available peer
list for a given IXP anymore.

## In Peering Manager

Inside Peering Manager, you create HiddenPeer records to exclude specific
networks from appearing as available peers on a particular Internet exchange
point LAN. A peer matching a HiddenPeer record will be hidden indefinitely
unless the record is deleted or the record's until timestamp is in the past.

* `Autonomous System`: the network (AS) to hide from the available peer list.
* `Internet Exchange LAN`: the specific IXP LAN where this network should be
  hidden.
* `Hide until`: optional date and time after which this record will expire. If
  left blank, the network will be hidden indefinitely. Expired records remain
  in the database until manually deleted.
* `Comments`: free text to document the reason for hiding this peer or any
  other relevant details.

## Notes

* A network can only be hidden once per IXP LAN.
* Expired HiddenPeer records (where until is in the past) will no longer hide
  the peer, but the record will remain until manually deleted.
