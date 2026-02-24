---
sidebar_position: 3
title: Voice
---

# Voice

Voice communication in NEXUS ranges from push-to-talk over LoRa to full-duplex calls over WiFi, adapting to available bandwidth.

## Codec Selection by Link Quality

| Link Type | Codec | Bitrate | Mode |
|-----------|-------|---------|------|
| LoRa (10+ kbps) | Codec2 | 700-3,200 bps | Push-to-talk |
| WiFi / Cellular | Opus | 6-510 kbps | Full-duplex |

### Codec2 on LoRa

Codec2 is an open-source voice codec designed for very low bitrates. At 700 bps, it produces intelligible speech — not high-fidelity, but functional for communication. At 3,200 bps, quality is similar to AM radio.

A 10 kbps LoRa link has enough bandwidth for Codec2 push-to-talk with room for protocol overhead.

### Opus on WiFi

On higher-bandwidth links, Opus provides near-CD-quality voice with full-duplex operation (both parties can talk simultaneously).

## Encryption

Voice streams are encrypted with a per-session symmetric key, negotiated via the standard [X25519 key exchange](../protocol/security#link-layer-encryption-hop-by-hop).

## Bandwidth Bridging

When participants are on different link types, the application can use compute delegation to bridge:

```
Scenario: Alice is on LoRa, Bob is on WiFi

Option 1: Codec conversion
  Alice sends Codec2 audio over LoRa to a bridge node
  Bridge node transcodes Codec2 → Opus
  Bridge node sends Opus audio to Bob over WiFi

Option 2: Speech-to-text bridging
  Alice sends Codec2 audio over LoRa
  A nearby compute node runs STT (Whisper) on the audio
  Text is sent to Bob over WiFi
  Bob's device optionally runs TTS to play it as audio
```

This is an **application-level decision** using standard [compute delegation](../marketplace/agreements). The protocol has no concept of "voice" — it routes bytes. The application decides how to adapt between bandwidth tiers.

## Push-to-Talk Protocol

On half-duplex links (LoRa), push-to-talk works as:

1. Sender presses talk button
2. Audio captured, encoded with Codec2
3. Encoded frames sent as a stream of small packets
4. Receiver buffers and plays back
5. Sender releases button, receiver can now respond

The protocol handles this as ordinary data packets — there is no special voice channel.
