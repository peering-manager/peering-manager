# Export Template

Export templates are meant to export data found within Peering Manager
database as a text based format.

Each export template is attributed an object type. For instance, an export
template linked to autonomous systems will be generally used to create a text
block that will contain some or all details about autonomous systems.

Only one variable named `dataset` is exposed. It contains all the objects (of
the selected type) as an iterable structure.

The template itself leverages the Jinja2 syntax the same way configurations
and e-mails do. Therefore Jinja2 filters and extensions (if configured) can be
used in export templates. For instance, an export template for autonomous
systems can look like:


```jinja2
autonomous_systems:
{% for autonomous_system in dataset | filter(irr_as_set__isnull=False) %}
- {{ autonomous_system.asn }}
{% endfor %}
```

This template will export all ASNs with an IRR AS-SET defined.

```jinja2
#! /usr/bin/env bash

CURL_OPTS='--silent'
TMP_FILE="/tmp/librenms_bgp_sessions_$(date --utc +%s).json"

curl ${CURL_OPTS} --header "X-Auth-Token: ${LIBRENMS_TOKEN}" \
  "https://nms.kviknet.dk/api/v0/bgp" > ${TMP_FILE}

{%- for session in dataset %}

device_information=$(
  cat ${TMP_FILE} | \
  jq '.bgp_sessions[] | select(.bgpPeerRemoteAs=={{ session.autonomous_system.asn }}) | select(.bgpPeerIdentifier=="{{ session.ip_address }}")'
)

session_id=$(
  echo "${device_information}" | jq '.bgpPeer_id'
)

if [ $(echo -n ${session_id} | wc -l) ]; then

  device_id=$(
    echo "${device_information}" | jq '.device_id'
  )

  local_address=$(
    echo "${device_information}" | jq '.bgpLocalAddr' | sed -e 's/"//g'
  )

  bgp_description=$(echo -n "IXP Peering: AS{{ session.autonomous_system.asn }} - {{ session.autonomous_system.name | safe_string }} - Peering Manager Session ID: {{ session.id }} - LibreNMS Device ID: ${device_id} - Local Device Address: ${local_address}{% if session.service_reference %} - Service Reference: {{ session.service_reference | safe_string }}{% endif %}")

  curl ${CURL_OPTS} --header "X-Auth-Token: ${LIBRENMS_TOKEN}" \
  --data "{
    \"bgp_descr\": \"$(echo -n ${bgp_description})\"
  }" \
  "https://nms.kviknet.dk/api/v0/bgp/${session_id}"

fi

{%- endfor %}
```

Will generate a complete bash shell script that can be run to update BGP Peer
descriptions in LibreNMS. The script assumes the LibreNMS token is provided as
an environment variable, `LIBRENMS_TOKEN`. Peering Manager Object Type used for
this template is `peering | internet exchange peering session`. Assumes `jq`,
and `curl` are installed on the system. ([community.librenms.org][0],
[github.com][1]).

[0]: https://community.librenms.org/t/bgp-peer-description-on-routing-page-complete/3337
[1]: https://github.com/librenms/librenms/pull/9165
