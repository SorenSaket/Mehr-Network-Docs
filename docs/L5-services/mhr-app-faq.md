---
sidebar_position: 4
title: "MHR-App: FAQ"
description: "Frequently asked questions about MHR-App distributed applications."
keywords: [MHR-App, FAQ, distributed applications, mesh apps]
pdf: false
---

# MHR-App: Frequently Asked Questions

<details>
<summary><strong>How is an "app" different from a smart contract?</strong></summary>

A Mehr app is a **composition** of primitives — state (CRDTs in MHR-Store), logic (contracts in MHR-Compute), events (MHR-Pub), identity, and discovery. A smart contract is just the logic piece. An app bundles everything needed to run into a single installable [AppManifest](./mhr-app#appmanifest), including UI, state schema, event topics, and dependencies.

</details>

<details>
<summary><strong>Can apps call each other's contracts?</strong></summary>

No. Contracts are independent execution units — they cannot invoke each other at runtime. Apps **compose at the application layer**: an app can depend on another app's contract code (shared via content-addressed hashes in the dependency list), but the calling app runs the contract locally. There is no cross-contract call stack.

</details>

<details>
<summary><strong>What happens if an app publisher disappears?</strong></summary>

The app continues to work. AppManifests, contracts, and state are all **content-addressed and immutable** — they don't depend on the publisher being online. Users who have installed the app keep their local copy. Other nodes can serve the app's artifacts from MHR-Store. The only thing that stops working is **upgrades** — no new versions will be published. Users can fork the app by publishing a new manifest referencing the same contracts.

</details>

<details>
<summary><strong>Why not use a delegate/agent model like Freenet or Holochain?</strong></summary>

Mehr's existing primitives already cover the delegate's responsibilities: the node's Ed25519 identity handles keys, local node storage handles secrets, MHR-Compute contracts handle policy enforcement, and MHR-Pub handles message passing. Adding a formal delegate concept would create a new abstraction layer with minimal benefit. See the [design decision](./mhr-app-security#design-decision-no-delegate-concept) for details.

</details>

<details>
<summary><strong>Can I run an app on an ESP32?</strong></summary>

Yes, if the app uses MHR-Byte contracts (compute_tier=1). MHR-Byte is Mehr's stack-based VM designed for constrained devices. Apps requiring WASM need at least a Community-tier device (Raspberry Pi Zero 2W or equivalent). If your device is underpowered, you can delegate contract execution to a more capable node via the [capability marketplace](/docs/L4-marketplace/overview).

</details>

<details>
<summary><strong>How do app upgrades work across partitions?</strong></summary>

A partitioned node that missed an upgrade continues running the old version. On reconnection, CRDT state merges normally if the schema is compatible. If the schema change is breaking, the node detects the version mismatch during sync, fetches the new manifest via MHR-Name, and runs the migration contract locally. State then converges. See [Partition Behavior](./mhr-app-upgrades#partition-behavior) for details.

</details>

<details>
<summary><strong>Is there an app store?</strong></summary>

Not a centralized one. App discovery is decentralized and trust-weighted. Subscribe to `Scope(Topic("apps"), Prefix)` via MHR-Pub to receive announcements of new apps. Apps from trusted publishers rank higher in resolution. There is no central authority that reviews, approves, or ranks applications — community curation happens organically through vouches and trust relationships.

</details>

<details>
<summary><strong>What if a schema migration fails?</strong></summary>

All migration failures are recoverable. If the migration contract aborts, times out, or produces invalid output, the old app version remains functional. There is no automatic rollback — users keep using the old version, and the publisher can release a fix. See [Migration Contract Execution Semantics](./mhr-app-upgrades#migration-contract-execution-semantics) for the full failure mode list.

</details>
