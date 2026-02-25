---
sidebar_position: 4
title: Naming
---

# Naming (MHR-Name)

MHR-Name provides human-readable names scoped to community labels. There is no global namespace — names resolve locally based on proximity and trust.

## Community-Scoped Names

Names follow the format `name@community-label`:

```
maryam@tehran-mesh
alice@portland-mesh
relay-7@backbone-west
```

Resolution works by proximity:

1. Parse the community label from the name (`portland-mesh`)
2. Search nearby nodes with that `community_label` set
3. Within that cluster, resolve the name via local naming records
4. Use the returned NodeID for routing

## Why No Global Namespace?

A global namespace requires global consensus on name ownership. Global consensus contradicts Mehr's partition tolerance requirement. If two partitioned networks both register the name "alice," there is no partition-safe way to resolve the conflict.

Community-scoped names solve this:
- Names are locally consistent within their trust neighborhood
- Different communities can have different "alice" users — they are `alice@portland-mesh` and `alice@tehran-mesh`
- No global coordination needed
- Community labels are self-assigned, not centrally managed

## Name Registration

Names are registered locally by announcing a name binding:

```
NameBinding {
    name: String,               // "alice"
    community_label: String,    // "portland-mesh"
    node_id: NodeID,
    signature: Ed25519Signature,
}
```

Name bindings propagate via gossip within the trust neighborhood. Conflicts (two nodes claiming the same name in the same community label) are resolved by precedence:

1. **Trust-weighted** (highest priority) — if one claimant is in your trust graph and the other is not, the trusted claimant wins regardless of timing. Between two trusted claimants, the one with the shorter trust distance wins.
2. **First-seen** (tiebreaker) — if both claimants have equal trust status (both trusted at the same distance, or both untrusted), the first binding your node received wins.
3. **Local petnames** (ultimate fallback) — if you need guaranteed resolution regardless of conflicts, assign a local petname (see below). Petnames override all network name resolution.

## Cross-Community Resolution

To resolve a name in a different community:

1. Query propagates toward nodes with the target community label
2. Nearest matching cluster responds with the name binding
3. Result is cached locally with a TTL

Because community labels are not unique, resolution finds the **nearest** cluster with that label. This is usually what you want — `alice@portland-mesh` resolves to the Portland cluster nearest to you.

## Local Petnames

As a fallback and privacy feature, each user can assign **petnames** — local nicknames for NodeIDs on their own device:

```
User's petname mapping (local only, never shared):
  "Mom"    → 0x3a7f...b2c1
  "Work"   → 0x8e2d...f4a9
  "Doctor" → 0x1b5c...d3e7
```

Petnames are:
- Completely private (stored only on the user's device)
- Not resolvable by anyone else
- Useful when community names aren't available or desired
- The most censorship-resistant naming possible — no one can take your petnames from you
