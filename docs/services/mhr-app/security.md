---
sidebar_position: 3
title: "MHR-App: Security"
description: "Security considerations for MHR-App distributed applications — publisher authentication, content integrity, malicious code, supply chain attacks, and comparison with other frameworks."
keywords: [app security, publisher authentication, content integrity, supply chain, MHR-App]
---

# MHR-App: Security Considerations

## Publisher Authentication

Every AppManifest is signed by the publisher's Ed25519 key. The publisher's identity is verifiable via [MHR-ID](../mhr-id/) claims and vouches. A manifest from an unknown or untrusted publisher triggers a trust warning at install time. Trust scoring follows the same model as [MHR-Name resolution](../mhr-name#resolution-priority).

## Content Integrity

Every component is content-addressed by Blake3 hash — contract code, UI assets, state schema, and the manifest itself. A malicious storage node cannot tamper with any component without changing its hash, which breaks the manifest reference. Verification is automatic and requires no trust in storage providers.

## Malicious Code

MHR-Byte and WASM contracts are fully sandboxed — no I/O, no network, no filesystem access. Malicious contract code cannot escape the compute sandbox. UI code (HTML/JS) is **not sandboxed** by the protocol — it runs in the user's local rendering environment. Mitigations: content-hash verification ensures UI hasn't been tampered with, and trusted publisher vouches via MHR-ID provide social proof of safety.

## Supply Chain Attacks

A compromised publisher key could push a malicious update. Mitigations:
- Old versions remain available by content hash (immutable)
- Key rotation via [MHR-ID](../mhr-id/) revokes the compromised key
- Users can pin to a specific manifest hash (version pinning)
- Publisher key change triggers a warning (like SSH host key warnings)

## Dependency Integrity

Dependencies are resolved by content hash — a dependency on `Blake3(0x1a2b...)` always resolves to the exact same bytes regardless of where it's fetched from. An attacker cannot substitute a malicious dependency without changing the hash, which would break the manifest's dependency list.

## State Poisoning

A malicious node could inject corrupted CRDT state during sync. Mitigations: contracts validate state transitions (invalid state is rejected), CRDT merge semantics are deterministic (invalid state that passes validation merges consistently), and state mutations are signed by the authoring node.

## Comparison with Other Frameworks

| | Mehr | Freenet | Holochain | Ethereum |
|---|---|---|---|---|
| **State model** | CRDT (eventually consistent) | Contracts (per-key replicated) | Agent-centric (source chains) | Global state (blockchain) |
| **Compute** | Explicit, paid, no global state | Implicit in storage ops | Validation functions | Global EVM |
| **Consensus** | None (CRDT convergence) | None (contract logic) | Per-app validation | Global PoS |
| **Storage** | Paid per-duration | Donated | Agent-hosted | On-chain (expensive) |
| **Hardware** | ESP32 to datacenter | Desktop+ | Desktop+ | Full node required |
| **Offline** | Full partition tolerance | Limited | Offline-first | No |
| **App packaging** | AppManifest (content-addressed) | Contract + State (content-addressed) | DNA + UI bundle (hApp) | No standard (dApps are websites) |
| **App discovery** | MHR-Name + trust-weighted | Key-based (must know contract key) | App store / out-of-band | Out-of-band (URLs) |
| **Private local agent** | Node identity + local storage | Delegate (actor model) | Agent (source chain) | Wallet (external) |
| **UI distribution** | DataObjects in MHR-Store | Contract state (WASM-rendered) | Bundled in hApp | Traditional web hosting |
| **Upgrade model** | New manifest + name rebind | New contract key (no migration) | DNA versioning | Contract is immutable |
| **Dependencies** | Content-addressed by hash | Not formalized | Zome composition | Contract composability |

## What Mehr Does NOT Provide

- **No global state machine** — no blockchain, no global consensus. Applications that need "everyone agrees on one truth" must use CRDTs (eventual consistency) or application-level coordination.
- **No automatic code execution at storage nodes** — storage is dumb. A storage node stores bytes and serves them on request. It does not execute contracts on stored data. Compute is always explicit and paid.
- **No contract composability** — contracts don't call other contracts. Each contract is an independent unit of execution. Applications compose at the application layer, not the contract layer. Apps can share contracts via dependencies, but contracts cannot invoke each other at runtime.
- **No transaction atomicity across nodes** — you cannot atomically update state on two different nodes. CRDTs provide eventual consistency, not transactional guarantees.
- **No curated app store** — app discovery is decentralized and trust-weighted. There is no central authority that reviews, approves, or ranks applications. Community curation happens organically through vouches and trust relationships.

These are deliberate: global state and atomic transactions require consensus, which contradicts partition tolerance. Mehr chooses partition tolerance and eventual consistency over global coordination — the right tradeoff for a mesh network where disconnection is normal.

<!-- explanation-start -->

#### Design Decision: No Delegate Concept {#design-decision-no-delegate-concept}

:::note

[Freenet](https://freenet.org) uses a three-component model: **contracts** (public replicated state), **delegates** (private local agents holding secrets), and **UIs** (web frontends). The delegate acts as a local policy enforcer — it holds private keys, manages per-app secrets, and communicates via actor-model message passing.

Mehr does not need a separate delegate concept. The same functionality is covered by existing primitives:

| Freenet Delegate Feature | Mehr Equivalent |
|--------------------------|-----------------|
| Hold private keys | Node's Ed25519 identity + local keystore |
| Per-app secret state | Local node storage (never replicated) |
| Policy enforcement | MHR-Compute contracts running locally |
| Message passing | MHR-Pub subscriptions + direct messages |
| Authorized actions | Contract logic checks `SENDER` opcode |

A Mehr app that needs private state stores it locally on the node — it never enters MHR-Store, is never gossiped, and is never visible to other nodes. Contracts running locally via MHR-Compute have no I/O or network access, providing the same sandboxing guarantees as Freenet delegates. Adding a formal delegate concept would introduce a new abstraction layer with minimal benefit over the existing primitives.

:::

<!-- explanation-end -->
