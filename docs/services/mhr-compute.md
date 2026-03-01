---
sidebar_position: 4
title: "MHR-Compute: Contract Execution"
description: "MHR-Compute provides sandboxed execution via MHR-Byte bytecode for constrained devices and WASM for capable nodes."
keywords:
  - compute
  - WASM
  - bytecode
  - smart contracts
  - execution
  - sandboxed
---

# MHR-Compute: Contract Execution

MHR-Compute provides a restricted execution environment for data validation, state transitions, and access control. It supports two execution tiers: MHR-Byte (a minimal bytecode for constrained devices) and WASM (for capable nodes).

## MHR-Byte: Minimal Bytecode

:::info[Specification]

```
MHR-Contract {
    hash: Blake3Hash,
    code: Vec<u8>,              // MHR-Byte bytecode
    max_memory: u32,
    max_cycles: u64,
    max_state_size: u32,
    state_key: Hash,            // current state in MHR-Store
    functions: [FunctionSignature],
}
```

:::

MHR-Byte is a minimal bytecode with a ~50 KB interpreter, designed to run on constrained devices like the ESP32. It supports:

| Capability | Description |
|-----------|-------------|
| **Cryptographic primitives** | Hash, sign, verify |
| **CRDT operations** | Merge, compare |
| **CBOR/JSON manipulation** | Structured data processing |
| **Bounded control flow** | Loops with hard cycle limits |

MHR-Byte explicitly **does not** support:
- I/O operations
- Network access
- Filesystem access
- Unbounded computation

All execution is **pure deterministic computation**. Given the same inputs, any node running the same contract produces the same output. This is what makes [verification](../marketplace/verification) possible.

### Opcode Set (47 Opcodes)

| Category | Opcodes | Cycle Cost | Description |
|----------|---------|-----------|-------------|
| **Stack** (6) | PUSH, POP, DUP, SWAP, OVER, ROT | 1 | Stack manipulation |
| **Arithmetic** (9) | ADD, SUB, MUL, DIV, MOD, NEG, ABS, MIN, MAX | 1–3 | 64-bit integer, overflow traps |
| **Bitwise** (6) | AND, OR, XOR, NOT, SHL, SHR | 1 | Bitwise operations |
| **Comparison** (6) | EQ, NEQ, LT, GT, LTE, GTE | 1 | Pushes 0 or 1 |
| **Control** (7) | JMP, JZ, JNZ, CALL, RET, HALT, ABORT | 2–5 | Bounded control flow |
| **Crypto** (3) | HASH, VERIFY_SIG, VERIFY_VRF | 500–2000 | Blake3, Ed25519, ECVRF |
| **System** (10) | BALANCE, SENDER, SELF, EPOCH, TRANSFER, LOG, LOAD, STORE, MSIZE, EMIT | 2–50 | State access and side effects |

**Cycle cost model**: The base unit is 1 cycle ≈ 1 μs on ESP32 (the reference platform). Faster hardware executes more cycles per wall-clock second but charges the same cycle cost per opcode. Gas price in μMHR/cycle is set by each compute provider in their capability advertisement.

**Specification approach**: The reference interpreter (in Rust) serves as the authoritative specification. A comprehensive test vector suite ensures cross-platform conformance. Formal specification (Yellow Paper-style) is deferred until the opcode set stabilizes through real-world usage.

## WASM: Full Execution

Gateway nodes and more capable hardware can offer full WASM (WebAssembly) execution as an additional compute capability. A contract declares its WASM requirement tier:

```
Contract execution path:
  1. Contract specifies: wasm_tier: None
     → Can run on any node with MHR-Byte interpreter (~50 KB)

  2. Contract specifies: wasm_tier: Light
     → Requires Community-tier or above (Pi Zero 2W+)
     → 16 MB memory limit, 10^8 fuel limit, 5 second wall-clock

  3. Contract specifies: wasm_tier: Full
     → Requires Gateway-tier or above (Pi 4/5+)
     → 256 MB memory limit, 10^10 fuel limit, 30 second wall-clock
     → Delegated via capability marketplace if local node can't execute
```

### WASM Sandbox

The WASM execution environment uses **Wasmtime** (Bytecode Alliance, Rust-native) as the reference runtime. Wasmtime provides AOT compilation on Gateway+ nodes, fuel-based execution metering that maps to MHR-Byte cycle accounting, and configurable memory limits per contract.

```
WasmSandbox {
    runtime: Wasmtime,
    max_memory: u32,             // from contract's max_memory field
    max_fuel: u64,               // from contract's max_cycles (1 fuel ≈ 1 MHR-Byte cycle)
    max_wall_time_ms: u32,       // 5,000 (Light) or 30,000 (Full)
}
```

**Host imports**: WASM contracts call back into the Mehr system through a restricted host API mirroring the MHR-Byte System opcodes:

| Host Function | MHR-Byte Equivalent | Fuel Cost |
|--------------|---------------------|-----------|
| `mehr_balance(node_id) → u64` | BALANCE | 10 |
| `mehr_sender() → [u8; 16]` | SENDER | 2 |
| `mehr_self() → [u8; 16]` | SELF | 2 |
| `mehr_epoch() → u64` | EPOCH | 5 |
| `mehr_transfer(to, amount) → bool` | TRANSFER | 50 |
| `mehr_log(data)` | LOG | 10 |
| `mehr_store_load(key) → Vec<u8>` | LOAD | 3 |
| `mehr_store_save(key, value)` | STORE | 3 |
| `mehr_hash(data) → [u8; 32]` | HASH | 500 |
| `mehr_verify_sig(pubkey, msg, sig) → bool` | VERIFY_SIG | 1000 |

No other host imports are available. WASM contracts cannot access the filesystem, network, clock, or random number generator — all execution remains pure and deterministic.

### Light WASM (Community Tier)

Community-tier devices (Pi Zero 2W, 512 MB RAM) support a restricted WASM profile: 16 MB max memory, 10^8 max fuel, 5-second wall-clock limit, interpreted via Cranelift baseline (no AOT). Contracts exceeding Light WASM limits are automatically delegated to a more capable node via [compute delegation](#compute-delegation).

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

## Opaque Compute: Hardware-Accelerated Services

:::tip[Key Insight]

ML inference, transcription, translation, text-to-speech, and any other heavy computation are **not protocol primitives**. They are compute capabilities offered by nodes that have the hardware. The pattern is **opaque compute**: input goes in, output comes out. The protocol does not sandbox, inspect, or guarantee the compute method — the node can use GPU, NPU, FPGA, or any hardware.

:::

```
A GPU/NPU node advertises:
  offered_functions: [
    { function_id: hash("whisper-small"), cost: 50 μMHR/minute },
    { function_id: hash("piper-tts"), cost: 30 μMHR/minute },
  ]
```

A consumer requests execution of that function through the standard compute delegation path. The protocol is **agnostic to what the function does** — it only cares about discovery, negotiation, execution, verification, and payment. Trust comes from reputation, not verification of the compute method.

**Hardware examples:**

| Accelerator Type | Examples |
|-----------------|----------|
| **GPU** | NVIDIA RTX series, AMD Radeon |
| **NPU** | Apple Neural Engine, Qualcomm Hexagon, MediaTek APU |
| **FPGA** | Xilinx, Intel/Altera |
| **TPU** | Google Edge TPU |

### Result Verification for Opaque Compute

Since opaque compute provides no built-in execution guarantee, consumers choose a verification strategy based on their trust requirements and budget:

| Strategy | How It Works | Cost | Trust Level |
|----------|-------------|------|-------------|
| **1. Reputation (default)** | Node builds reputation through consistent outputs. Bad outputs → trust removal → lost income stream. | None (built into trust system) | Moderate |
| **2. Redundant execution** | Client sends same input to 2–3 nodes. Majority agreement = accepted result. | 2–3x compute fees | High |
| **3. Spot-checking** | Client occasionally sends inputs with known outputs. Wrong answer → node flagged, agreement terminated. | ~5% overhead | Moderate–High |
| **4. Cryptographic verification** | ZK proofs for deterministic contracts; TEE attestation for opaque compute. See below. | 10–1000x (ZK) or ~5% (TEE) | Highest |

### Cryptographic Verification Details

ZK proofs and TEE attestation provide the strongest verification guarantees. Their applicability depends on the workload:

```
Cryptographic verification tiers:

  Tier A: ZK Proofs for MHR-Byte / WASM Contracts (deterministic compute)

    Viable ZK systems for Mehr's constraint environment:
      1. RISC Zero (zkVM) — proves correct execution of RISC-V programs
         Circuit: RISC-V trace → STARK proof
         Proof size: ~200 KB (compressible to ~50 KB with SNARK wrapping)
         Prover cost: ~1000x slowdown vs native execution
         Verifier cost: ~10 ms on Raspberry Pi, <1 ms on Gateway+
         Viable for: MHR-Byte and WASM contracts up to ~10^6 cycles

      2. SP1 (Succinct) — similar approach, optimized prover
         Proof size: ~100-300 KB
         Prover cost: ~500-1000x slowdown
         Viable for: same as RISC Zero, slightly better performance

      3. Jolt (a]16) — optimized for structured computations
         Proof size: ~50-150 KB
         Prover cost: ~200-500x slowdown for simple contracts
         Viable for: contracts with bounded loops and array operations

    Practical overhead for typical workloads:
      Simple validation contract (10^4 cycles): ~10 second prover time
      Complex state migration (10^6 cycles): ~15 minutes prover time
      ZK proofs are IMPRACTICAL above ~10^8 cycles with current technology

    Cost model:
      zk_proof_cost = base_compute_cost × zk_overhead_factor
      zk_overhead_factor = 500 (default, adjustable by provider)
      Consumer pays for the proof generation as part of the compute fee

    Integration:
      ComputeResult {
          job_hash: Blake3Hash,
          output_hash: Blake3Hash,
          proof: Option<ZKProof>,    // present when ZK verification requested
          proof_system: u8,          // 0=None, 1=RISC_Zero, 2=SP1, 3=Jolt
      }
      Verifier checks proof against (contract_hash, input_hash, output_hash)
      Any node can verify without re-executing the contract

  Tier B: TEE Attestation for Opaque Compute (non-deterministic / large models)

    ZK proofs are impractical for large ML models (10^12+ operations).
    TEE attestation is the viable path for high-assurance opaque compute:

      TEE platforms:
        AMD SEV-SNP: Available now on EPYC processors
        NVIDIA H100 Confidential Computing: GPU compute inside TEE
        ARM CCA (Confidential Compute Architecture): Emerging

      Attestation flow:
        1. Provider generates attestation report from TEE hardware
        2. Report binds: TEE identity + loaded code hash + platform state
        3. Consumer verifies report against vendor's root of trust
        4. If valid: the code running in the TEE matches expectations

      Cost: ~5% overhead vs plaintext (hardware-level, nearly free)
      Trust assumption: hardware vendor is honest

    For Mehr:
      TEE attestation is preferred over ZK for models > 10^6 parameters.
      Nodes advertise TEE support in capability bits.
      Attestation reports are ~2-4 KB, verified by the consumer.

  Decision matrix:
    Workload                    Recommended verification
    ─────────────────────────   ──────────────────────────
    MHR-Byte contract (<10^4)   ZK proof (cheap, fast)
    WASM contract (<10^6)       ZK proof (feasible)
    WASM contract (>10^6)       Redundant execution or TEE
    Small ML model (<1M params) Redundant execution + spot-check
    Large ML model (>1M params) TEE attestation (if available)
    Any model on GPU             TEE (NVIDIA H100 CC) or reputation
    No TEE, large model          Reputation + spot-checking (default)

  Mehr does NOT mandate any single verification approach.
  The consumer chooses based on sensitivity, budget, and available providers.
  The protocol provides the framework; the market determines adoption.
```

Verification is a **consumer-side choice**, not protocol enforcement. Most consumers rely on reputation (the default). High-value or adversarial workloads use redundant execution or spot-checking.

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

<!-- faq-start -->

## Frequently Asked Questions

<details className="faq-item">
<summary>What kind of programs can run on MHR-Compute?</summary>

MHR-Compute supports two tiers: MHR-Byte (a minimal 47-opcode bytecode) runs on any device including ESP32 microcontrollers and handles data validation, access control, and simple state transitions. WASM (WebAssembly) runs on more capable hardware and supports complex logic up to 256 MB memory. Neither tier can access the network, filesystem, or clock — all execution is pure and deterministic.

</details>

<details className="faq-item">
<summary>Who pays for computation, and how?</summary>

The node requesting the computation pays. Each opcode has a cycle cost, and compute providers set a price in μMHR per cycle in their capability advertisements. Payment flows through bilateral payment channels — the same mechanism used for all Mehr services. If your node can run the contract locally, there’s no payment to anyone else.

</details>

<details className="faq-item">
<summary>Is this like smart contracts on a blockchain?</summary>

Similar in concept (deterministic, verifiable programs) but fundamentally different in architecture. MHR-Compute contracts don’t require global consensus or a blockchain. They run on individual nodes, state lives in CRDT DataObjects that merge without consensus, and verification is bilateral (between the parties involved). There’s no gas auction, no block confirmation wait, and no global state.

</details>

<details className="faq-item">
<summary>Can GPUs or other accelerators be used for computation?</summary>

Yes, through **opaque compute**. Nodes with GPUs, NPUs, FPGAs, or TPUs advertise specific functions they can run (e.g., Whisper speech-to-text, image generation). These aren’t sandboxed like MHR-Byte/WASM — the protocol treats them as black boxes where input goes in and output comes out. Trust comes from reputation, redundant execution, or TEE attestation rather than deterministic verification.

</details>

<details className="faq-item">
<summary>What if my device is too weak to run a contract?</summary>

Your node automatically delegates to a more capable neighbor via the capability marketplace. The delegation is transparent — you send a request, a nearby node executes the contract, returns the result, and you verify it. You pay the provider’s compute fees. The original requester doesn’t need to know whether execution was local or delegated.

</details>

<!-- faq-end -->
