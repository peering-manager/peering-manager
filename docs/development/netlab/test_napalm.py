from napalm import get_network_driver
import json

driver = get_network_driver("sros")
optional_args = {'port': 830}
device = driver("192.168.121.102", "admin", "admin", 60, optional_args)
device.open()
print(device.get_facts())
print(device.get_optics())

# Peering Manager calls get_bgp_neighbors_detail to get peer status
print(json.dumps(device.get_bgp_neighbors_detail(), indent=2))
device.close()
