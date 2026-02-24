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

## Private Compute (Optional)

By default, compute delegation has **no input privacy** — the compute node sees your input and produces a result. This is fine for most workloads (contract execution, public data processing, non-sensitive queries). But for sensitive data — medical records, private messages, financial analysis — you need the compute node to process data it cannot read.

Private compute is **opt-in per agreement**. The consumer chooses a privacy tier based on sensitivity and willingness to pay:

```
CapabilityAgreement {
    ...
    privacy: enum {
        None,                   // default — compute node sees input/output
        SplitInference,         // model partitioned, node sees only middle layers
        SecretShared,           // input split across multiple nodes
        TEE,                    // hardware-attested secure enclave
    },
}
```

### Tier 0: No Privacy (Default)

The compute node receives plaintext input, executes, and returns the result. Verification is via [result hash](../marketplace/verification) or redundant execution. This is the cheapest and fastest option.

**Use for**: Public data, non-sensitive queries, contract execution, anything where the input isn't secret.

### Tier 1: Split Inference

For ML/AI workloads. The neural network is partitioned across nodes so no single node sees both the raw input and the final output:

```
Split inference flow:
  1. Consumer runs first 1-3 layers locally (transforms raw input)
  2. Intermediate activations are sent to Inference node
     (optionally with calibrated DP noise for formal privacy guarantees)
  3. Inference node runs the heavy middle layers
  4. Intermediate result sent back to consumer
  5. Consumer runs final 1-2 layers locally (produces final output)

What the Inference node sees:
  ✗ Raw input (transformed by early layers)
  ✗ Final output (produced by consumer's final layers)
  ✓ Intermediate activations (a compressed, transformed representation)
```

**Overhead**: ~1.2–2x latency vs plaintext. Bandwidth for activation transfer at cut points. Consumer needs enough compute for a few neural network layers (Gateway tier or above).

**Privacy strength**: Moderate. Adding differential privacy noise to activations at cut points provides formal (ε, δ)-privacy guarantees at the cost of some accuracy (2–15% depending on privacy budget).

**Use for**: AI inference on personal data — voice transcription, document analysis, image processing — where the compute node shouldn't see the raw content.

### Tier 2: Secret-Shared Computation

Input data is split using Shamir's Secret Sharing into N shares, each sent to a different compute node. No individual node can reconstruct the input.

```
Secret-shared compute flow:
  1. Consumer splits input into 3 shares (2-of-3 threshold)
  2. Each share sent to a different compute node
  3. Each node computes on its share independently
     - Additions and scalar multiplications: free (local computation)
     - Multiplications between secrets: one communication round between nodes
  4. Consumer collects result shares and reconstructs the output

What each compute node sees:
  ✗ Original input (only a random-looking share)
  ✗ Other nodes' shares
  ✗ Final output
  ✓ Its own share (information-theoretically meaningless alone)
```

**Overhead**: 3x bandwidth (3 shares), 3x compute cost (3 nodes). Linear operations are nearly free; non-linear operations require inter-node communication.

**Trust assumption**: At most 1 of 3 nodes may be malicious (honest majority). The consumer selects 3 nodes from different trust neighborhoods to minimize collusion risk.

**Best for**: Linear/affine workloads — aggregation, statistics, linear classifiers, search queries. For neural networks with many non-linear layers, combine with Tier 1: secret-share the input, run the first layers as MPC on shares, then switch to split inference for the deep non-linear layers.

**Use for**: Medical data analysis, private search, financial computation — anything where the input must remain hidden from all compute providers.

### Tier 3: TEE (Hardware-Attested)

Compute runs inside a Trusted Execution Environment (AMD SEV-SNP, NVIDIA H100 Confidential Computing, or ARM CCA). The hardware enforces that even the node operator cannot read the data being processed.

```
TEE compute flow:
  1. Consumer discovers a node advertising TEE capability
  2. Consumer requests and verifies a remote attestation report
     (proves specific code is running inside a genuine TEE)
  3. Consumer sends encrypted input (encrypted to the TEE's ephemeral key)
  4. TEE decrypts, processes, encrypts output for consumer
  5. Consumer decrypts result

What the node operator sees:
  ✗ Input (encrypted for the TEE)
  ✗ Output (encrypted for the consumer)
  ✗ Intermediate state (protected by hardware)
  ✓ That a computation happened, its duration, and data sizes
```

**Overhead**: Under 5% compute overhead. Near-zero bandwidth overhead. Requires server-grade hardware (AMD EPYC, NVIDIA H100).

**Trust assumption**: You trust the hardware vendor (AMD, Intel, NVIDIA) to have correctly implemented the TEE. You do NOT trust the node operator.

**Limitation**: Only available on Inference-tier nodes with server hardware. Not available on ESP32, Raspberry Pi, or consumer hardware.

**Use for**: Highest-sensitivity workloads — end-to-end encrypted AI inference, confidential data processing — where you're willing to trust the hardware vendor but not the node operator.

### Choosing a Privacy Tier

| Tier | Overhead | Privacy | Hardware Required | Cost |
|------|----------|---------|-------------------|------|
| **None** | 1x | None | Any | Cheapest |
| **Split Inference** | 1.2–2x | Moderate (DP-configurable) | Consumer: Gateway+. Provider: any. | Low premium |
| **Secret Shared** | 3x+ | Strong (information-theoretic) | 3 compute nodes | 3x compute cost |
| **TEE** | ~1x | Strong (hardware-attested) | Provider: server-grade with TEE | Slight premium |

The default is **no privacy**. Most compute delegation doesn't need it — you're running a public contract on public data, or the result hash verification is sufficient. Private compute is for when the **input itself** is sensitive.

### Combining Tiers

Tiers can be combined for defense in depth:

- **Split + Secret Shared**: Secret-share the input, run first layers as MPC across 3 nodes, then split inference for deep layers. Maximum software-based privacy.
- **Split + TEE**: Run the heavy middle layers inside a TEE. The TEE never sees raw input (early layers run locally), and you get hardware attestation for the critical computation.

The consumer specifies the desired combination in the capability agreement. The marketplace handles discovery of nodes that support the requested privacy tier.
