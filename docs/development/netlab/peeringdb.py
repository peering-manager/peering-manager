#
# A plugin for PeeringDB - provisions interface IP addresses based on a lookup of the BGP AS
#
import typing, requests, json, netaddr
from box import Box
from netsim import data
from urllib.parse import quote

"""
Adds a custom 'ixp' node attribute
"""
def init(topology: Box) -> None:
  topology.defaults.attributes.node.append('ixp')

"""
Lookup ASN in PeeringDB and return ipv4,ipv6 peering IPs at given IX
"""
def query_peeringdb(asn: int, ix: str) -> typing.Tuple[typing.Optional[str],typing.Optional[str],typing.Optional[str]]:
  url = f"https://peeringdb.com/api/netixlan?asn={asn}&name__contains={quote(ix)}"
  print( f"PeeringDB query: {url}" )
  resp = requests.get(url=url)
  pdb_json = json.loads(resp.text)
  print( pdb_json )
  if 'data' in pdb_json and pdb_json['data']:
    site = pdb_json['data'][0]
    return ( site['name'], site['ipaddr4'], site['ipaddr6'] )
  return ( None, None, None )

"""
Update eBGP peering IP addresses at given IXP site
"""
def post_transform(topology: Box) -> None:

  # Iterate over all IXP nodes, update interface IP addresses based on PeeringDB
  for n, ndata in topology.nodes.items():
    print( f"Processing {n} bgp.neighbors" )
    updated_neighbors = []
    ixp_node = None
    for i in ndata.bgp.neighbors:
      print(i)
      def update_ips(ip,prefix,ipv):
        net = netaddr.IPNetwork( f"{ip}/{prefix}" )
        ixp_ip = str( net[1] )
        ndata.interfaces[i.ifindex-1][ipv] = f"{ixp_ip}/{prefix}"
        for nb in ndata.interfaces[i.ifindex-1].neighbors:
          peer = topology.nodes[ nb.node ]
          if peer.bgp['as'] == i['as']:
            for p in peer.interfaces:
              if n in [ x.node for x in p.neighbors ]:
                p[ipv] = f"{ip}/{prefix}"
                return

      if 'ixp' in ndata:
        (name,ip4,ip6) = query_peeringdb( i['as'], ndata.ixp )
        if name:
          ndata.interfaces[i.ifindex-1].name = name
        if ip4 and 'ipv4' in ndata.af:
          update_ips(ip4,22,'ipv4')    # Assume /22 is large enough
        if ip6 and 'ipv6' in ndata.af:
          update_ips(ip6,64,'ipv6')

        ndata.pop('bgp',None) # Remove BGP peerings from IXP node
        ndata.module = []
      else:
        # Assumes IXP nodes are listed first...update peering IPs
        peer = topology.nodes[ i.name ]
        if 'ixp' in peer:
          ixp_node = i.name
          continue
        for l in peer.interfaces:
          if ixp_node in [ nb.node for nb in l.neighbors ]:
            print( f"Found peering interface with node {ixp_node}: {l}" )
            if 'ipv4' in l and 'ipv4' in i and isinstance(l.ipv4,str):
              i.ipv4 = l.ipv4.split('/')[0]
            if 'ipv6' in l and 'ipv6' in i and isinstance(l.ipv6,str):
              i.ipv6 = l.ipv6.split('/')[0]
            updated_neighbors.append(i)     # Keep only updated ones, remove ixp

    if updated_neighbors:
      ndata.bgp.neighbors = updated_neighbors
