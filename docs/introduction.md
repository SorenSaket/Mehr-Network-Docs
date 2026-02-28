---
sidebar_position: 1
slug: /introduction
title: Introduction
---

import StackDiagram from '@site/src/components/StackDiagram';

# Mehr Network

**Decentralized Mesh Infrastructure Powered by Proof of Service**

Proof of work wastes electricity. Proof of stake rewards capital, not contribution. Mehr uses **proof of service** — a token is minted only when a real service is delivered to a real paying client through a funded payment channel. Relay a packet, store a block, run a computation — that's how MHR enters circulation. No work is wasted. No token is unearned.

Mehr is a decentralized network where every resource — bandwidth, compute, storage, connectivity — is a discoverable, negotiable, verifiable, payable capability. Nodes participate at whatever level their hardware allows. Nothing is required except a cryptographic keypair.

## What Makes Mehr Different

### Proof of Service

Most decentralized networks create tokens through artificial work (hashing) or capital lockup (staking). Mehr mints tokens only when a provider delivers a real service — relaying traffic, storing data, or executing computations — to a client who pays through a funded payment channel. Minting is proportional to real economic activity and capped at 50% of net service income. A 2% burn on every payment creates a deflationary counterforce that keeps supply bounded.

### Zero Trust Economics

The economic layer assumes every participant is adversarial. Two mechanisms make cheating structurally unprofitable in connected networks: **non-deterministic service assignment** (the client can't choose who serves the request) and a **net-income revenue cap** (cycling MHR produces zero minting). In isolated partitions, active-set-scaled emission and the service burn bound damage to a finite equilibrium. No staking, no slashing, no trust scores required.

### Free Between Friends

Communication within your trust network is free — no tokens, no channels, no economic overhead. A local mesh where everyone trusts each other operates at zero cost. The economic layer only activates when traffic crosses trust boundaries. This mirrors how communities actually work: you help your neighbors for free, but charge strangers for using your infrastructure.

### Self-Sovereign Identity

Your identity is your cryptographic key — not an account on someone else's server. [MHR-ID](services/mhr-id) lets you build a rich profile (name, bio, avatar, linked accounts, achievements) where every field is a signed claim that peers can vouch for or dispute. You control who sees each field: public, trusted friends only, friends-of-friends, or specific people. Geographic presence is verified by radio range proofs; external accounts are verified by [FUTO ID-style](https://docs.polycentric.io/futo-id/) crawler and OAuth challenges. No central identity provider. No data broker.

### Subjective Naming

There is no global DNS. [MHR-Name](services/mhr-name) provides human-readable names (`alice@geo:portland`, `my-blog@topic:tech`) that resolve from each viewer's position in the trust graph. Names registered by people you trust outrank names from strangers. Two communities can have different "alice" users — that's by design. Names can point to people, content, or [distributed applications](services/distributed-apps).

### Distributed Applications

Applications on Mehr are not hosted on servers — they are [content-addressed packages](services/distributed-apps) stored in the mesh. An AppManifest bundles contract code, UI, state schema, and dependencies into a single installable artifact. Users discover apps by name, install them locally, and upgrade via trust-weighted update propagation. No app store. No platform fee. No single point of removal.

## Vision

### Strengthen Communities

The internet was supposed to connect people. Instead, it routed everything through distant data centers owned by a handful of corporations. Mehr reverses this: communication within a community is **free, direct, and unstoppable**. Trusted neighbors relay for each other at zero cost. The economic layer only activates when traffic crosses trust boundaries — just like the real world.

### Democratize Communication

A village with no ISP should still be able to communicate. A country under internet shutdown should still have a mesh. A community that can't afford $30/month per household should be able to share one uplink across a neighborhood. Mehr makes communication infrastructure a commons, not a product.

### One Decentralized Computer

Every device on the network — from a $30 solar relay to a GPU workstation — contributes what it can. Storage, compute, bandwidth, and connectivity are pooled into a single capability marketplace. Your phone delegates AI inference to a neighbor's GPU. Your Raspberry Pi stores data for the mesh. No single point of failure, no single point of control. The network **is** the computer.

### Share Hardware, Save Money

Most hardware sits idle most of the time. A home internet connection averages less than 5% utilization. A desktop GPU sits unused 22 hours a day. Mehr turns idle capacity into shared infrastructure: you earn when others use your resources, and you pay when you use theirs. The result is that communities need far less total hardware to achieve the same capabilities.

## Why Mehr?

The internet depends on centralized infrastructure: ISPs, cloud providers, DNS registrars, certificate authorities. When any of these fail — through censorship, natural disaster, or economic exclusion — people lose connectivity entirely.

Mehr is designed for a world where:

- A village with no internet can still communicate internally over LoRa radio
- A country with internet shutdowns can maintain mesh connectivity between citizens
- A community can run its own local network and bridge to the wider internet through any available uplink
- Every device — from a $30 solar-powered relay to a GPU workstation — contributes what it can and pays for what it needs

## Core Principles

### 1. Transport Agnostic

Any medium that can move bytes is a valid link. The protocol never assumes IP, TCP, or any specific transport. It works from 500 bps radio to 10 Gbps fiber. A single node can bridge between multiple transports simultaneously.

### 2. Capability Agnostic

Nodes are not classified into fixed roles. A node advertises what it can do. What it cannot do, it delegates to a neighbor and pays for the service. Hardware determines capability; the market determines role.

### 3. Partition Tolerant

Network fragmentation is not an error state — it is expected operation. A village on LoRa **is** a partition. A country with internet cut **is** a partition. Every protocol layer functions correctly during partitions and converges correctly when partitions heal.

### 4. Anonymous by Default

Packets carry no source address. A relay node knows which neighbor handed it a packet, but not whether that neighbor originated it or is relaying it from someone else. Identity is a cryptographic keypair — not a name, not an IP address, not an account. [Human-readable names](services/mhr-name) are optional and trust-scoped. [Profile fields](services/mhr-id#profile-fields) have per-field [visibility controls](services/mhr-id#visibility-controls) — you decide what to reveal and to whom. You can use the network, earn MHR, host content, and communicate without ever revealing who you are.

### 5. Free Local, Paid Routed

Direct neighbors communicate for free. You pay only when your packets traverse other people's infrastructure. This mirrors real-world economics — talking to your neighbor costs nothing, sending a letter across the country does.

### 6. Layered Separation

Each layer depends only on the layer below it. Applications never touch transport details. Payment never touches routing internals. Security is not bolted on — it is structural.

## Protocol Stack Overview

Mehr is organized into seven layers, each building on the one below. Click any layer to read its full specification.

<StackDiagram />

## How It Works — A Simple Example

1. **Alice** has a Raspberry Pi with a LoRa radio and WiFi. She's in a rural area with no internet. She's registered as `alice@geo:us/oregon/bend` and her profile shows her bio, avatar, and a verified GitHub link.
2. **Bob** has a gateway node 5 km away with a cellular modem providing internet access. He's Alice's trusted peer — they relay for each other for free.
3. **Carol** is somewhere on the internet and wants to message Alice.

Here's what happens:

- Carol looks up `alice@geo:us/oregon/bend` — the name resolves to Alice's node via trust-weighted resolution
- Carol's message is encrypted end-to-end for Alice's public key
- It routes through the internet to Bob's gateway
- Bob relays it over LoRa to Alice (free, because Alice is his trusted peer)
- Alice's device decrypts and displays the message
- Carol's relay cost to reach Bob's gateway is paid automatically through a bilateral payment channel

Carol can see Alice's public profile fields (bio, avatar, verified GitHub) but not her phone number — Alice set that to DirectTrust visibility, so only her trusted peers can see it.

No central server. No accounts. No subscriptions. Just cryptographic identities, trust-weighted naming, and a marketplace for capabilities.

## Next Steps

- **Understand the protocol**: Start with [Physical Transport](protocol/physical-transport) and work up the stack
- **Explore the economics**: Learn how [MHR tokens](economics/mhr-token) and [stochastic relay rewards](economics/payment-channels) enable decentralized resource markets
- **Identity and naming**: See how [MHR-ID](services/mhr-id) builds self-sovereign profiles and how [MHR-Name](services/mhr-name) provides trust-weighted naming
- **Distributed apps**: Learn how [AppManifests](services/distributed-apps) package and distribute applications across the mesh
- **See the real-world impact**: Understand [how Mehr affects existing economics](economics/real-world-impact) and how participants earn
- **See the hardware**: Check out the [reference designs](hardware/reference-designs) for building Mehr nodes
- **Read the full spec**: The complete [protocol specification](specification) covers every detail
