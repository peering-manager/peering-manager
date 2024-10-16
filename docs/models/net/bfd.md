# BFD (Bidirectional Forwarding Detection)

BFD is a network protocol designed to provide rapid detection of failures in
the forwarding path between two devices. It operates independently of the
underlying transport protocol and provides low-latency failure detection. It
is lightweight and allows the network to react quickly to failures, improving
convergence times for protocols like BGP and others.

BFD establishes a session between two devices, monitoring the liveness of a
specific path. Each device exchanges BFD control packets at defined intervals
(transmit and receive intervals). If a failure is detected, BFD immediately
notifies higher-layer protocols (like BGP), which can quickly reroute traffic.

## Key Configuration Parameters

* Minimum TX Interval: the minimum interval in milliseconds between BFD
  control packets sent by a device. This defines how frequently packets are
  transmitted.
* Minimum RX Interval: the minimum interval in milliseconds that a device
  expects to receive BFD control packets from its peer.
* Detection Multiplier: the number of consecutive missed BFD control packets
  required to declare the session down.
* Hold time: the time to wait before declaring a session down if the detection
  multiplier threshold has been reached.

Like multi-hop BGP, BFD can also operates in a multi-hop mode when the peer is
multiple hops away.

## Typical BFD Values:

* Minimum TX Interval: 300ms
* Minimum RX Interval: 300ms
* Detection Multiplier: 3 (meaning the session is considered down after 3
  missed packets)

## Usage

Create a BFD configuration object with wanted values. Set the BFD
configuration to use when creating or editing a BGP session (IXP or direct).
