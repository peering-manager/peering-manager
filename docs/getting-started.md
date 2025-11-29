# Getting Started with Peering Manager

This guide will walk you through the essential steps to start using
Peering Manager for managing your BGP peering relationships. We'll cover
the core concepts and guide you through setting up your first peering
sessions.

!!! info "Prerequisites"
    This guide assumes you have already [installed](./setup/index.md) and
    configured Peering Manager. If you haven't done so yet, please follow
    the installation guide first.

## Understanding Core Concepts

Before diving into configuration, it's important to understand the key
concepts in Peering Manager:

### Autonomous Systems (AS)

An autonomous system is a collection of IP networks and routers under the
control of a single organisation that presents a common routing policy to
the Internet. Each AS is identified by a unique number called an ASN
(Autonomous System Number).

In Peering Manager, there are two types of autonomous systems:

* **Affiliated AS**: Your own autonomous system(s) that you manage and
  operate
* **Peering AS**: External autonomous systems that you establish BGP
  sessions with

!!! tip "The Affiliated AS Concept"
    The concept of an **affiliated AS** is fundamental to Peering Manager.
    An affiliated AS represents your organisation's autonomous system(s).
    You must mark your own AS as affiliated by checking the "Affiliated"
    field when creating it. This distinction allows you to have a single
    Peering Manager instance even if your organisation operates multiple ASNs.

### Internet Exchange Points (IXPs)

An Internet Exchange Point (IXP or IX) is a physical infrastructure where
multiple networks connect to exchange traffic directly. IXPs provide a
shared switching fabric that allows participating networks to peer with
each other without requiring individual direct connections.

### Peering Sessions

A BGP peering session is an established connection between two routers for
exchanging routing information. Peering Manager distinguishes between:

* **Internet Exchange Peering Sessions**: BGP sessions established over an
  IXP
* **Direct Peering Sessions**: BGP sessions established over a private
  interconnection (PNI)

### Routers

Routers are the network devices where your BGP sessions are configured. In
Peering Manager, you define your routers and associate them with Internet
exchanges or direct peering sessions.

### Routing Policies and Communities

* **Routing Policies**: Define how you accept or advertise routes
  (import/export rules)
* **BGP Communities**: Tags attached to routes to influence routing
  decisions and track route origin

## Initial Setup Workflow

Let's walk through setting up your first peering configuration step by
step.

### Step 1: Create Your Affiliated Autonomous System

The very first thing you need to do is define your own autonomous system.

1. Navigate to **Autonomous Systems**
2. Click the **Add** button
3. Fill in the details:
    * **ASN**: Your autonomous system number (e.g., `64512`)
    * **Name**: Your organisation name (e.g., `Example Networks`)
    * **Affiliated**: Check this box (this is critical!)
    * **IRR AS-SET**: Your IRR AS-SET if you maintain one (e.g.,
      `AS-EXAMPLE`)
    * **IPv4 Max Prefixes**: Maximum IPv4 prefixes you announce (optional)
    * **IPv6 Max Prefixes**: Maximum IPv6 prefixes you announce (optional)
4. Click **Create**

!!! warning "Don't Forget Affiliated!"
    Always check the "Affiliated" box for your own autonomous system(s).
    This is essential for Peering Manager to function correctly.

### Step 2: Synchronise with PeeringDB (Optional but Recommended)

[PeeringDB](https://peeringdb.com/) is a freely available database that
contains information about networks, Internet exchanges, and facilities.
Peering Manager can synchronise data from PeeringDB to keep your
information up-to-date.

First, synchronise the PeeringDB cache by running the management command:

```bash
python3 manage.py peeringdb_sync
```

Once the cache is populated, you can synchronise individual autonomous
systems:

1. Navigate to **Autonomous Systems**
2. Click on your affiliated AS
3. If your AS exists in PeeringDB, you'll see a **Synchronise** button
4. Click it to pull the latest data from PeeringDB

Re-running the previous command will make sure that the cache remains
up-to-date and it will also synchronise data for known autonomous systems.

### Step 3: Create a Router

Next, define the router(s) where your BGP sessions will be configured.

1. Navigate to **Devices > Routers**
2. Click the **Add** button
3. Fill in the details:
    * **Local Autonomous System**: Select your affiliated AS
    * **Name**: A descriptive name (e.g., `edge-router-01`)
    * **Hostname**: The FQDN or IP address of the router
    * **Platform**: Select the router's operating system from the dropdown
    * **Status**: Set to `Enabled`
4. Click **Create**

!!! tip "Platform Support"
    Make sure to create a Platform first (under **Devices > Platforms**)
    if your router's OS isn't already listed.

### Step 4: Create an Internet Exchange

If you're connected to an IXP, you need to create it in Peering Manager.

1. Navigate to **Internet Exchanges**
2. Click the **Add** button
3. Fill in the details:
    * **Name**: The IXP name (e.g., `AMS-IX` or `DE-CIX Frankfurt`)
    * **Slug**: Auto-generated, URL-friendly identifier
    * **Local Autonomous System**: Select your affiliated AS
    * **Status**: Set to `Enabled`
4. Click **Create**
5. After creation, navigate to the **Connections** tab
6. Click **Add** to create a connection:
    * **Router**: Select the router connected to this IXP
    * **IPv6 Address**: Your IPv6 address on the IXP
    * **IPv4 Address**: Your IPv4 address on the IXP

!!! info "PeeringDB Integration"
    If you already have your IXP connections in PeeringDB, you can simply
    click **Import from PeeringDB**, Peering Manager will take care of
    creating the IXPs and connections for you.

### Step 5: Discover Potential Peers

Now that you have your IXP configured, you can discover potential peering
opportunities:

1. Navigate to your Internet Exchange
2. Click the **Peers** tab
3. Review the list of networks present at the same IXP
4. Identify networks you want to peer with

!!! tip "PeeringDB Data"
    The peer discovery feature requires PeeringDB synchronisation to work.
    Make sure you've run `peeringdb_sync` as described in Step 2.

### Step 6: Add a Peering Autonomous System

Select an external AS that you want to peer with from the discovered peers
or add one manually.

1. Navigate to **Autonomous Systems**
2. Click the **Add** button
3. Fill in the details:
    * **ASN**: The remote peer's ASN (e.g., `15169` for Google)
    * **Name**: The peer's name (e.g., `Google LLC`)
    * **Affiliated**: Leave unchecked (this is not your AS)
    * **IRR AS-SET**: Their IRR AS-SET if known
    * **IPv4 Max Prefixes**: Expected number of IPv4 prefixes
    * **IPv6 Max Prefixes**: Expected number of IPv6 prefixes

!!! tip "Quick Addition from PeeringDB"
    If the AS exists in PeeringDB, you can enter its ASN and Peering
    Manager will auto-populate the fields.

### Step 7: Create a Peering Session

Finally, let's establish a BGP peering session.

**For an Internet Exchange Peering Session:**

1. Navigate to an IXP then click on the **Peering Sessions** tab
2. Click the **Add** button
3. Fill in the details:
    * **Autonomous System**: Select the peer's AS
    * **Connection**: Select the IXP connection to set the source address
    * **IP Address**: The peer's IP address on the IXP
    * **Status**: Set to `Enabled`
    * **Multihop TTL**: Usually `1` for direct peering on an IXP
4. Optionally configure:
    * **Password**: If your peer uses authentication
5. Click **Create**

**For a Direct Peering Session:**

1. Navigate to the AS you want to peer with
2. Click the **Direct Peering Sessions** tab
3. Click the **Add** button
4. Fill in similar details but select a **Router** instead of an Internet
   Exchange
5. Configure the relationship type (e.g., Transit Provider, Customer,
   Private Peering)

## Next Steps

### Configuration Templates

Once you have your routers and sessions defined, you'll want to generate
router configurations:

1. Create a configuration template (see
   [Templating Guide](./templating/index.md))
2. Assign the template to your router
3. Navigate to your router and click the **Configuration** tab to see the
   generated config
4. Optionally use NAPALM integration to push configurations directly to
   devices

### Routing Policies and Communities

Define reusable routing policies and BGP communities:

* Navigate to **Policy Options > Routing Policies** to create import/export
  policies
* Navigate to **Policy Options > Communities** to define BGP communities for
  traffic engineering

### Discovering Peering Opportunities

Peering Manager can help you discover potential peering sessions at your
configured IXPs:

1. Navigate to an Internet Exchange
2. Click the **Available Peers** tab to see all networks present at the IXP
3. Review the list and identify missing peering sessions
4. Select the peer then click the "Add Selected" button

Alternatively, you can view potential peers from an autonomous system's
perspective:

1. Navigate to an autonomous system that's present at the same IXP
2. View the **Available Sessions** tab to see potential sessions
3. Select the sessions then click the "Add Selected" button

### Monitoring and Automation

* **Poll BGP Session States**: Enable polling on routers to track session
  status
* **Webhooks**: Set up webhooks to integrate with other systems
* **REST API**: Use the powerful REST API for automation workflows

## Tips and Best Practices

!!! tip "Start Small"
    Don't try to import your entire network at once. Start with one
    router, one IXP, and a few sessions. Once you're comfortable, expand
    to more infrastructure.

!!! tip "Use Tags"
    Tags are powerful organisational tools. Use them to categorise
    routers, sessions, and ASes (e.g., `production`, `test`,
    `tier1-peer`, etc.).

!!! tip "Leverage PeeringDB"
    Keep your PeeringDB record up-to-date and enable synchronisation in
    Peering Manager. This saves significant manual data entry.

!!! tip "Configuration Context"
    Use the JSON-based configuration context feature for storing
    router-specific or session-specific variables that your templates can
    reference.

!!! warning "Test Configurations First"
    Always review generated configurations before deploying them to
    production routers. Start with manual deployment until you're
    confident in your templates.

## Getting Help

If you need assistance:

* Check the
  [official documentation](https://docs.peering-manager.net/)
* Browse the [templating guide](./templating/index.md)
* Visit the
  [GitHub repository](https://github.com/peering-manager/peering-manager)
  for issues and discussions
* Join the community on [Slack](https://netdev.chat/)

## What's Next?

Now that you understand the basics, you can explore more advanced
features:

* **[REST API](./integrations/rest-api.md)**: Automate Peering Manager
  with the API
* **[Webhooks](./integrations/webhooks.md)**: Integrate with external
  systems
* **[NAPALM Integration](./integrations/napalm.md)**: Deploy
  configurations automatically

Happy peering! :material-web:
