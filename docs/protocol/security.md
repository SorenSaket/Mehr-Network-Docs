---
sidebar_position: 3
title: "Security"
description: Security layer of the Mehr Network — end-to-end encryption, X25519 key exchange, forward secrecy, and threat model analysis.
keywords: [security, encryption, E2EE, key exchange, threat model]
---

# Layer 2: Security

Security in Mehr is structural, not bolted on. Every layer of the protocol incorporates cryptographic protections. There is no trusted infrastructure — no certificate authorities, no trusted servers. DNS is used only for initial [genesis gateway discovery](../economics/token-economics#genesis-gateway-discovery), not for protocol operation.

## Threat Model

:::danger[Threat]

Mehr assumes the worst:

- **Open network**: Any node can join. Nodes may be malicious.
- **Hostile observers**: All link-layer traffic may be monitored (especially radio).
- **No trusted infrastructure**: No certificate authorities, no trusted servers. DNS is used only for initial genesis gateway discovery, not for protocol operation.
- **State-level adversaries**: Governments may control internet gateways and operate nodes within the mesh.

Mehr does **not** attempt to defend against:

- **Global traffic analysis**: A sufficiently powerful adversary monitoring all links simultaneously can correlate traffic patterns. [Opt-in onion routing](#onion-routing-opt-in) mitigates this for individual packets but does not defeat a global adversary.
- **Physical compromise**: If an adversary physically captures a node, they obtain its private key and all local state.

:::

## Encryption Model

### Link-Layer Encryption (Hop-by-Hop)

Every link between two nodes is encrypted using a session key derived from X25519 Diffie-Hellman key exchange:

```
Link establishment:
  1. Alice and Bob exchange X25519 ephemeral public keys
  2. Both derive shared_secret = X25519(my_ephemeral, their_ephemeral)
  3. session_key = Blake2b(shared_secret || alice_pub || bob_pub)
  4. All traffic on this link encrypted with ChaCha20-Poly1305(session_key)
     Nonce: 64-bit counter (zero-padded to 96 bits), incremented per packet
     Counter is per session_key — reset to 0 on each key rotation
     No nonce reuse risk: key rotation occurs well before 2^64 packets
  5. Keys rotated periodically (every 1 hour of local monotonic time, or
     max(1 MB, bandwidth_bps × 60s) of data, whichever first — this scales
     the data threshold to ~1 minute of link capacity, preventing excessive
     rotation on fast links). "1 hour" is measured by each node's local
     monotonic clock independently — no synchronization needed. Either side
     of the link can initiate rotation; the peer accepts and derives a new
     session key via fresh ephemeral key exchange
```

This prevents passive observers from reading packet contents or metadata beyond the cleartext header fields needed for routing.

### End-to-End Encryption (Data Payloads)

Data packets are encrypted by the sender for the destination using the destination's public key. Relay nodes **cannot** read the payload:

```
E2E encryption for a message to Bob:
  1. Alice generates ephemeral X25519 keypair
  2. shared_secret = X25519(alice_ephemeral, bob_x25519_public)
  3. payload_key = Blake2b(shared_secret || alice_ephemeral_pub)
  4. encrypted_payload = ChaCha20-Poly1305(payload_key, plaintext)
  5. Packet contains: alice_ephemeral_pub || encrypted_payload
  6. Bob derives the same payload_key and decrypts
```

This provides **forward secrecy per message** — each message uses a unique ephemeral key. Compromise of one message's key does not compromise any other message.

### What Relay Nodes Can See

| Visible | Hidden |
|---------|--------|
| Destination hash | Source address |
| Hop count | Payload contents |
| Packet size | Application-layer data |
| Timing | Sender identity |

## Authentication

Node identity is **self-certifying**. A node proves it owns a destination hash by signing with the corresponding Ed25519 private key. No certificates, no PKI, no trust hierarchy.

- **Payment channels**: Both parties sign every state update. Forgery requires the other party's private key.
- **Capability agreements**: Both provider and consumer sign. Neither can forge the other's commitment.
- **Announcements**: Path announcements are signed by the announcing node. Relay nodes update the [CompactPathCost](network-protocol#mehr-extension-compact-path-cost) running totals (not individually signed — link-layer authentication at each hop is sufficient). Malicious relays can lie about costs, but the economic model disincentivizes this — overpriced nodes are routed around, underpriced nodes lose money.

## Privacy

### Sender Anonymity

Packets do not carry source addresses. A relay node knows which neighbor sent it a packet, but not whether that neighbor originated the packet or is relaying it from someone else.

### Recipient Privacy

Destination hashes are pseudonymous. A hash is not linked to a real-world identity unless the user chooses to publish that association (e.g., via MHR-Name).

### Traffic Analysis Resistance

Basic protections (always active):
- Link-layer encryption prevents content inspection
- Variable-rate padding on LoRa links obscures traffic patterns
- No source address in packet headers

### Onion Routing (Opt-In)

For high-threat environments where an adversary monitors multiple links simultaneously, per-packet layered encryption is available as an opt-in privacy upgrade via `PathPolicy.ONION_ROUTE`:

```
Onion-routed packet (3-hop default):
  1. Sender selects 3 intermediate relays (at least 1 outside trust neighborhood)
  2. Wraps message in 3 encryption layers (outermost = first relay)
  3. Each layer: 16-byte nonce + 16-byte Poly1305 tag = 32 bytes overhead
  4. Each relay decrypts one layer, reads next-hop destination, forwards
  5. Final relay decrypts innermost layer and delivers to destination

Overhead: 32 bytes × 3 hops = 96 bytes
Usable payload on LoRa (465 max): 369 bytes (~79% efficiency)
```

Key properties:
- **Stateless**: No circuit establishment, no relay-side state. Each packet is independently routable
- **Opt-in**: Enabled per-packet via `PathPolicy.ONION_ROUTE` with configurable hop count (default 3)
- **Cover traffic**: Optional constant-rate dummy packets (1/minute, off by default) for timing analysis resistance on high-threat links
- **Not for voice**: The payload overhead and additional latency make onion routing unsuitable for real-time voice. Recommended for text messaging in high-threat scenarios

### Key Rotation

- **Long-lived keys** (Ed25519 identity): Used only for signing, never for encryption
- **Ephemeral keys**: Used for encryption, discarded after use
- Compromise of an ephemeral key does not compromise past or future communications

## Sybil Resistance

:::danger[Threat]

An attacker can generate unlimited identities (Sybil attack). Mehr mitigates this through economic mechanisms rather than identity verification:

1. **Payment channel deposits**: Opening a channel requires visible balance. Sybil nodes with no balance cannot participate in the economy.
2. **Reputation accumulation**: Reputation is earned through verified service delivery over time. New identities start with zero reputation. Creating many identities dilutes rather than concentrates reputation.
3. **Trust graph**: A Sybil attacker needs real social relationships to gain trust. Trusted peers [vouch economically](../economics/trust-neighborhoods#trust-based-credit) — they absorb the debts of nodes they trust, making trust costly to extend.
4. **Proof of service (demand-backed)**: Stochastic relay rewards use a [VRF-based lottery](../economics/payment-channels#how-stochastic-rewards-work) that produces exactly one verifiable outcome per (relay, packet) pair — preventing grinding. However, VRF alone does not prevent traffic fabrication between colluding nodes. The actual Sybil defense is [demand-backed minting](../economics/payment-channels#demand-backed-minting-eligibility): VRF wins only count for minting if the packet traversed a funded payment channel, and [revenue-capped minting](../economics/payment-channels#revenue-capped-minting) ensures self-dealing is always unprofitable (spending Y MHR on fake traffic yields at most 0.5Y in minting).
5. **Transitive credit limits**: Even if a Sybil node gains one trust relationship, transitive credit is capped at 10% per hop and rate-limited for new relationships.

:::

## Reputation

Reputation is a **locally computed, per-neighbor score** — not a global value. There is no network-wide reputation database. Each node maintains its own view of how reliable its peers are.

### Reputation State

```
PeerReputation {
    node_id: NodeID,
    relay_score: u16,       // 0-10000 (fixed-point, 2 decimal places)
    storage_score: u16,     // 0-10000
    compute_score: u16,     // 0-10000
    total_interactions: u32, // number of completed agreements
    failed_interactions: u32,// number of failed/disputed agreements
    first_seen_epoch: u64,  // how long we've known this peer
    last_updated: Timestamp,
}
```

### How Reputation Is Earned

Each completed capability agreement adjusts the relevant score:

```
On agreement completion:
  if successful:
    score += (10000 - score) / 100   // diminishing returns — harder to gain at higher scores
  if failed:
    score -= score / 10              // 10% penalty per failure — fast to lose

Initialization:
  - New peer (no interactions, no referral): score = 0 (unknown)
  - New peer with trusted referral: score = min(5000, referrer_score × 0.3)
  - Referral → first-hand transition: after 5 successful interactions,
    first-hand score fully replaces the referral score
  - Referral expiry: 500 gossip rounds (~8 hours) without refresh
```

### How Reputation Is Used

- **Credit line sizing**: Nodes extend larger credit lines to higher-reputation peers
- **Capability selection**: When multiple providers offer the same capability, the consumer considers reputation alongside cost and latency
- **Storage agreement duration**: Nodes with higher storage scores get offered longer storage contracts
- **Epoch consensus**: Epoch proposals from higher-reputation nodes are preferred when competing proposals conflict

### Properties

- **Local only**: Each node computes its own reputation scores. No gossip of reputation values — this prevents reputation manipulation by flooding the network with fake endorsements
- **First-hand primary**: Scores are based primarily on direct interactions. First-hand experience always takes precedence over third-party information
- **No global score**: There is no way to ask "what is node X's reputation?" There is only "what is my experience with node X?" This makes reputation Sybil-resistant — an attacker can't inflate a score without actually providing good service to the scoring node

### Trust-Weighted Referrals

When a node has no direct experience with a peer, it can query trusted neighbors for their first-hand scores. Referrals help new nodes bootstrap but are tightly bounded to limit manipulation:

- **1-hop only**: Only direct trusted peers can provide referrals. No transitive gossip — a referral from a friend-of-a-friend is not accepted. This limits the manipulation surface to corruption of your direct trusted peers
- **Weight formula**: `referral_weight = trust_score_of_referrer / max_score × 0.3` — even a maximally trusted referrer's opinion carries only 30% of direct experience weight
- **Capped at 50%**: A referred reputation score cannot exceed 5000 (50% of max). A referral alone cannot make a peer fully trusted — direct interaction is required to reach higher scores
- **Overwritten by experience**: Referral scores are advisory. After the first few direct interactions, first-hand experience overwrites the referral entirely
- **Expiry**: Referral scores expire after 500 gossip rounds (~8 hours at 60-second intervals) without refresh from the referrer
- **Anti-collusion**: Since only 1-hop referrals are accepted and each is capped, a colluding cluster must corrupt your direct trusted peers to manipulate scores — which already breaks the trust model regardless of reputation

## Key Management

| Operation | Method |
|-----------|--------|
| **Generation** | Ed25519 keypair from cryptographically secure random source on first boot |
| **Storage** | Private key encrypted at rest (ChaCha20-Poly1305 with user passphrase, or hardware secure element) |
| **Recovery** | Social recovery via Shamir's Secret Sharing — split key into N shares, recover with K-of-N |
| **Revocation** | No global revocation mechanism (intentional — no infrastructure that can be coerced into revoking keys) |

The absence of a revocation mechanism is a deliberate tradeoff. A user who loses their key loses their identity and balance, but no authority can forcibly revoke anyone's identity.

### Key Compromise Advisory

While there is no revocation, a node that detects its key has been compromised can broadcast an advisory:

```
KeyCompromiseAdvisory {
    compromised_key: Ed25519PublicKey,
    new_key: Ed25519PublicKey,          // optional migration target
    sequence: u64,                      // monotonic counter — prevents replay of old advisories
    evidence: enum {
        SignedByBoth(sig_old, sig_new), // proves control of both keys
        SignedByOldOnly(sig_old),       // can only prove old key ownership
    },
    timestamp: u64,
}
```

The `sequence` field is monotonically increasing per compromised key. Receiving nodes only accept an advisory if its sequence is strictly greater than any previously seen advisory for the same `compromised_key`. This prevents an attacker from replaying an old advisory to override a newer one.

This is **advisory, not authoritative**. Receiving nodes may:
- Flag the old identity as potentially compromised
- Require re-authentication for high-value operations
- Accept the new key if evidence includes both signatures (strongest proof)

**Conflict resolution**: An attacker holding the stolen key could issue a counter-advisory claiming the legitimate owner's *new* key is compromised. Receiving nodes resolve conflicting advisories as follows:

1. **`SignedByBoth` always wins over `SignedByOldOnly`** — proving control of both keys is strictly stronger evidence than proving control of only one
2. **Multiple `SignedByOldOnly` advisories cancel out** — if two different advisories both signed only by the old key claim different new keys, both are suspect. Receiving nodes flag the old identity as compromised but accept neither new key automatically.
3. **Trust-weighted resolution** — if the advisory is vouched for by trusted peers (who can attest to knowing the real owner), it is weighted more heavily

This does not prevent an attacker from continuing to use the stolen key. It provides a mechanism for the legitimate owner to signal compromise and begin migration — strictly better than no mechanism at all. The `SignedByBoth` evidence type is the only reliable migration path; users should generate their new keypair **before** the old one is exposed whenever possible.

## Cryptographic Primitives Summary

| Purpose | Algorithm | Key Size |
|---------|-----------|----------|
| Identity / Signing | Ed25519 | 256-bit (32-byte public key) |
| Key Exchange | X25519 (Curve25519 DH) | 256-bit |
| Identity Hashing | Blake2b | 256-bit |
| Content Hashing | Blake3 | 256-bit |
| Symmetric Encryption | ChaCha20-Poly1305 | 256-bit key, 96-bit nonce |
| Address Derivation | Blake2b truncated | 128-bit (16-byte destination hash) |
| Relay Lottery (VRF) | ECVRF-ED25519-SHA512-TAI ([RFC 9381](https://www.rfc-editor.org/rfc/rfc9381)) | Reuses Ed25519 keypair; 80-byte proof |

### Hash Algorithm Split

Mehr uses two hash algorithms for distinct purposes:

- **Blake2b** — Identity derivation and key derivation. Chosen for compatibility with the Ed25519/X25519 ecosystem and its proven security margin. Used in: `destination_hash`, `session_key` derivation.
- **Blake3** — Content addressing and general hashing. Chosen for speed (3x faster than Blake2b on general data) and built-in Merkle tree support for streaming verification. Used in: `DataObject` hash, contract hash, DHT keys, `ChannelState` hash.

Both produce 256-bit outputs. The protocol never mixes them — identity operations use Blake2b, data operations use Blake3.

### Ed25519 to X25519 Conversion

X25519 public keys are derived from Ed25519 public keys using the birational map defined in **RFC 7748 Section 4.1**: the Ed25519 public key (a compressed Edwards point) is converted to Montgomery form by computing `u = (1 + y) / (1 - y) mod p`, where `y` is the Edwards y-coordinate and `p = 2^255 - 19`. This is a standard, well-analyzed transformation used by libsodium, OpenSSL, and other major cryptographic libraries.

<!-- faq-start -->

## Frequently Asked Questions

<details className="faq-item">
<summary>What happens if a node's private key is physically compromised?</summary>

If an adversary physically captures a node, they obtain its private key and all local state. Mehr does not attempt to defend against this. However, the compromised node can broadcast a KeyCompromiseAdvisory signed by both the old and new keys, enabling migration to a new identity. Forward secrecy ensures that past messages (encrypted with unique ephemeral keys) remain secure even after key compromise.

</details>

<details className="faq-item">
<summary>How does Mehr defend against Sybil attacks without proof-of-work or staking?</summary>

Mehr uses economic mechanisms instead of identity verification. Payment channel deposits require visible balance, reputation is earned through verified service delivery over time, trusted peers vouch economically (absorbing debts of nodes they trust), and VRF-based relay rewards are demand-backed — only funded payment channel traffic earns minting. Revenue-capped minting ensures that spending Y MHR on fake traffic yields at most 0.5Y in minting, making self-dealing structurally unprofitable.

</details>

<details className="faq-item">
<summary>Does Mehr provide forward secrecy for messages?</summary>

Yes. Every end-to-end message uses a unique ephemeral X25519 keypair generated by the sender. The shared secret is derived from this ephemeral key and the recipient's public key, then used for ChaCha20-Poly1305 encryption. Since each message has its own ephemeral key that is discarded after use, compromising one message's key reveals nothing about any other message — true per-message forward secrecy.

</details>

<details className="faq-item">
<summary>Can relay nodes see message contents or sender identity?</summary>

No. Data payloads are end-to-end encrypted — relay nodes cannot read them. Additionally, packets carry only the destination hash, never the source address. A relay knows which direct neighbor forwarded a packet but cannot determine if that neighbor originated it or is relaying from someone else. For high-threat scenarios, optional onion routing adds layered encryption across 3 hops.

</details>

<details className="faq-item">
<summary>Why is there no global key revocation mechanism?</summary>

This is a deliberate tradeoff. A global revocation mechanism requires infrastructure that can be coerced — a certificate authority or revocation list that governments could force to revoke identities. Instead, Mehr provides a KeyCompromiseAdvisory system that is advisory, not authoritative. A user who loses their key loses their identity and balance, but no external authority can forcibly revoke anyone's identity.

</details>

<!-- faq-end -->
