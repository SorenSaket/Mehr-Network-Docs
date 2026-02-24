---
sidebar_position: 3
title: "Layer 2: Security"
---

# Layer 2: Security

Security in NEXUS is structural, not bolted on. Every layer of the protocol incorporates cryptographic protections. There is no trusted infrastructure — no certificate authorities, no trusted servers, no DNS.

## Threat Model

NEXUS assumes the worst:

- **Open network**: Any node can join. Nodes may be malicious.
- **Hostile observers**: All link-layer traffic may be monitored (especially radio).
- **No trusted infrastructure**: No certificate authorities, no trusted servers, no DNS.
- **State-level adversaries**: Governments may control internet gateways and operate nodes within the mesh.

NEXUS does **not** attempt to defend against:

- **Global traffic analysis**: A sufficiently powerful adversary monitoring all links simultaneously can correlate traffic patterns. Onion routing (future work) can mitigate this.
- **Physical compromise**: If an adversary physically captures a node, they obtain its private key and all local state.

## Encryption Model

### Link-Layer Encryption (Hop-by-Hop)

Every link between two nodes is encrypted using a session key derived from X25519 Diffie-Hellman key exchange:

```
Link establishment:
  1. Alice and Bob exchange X25519 ephemeral public keys
  2. Both derive shared_secret = X25519(my_ephemeral, their_ephemeral)
  3. session_key = Blake2b(shared_secret || alice_pub || bob_pub)
  4. All traffic on this link encrypted with ChaCha20-Poly1305(session_key)
  5. Keys rotated periodically (every 1 hour or max(1 MB, bandwidth_bps × 60s),
     whichever first — this scales the data threshold to ~1 minute of link
     capacity, preventing excessive rotation on fast links)
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
- **Announcements**: Path announcements are signed by the announcing node. Relay nodes append signed cost annotations. Malicious relays can lie about costs, but the economic model disincentivizes this — overpriced nodes are routed around, underpriced nodes lose money.

## Privacy

### Sender Anonymity

Packets do not carry source addresses. A relay node knows which neighbor sent it a packet, but not whether that neighbor originated the packet or is relaying it from someone else.

### Recipient Privacy

Destination hashes are pseudonymous. A hash is not linked to a real-world identity unless the user chooses to publish that association (e.g., via NXS-Name).

### Traffic Analysis Resistance

Basic protections include:
- Link-layer encryption prevents content inspection
- Variable-rate padding on LoRa links obscures traffic patterns
- Full traffic analysis resistance (onion routing) is deferred to future work

### Key Rotation

- **Long-lived keys** (Ed25519 identity): Used only for signing, never for encryption
- **Ephemeral keys**: Used for encryption, discarded after use
- Compromise of an ephemeral key does not compromise past or future communications

## Sybil Resistance

An attacker can generate unlimited identities (Sybil attack). NEXUS mitigates this through economic mechanisms rather than identity verification:

1. **Payment channel deposits**: Opening a channel requires visible balance. Sybil nodes with no balance cannot participate in the economy.
2. **Reputation accumulation**: Reputation is earned through verified service delivery over time. New identities start with zero reputation. Creating many identities dilutes rather than concentrates reputation.
3. **Trust graph**: A Sybil attacker needs real social relationships to gain trust. Trusted peers [vouch economically](../economics/community-zones#trust-based-credit) — they absorb the debts of nodes they trust, making trust costly to extend.
4. **Proof of service**: Stochastic relay rewards use a [VRF-based lottery](../economics/payment-channels#how-stochastic-rewards-work) that produces exactly one verifiable outcome per (relay, packet) pair. A node can only earn by actually delivering packets, and cannot grind for favorable lottery outcomes.
5. **Transitive credit limits**: Even if a Sybil node gains one trust relationship, transitive credit is capped at 10% per hop and rate-limited for new relationships.

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
    evidence: enum {
        SignedByBoth(sig_old, sig_new), // proves control of both keys
        SignedByOldOnly(sig_old),       // can only prove old key ownership
    },
    timestamp: u64,
}
```

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

NEXUS uses two hash algorithms for distinct purposes:

- **Blake2b** — Identity derivation and key derivation. Chosen for compatibility with the Ed25519/X25519 ecosystem and its proven security margin. Used in: `destination_hash`, `session_key` derivation.
- **Blake3** — Content addressing and general hashing. Chosen for speed (3x faster than Blake2b on general data) and built-in Merkle tree support for streaming verification. Used in: `DataObject` hash, contract hash, DHT keys, `ChannelState` hash.

Both produce 256-bit outputs. The protocol never mixes them — identity operations use Blake2b, data operations use Blake3.

### Ed25519 to X25519 Conversion

X25519 public keys are derived from Ed25519 public keys using the birational map defined in **RFC 7748 Section 4.1**: the Ed25519 public key (a compressed Edwards point) is converted to Montgomery form by computing `u = (1 + y) / (1 - y) mod p`, where `y` is the Edwards y-coordinate and `p = 2^255 - 19`. This is a standard, well-analyzed transformation used by libsodium, OpenSSL, and other major cryptographic libraries.
