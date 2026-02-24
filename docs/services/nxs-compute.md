---
sidebar_position: 4
title: "NXS-Compute: Contract Execution"
---

# NXS-Compute: Contract Execution

NXS-Compute provides a restricted execution environment for data validation, state transitions, and access control. It supports two execution tiers: NXS-Byte (a minimal bytecode for constrained devices) and WASM (for capable nodes).

## NXS-Byte: Minimal Bytecode

```
NXS-Contract {
    hash: Blake3Hash,
    code: Vec<u8>,              // NXS-Byte bytecode
    max_memory: u32,
    max_cycles: u64,
    max_state_size: u32,
    state_key: Hash,            // current state in NXS-Store
    functions: [FunctionSignature],
}
```

NXS-Byte is a minimal bytecode with a ~50 KB interpreter, designed to run on constrained devices like the ESP32. It supports:

| Capability | Description |
|-----------|-------------|
| **Cryptographic primitives** | Hash, sign, verify |
| **CRDT operations** | Merge, compare |
| **CBOR/JSON manipulation** | Structured data processing |
| **Bounded control flow** | Loops with hard cycle limits |

NXS-Byte explicitly **does not** support:
- I/O operations
- Network access
- Filesystem access
- Unbounded computation

All execution is **pure deterministic computation**. Given the same inputs, any node running the same contract produces the same output. This is what makes [verification](../marketplace/verification) possible.

## WASM: Full Execution

Gateway nodes and more capable hardware can offer full WASM (WebAssembly) execution as an additional compute capability. A contract declares whether it needs WASM or can run on NXS-Byte.

```
Contract execution path:
  1. Contract specifies: requires_wasm: false
     → Can run on any node with NXS-Byte interpreter (~50 KB)

  2. Contract specifies: requires_wasm: true
     → Requires a node with WASM runtime
     → Delegated via capability marketplace if local node can't execute
```

## Compute Delegation

If a node can't execute a contract locally, it delegates to a capable neighbor via the [capability marketplace](../marketplace/overview):

```
Delegation flow:
  1. Node receives request to execute contract
  2. Node checks: can I run this locally?
  3. If no: query nearby capabilities for compute
  4. Find a provider, form agreement, send execution request
  5. Receive result, verify (per agreement's proof method)
  6. Return result to requester
```

This is transparent to the original requester — they don't need to know whether their contract ran locally or was delegated.

## Heavy Compute as Capabilities

ML inference, transcription, translation, text-to-speech, and any other heavy computation are **not protocol primitives**. They are compute capabilities offered by nodes that have the hardware:

```
A GPU node advertises:
  offered_functions: [
    { function_id: hash("whisper-small"), cost: 50 μNXS/minute },
    { function_id: hash("piper-tts"), cost: 30 μNXS/minute },
  ]
```

A consumer requests execution of that function through the standard compute delegation path. The protocol is **agnostic to what the function does** — it only cares about discovery, negotiation, execution, verification, and payment.

## Contract Use Cases

| Application | Contract Purpose |
|------------|-----------------|
| **Naming** | Community-label-scoped name resolution (`maryam@tehran-mesh` → NodeID) |
| **Forums** | Append-only log management, moderation rules |
| **Marketplace** | Listing validation, escrow logic |
| **Wiki** | CRDT merge rules for collaborative documents |
| **Group messaging** | Symmetric key rotation, member management |
| **Access control** | Permission checks for mutable data objects |

## Resource Limits

Every contract declares its resource bounds upfront:

- **max_memory**: Maximum memory allocation
- **max_cycles**: Maximum CPU cycles before forced termination
- **max_state_size**: Maximum persistent state

These limits are enforced by the runtime. A contract that exceeds its declared limits is terminated immediately. This prevents denial-of-service through runaway computation.
