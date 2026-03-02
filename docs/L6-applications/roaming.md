---
sidebar_position: 10
title: Roaming & Connectivity
description: "Seamless roaming across WiFi, LoRa, cellular, and other transports using cryptographic identity instead of network addresses."
keywords:
  - roaming
  - connectivity
  - transport switching
  - multi-interface
  - mobility
  - handoff
---

# Roaming & Connectivity

On the traditional internet, switching networks is disruptive — you change WiFi, your connections drop; you move between cells, there's a handoff delay; you plug into a different ethernet port, your IP changes. On Mehr, **your identity is your cryptographic key, not your network address.** Moving between transports, locations, and access points is seamless.

:::info[App Manifest]
Roaming is packaged as a **Headless** (compute only) [AppManifest](/docs/L5-services/mhr-app). It composes MHR-Pub for announce-based presence and transport change notifications, MHR-DHT for route discovery across transport boundaries, and MHR-Compute for link-quality scoring and handoff priority logic. No UI bundle is needed — the roaming service runs as a background daemon that other applications depend on for seamless transport switching.
:::

## How Roaming Works

Mehr's transport layer handles multiple interfaces simultaneously and routes through whichever is best. Your identity doesn't change when your network connection does:

```mermaid
flowchart LR
    A["Home WiFi\n100 Mbps\nFull media"] -->|walk| B["LoRa only\nText only"]
    B -->|arrive| C["Café WiFi\n50 Mbps\nFull media"]
    C -->|walk| D["LTE-M\nModerate"]
    ID(["Your identity: same key throughout"]) -.-> A
    ID -.-> B
    ID -.-> C
    ID -.-> D
    style ID fill:none,stroke:none,color:#666
```

**Key properties:**

- **Identity is transport-independent.** Your NodeID (Ed25519 public key) stays the same regardless of which radio, WiFi, or ethernet port you're using. Nobody needs to "re-discover" you.
- **Announce-based routing adapts automatically.** When you connect to a new access point, your node sends an announce. Nearby nodes update their routing tables within seconds. Traffic starts flowing through the new path.
- **Applications adapt to link quality.** When you switch from WiFi to LoRa, apps detect the bandwidth change and adjust — images become blurhash previews, video pauses, voice degrades to push-to-talk. When you reach WiFi again, full quality resumes.
- **No session state on the network.** There are no "sessions" to transfer between access points. Your node is an endpoint, not a session on someone else's server. Moving between mesh nodes doesn't require session migration.

## Ethernet Roaming

Plug your device into any ethernet port on the mesh and you're connected — no IP configuration, no DHCP negotiation, no VPN. Your Mehr identity authenticates you, and traffic routes through the mesh.

```
Ethernet roaming scenario:

  Building A                          Building B
  ──────────                          ──────────
  [Ethernet port] ──mesh──▶          [Ethernet port] ──mesh──▶
       │                                   │
  Plug in laptop                      Unplug, walk over,
  → announce sent                     plug in again
  → routes established                → new announce
  → online in <1 sec                  → routes update
                                      → online in <1 sec

  Same identity, same conversations, same files.
  No reconfiguration. No VPN reconnect. No IT ticket.
```

**Use cases:**

| Scenario | How It Works |
|----------|-------------|
| **Office building** | Ethernet ports on every floor. Move between desks — plug in anywhere |
| **Campus** | Multiple buildings, each with mesh nodes. Walk between them, stay connected |
| **Co-working space** | Gateway operator provides ethernet access, bills via fiat subscription |
| **Manufacturing floor** | Fixed ethernet connections at workstations. Workers roam between stations |
| **Home** | Multiple rooms with ethernet drops. Devices plug in wherever convenient |

### Gateway-Provided Ethernet

[Gateway operators](/docs/L3-economics/token-economics#gateway-operators-fiat-onramp) can deploy ethernet access points as part of their service. A co-working space, hotel, or campus deploys mesh-connected ethernet ports. Customers (gateway subscribers) plug in and have immediate access — the gateway handles authentication via its trusted peer relationship.

```
Gateway ethernet access:

  Customer signs up with gateway (fiat subscription)
    → gateway adds customer to trusted_peers
    → customer plugs into any gateway ethernet port
    → traffic routes through gateway (free for trusted peer)
    → gateway handles MHR costs for onward relay
    → customer experiences: "plug in, works"
```

## WiFi Roaming

WiFi roaming works the same way — your device automatically discovers and connects to nearby mesh WiFi nodes:

```mermaid
flowchart LR
    H["Home AP"] -->|walk| C["Café AP"]
    C -->|walk| L["Library AP"]
    H -.-|announce| H2(["routes set"])
    C -.-|announce| C2(["routes update"])
    L -.-|announce| L2(["routes update"])
    style H2 fill:none,stroke:none
    style C2 fill:none,stroke:none
    style L2 fill:none,stroke:none
```

The transition between WiFi access points takes under a second — the time for an announce to propagate and routes to update. Active connections (messaging, voice) continue without interruption because they're addressed to your NodeID, not to a network address.

## Multi-Transport Handoff

Mehr nodes can have multiple active interfaces. When one interface drops, traffic shifts to the next best option:

```
Handoff priority (configurable per node):

  1. Ethernet (if available) — highest bandwidth, lowest latency
  2. WiFi (if in range) — high bandwidth
  3. LTE/LTE-M (if available) — wide coverage
  4. LoRa (always available in mesh) — fallback, low bandwidth

When WiFi drops:
  → Traffic shifts to next available transport (<1 sec)
  → Applications adapt to new bandwidth
  → No connection reset, no re-authentication
```

### Voice Call Handoff

Voice calls demonstrate seamless handoff:

```mermaid
stateDiagram-v2
    [*] --> WiFi_Home: Start call\n16 kbps Opus
    WiFi_Home --> LoRa: Walk out of range
    LoRa --> WiFi_Dest: Arrive at destination
    WiFi_Dest --> [*]: Call ends

    WiFi_Home: WiFi (High Quality)
    LoRa: LoRa (2.4 kbps Codec2)
    WiFi_Dest: WiFi (16 kbps Opus)

    note right of LoRa: Handoff < 1 second\nCall never drops
```

The call never drops. Quality adapts. Interruption during handoff: < 1 second.

## How Announce-Based Routing Enables Roaming

The transport layer's announce mechanism is what makes all of this work. Every Mehr node periodically broadcasts its identity and routing information:

```
Roaming via announces:

  1. Node arrives at new location (plugs in, enters WiFi range, etc.)
  2. Node sends announce on new interface:
       [NodeID] [MehrExtension] [routing info]
  3. Nearby nodes update routing tables:
       "Node X is now reachable via this interface at this cost"
  4. Traffic destined for Node X takes the new path
  5. Old paths age out (no traffic = removed from routing table)

Time from connection to routable: <1 second (announce propagation)
```

No central mobility controller. No IP address reassignment. No DHCP. No DNS update. The announce is the only message needed — everything else follows from distributed routing.

## Comparison

| | Traditional Networking | Mehr Roaming |
|---|---|---|
| **Identity** | IP address (changes with network) | Cryptographic key (permanent) |
| **Switch networks** | Connections drop, reconnect needed | Seamless, sub-second handoff |
| **Multi-transport** | Manual (WiFi or cellular, rarely both) | Automatic, simultaneous interfaces |
| **Authentication** | Per-network (passwords, certificates) | Identity key (universal) |
| **Configuration** | DHCP, DNS, proxy settings | None — announce-based discovery |
| **Ethernet roaming** | Requires enterprise 802.1X, VLAN config | Plug in anywhere, works immediately |
| **Voice handoff** | Cellular does this; WiFi calling is fragile | Seamless across all transports |
| **Works without internet** | No | Yes — mesh routing is local |
