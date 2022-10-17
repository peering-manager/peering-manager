# Netlab virtual lab topology for testing peering configurations and NAPALM driver interaction

This directory contains a sample [Netlab](https://netsim-tools.readthedocs.io/en/latest/) topology file
to build a virtual lab for testing with Peering Manager

## Instructions
1. [Install Netlab](https://netsim-tools.readthedocs.io/en/latest/install.html)
2. Obtain/build Docker images for your network platforms (some may require a license)
3. Run ```source {netlab path}/setup.sh```
3. Run ```netlab install grpc``` [for Nokia SR OS / SR Linux]
4. Run ```netlab up```

Peering Manager can be attached to the same virtual management network:
docker-compose.override:
```
---
networks:
  default:
    driver: bridge
    external: true
    name: netlab_mgmt
```

The sample SR OS router in this example can be reached at 192.168.121.102, admin/admin
