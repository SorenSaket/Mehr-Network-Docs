---
sidebar_position: 2
title: "MHR-App: Upgrades & Migration"
description: "Application upgrade flows, state migration strategies, schema compatibility rules, and partition behavior for MHR-App distributed applications."
keywords: [app upgrades, state migration, schema compatibility, CRDT migration, MHR-App]
---

# MHR-App: Upgrades & Migration

AppManifests are **immutable** — each version is a new DataObject with a new hash. Upgrades work by publishing a new manifest and rebinding the MHR-Name.

## Upgrade Flow

```
  1. Publisher creates new manifest:
     app_version incremented
     Updated contract/UI/schema hashes as needed
     Same publisher identity (continuity of authorship)

  2. Publisher rebinds MHR-Name:
     "forum-app@topic:apps/forums" → AppManifest(new_manifest_hash)
     NameBinding sequence number incremented

  3. Publisher notifies via MHR-Pub:
     Topic = Key(old_manifest_hash)
     Payload = new_manifest_hash + app_version
     All installed nodes receive the notification

  4. User-side upgrade:
     Fetch new manifest, verify signature (same publisher)
     Verify app_version > current version
     Download only changed components (unchanged hashes → already cached)
     Apply state migration if schema changed
```

## State Migration

Three strategies depending on whether the state schema changed:

:::info[Specification]
`StateSchema` defines fields with explicit CRDT types and defaults. Compatibility is programmatically verified: additive changes (new fields only) are auto-merged via CRDT semantics; breaking changes require a deterministic `migration_contract` that transforms old state into new state.
:::

**Compatible** (schema unchanged): State carries over directly. New contract code works with existing CRDT DataObjects. No migration needed.

**Additive** (new fields added, none removed): New schema lists the old schema hash in a `compatible_with` field. New code initializes new fields with defaults. Old state merges cleanly via CRDT semantics.

**Breaking** (incompatible change): New schema includes a `migration_contract` — a contract that transforms old state into new state. The node runs it locally. If migration fails, the user is warned and the old version remains usable.

```
StateSchema {
    fields: [FieldDef],                     // field names, CRDT types, defaults
    compatible_with: [Blake3Hash],          // previous schema hashes (additive compat)
    migration_contract: Option<Blake3Hash>, // contract for breaking migrations
}

FieldDef {
    name: String,                           // field name (max 32 bytes UTF-8)
    crdt_type: CRDTType,                    // GCounter, GSet, LWWRegister, ORSet, RGA, etc.
    default_value: Vec<u8>,                 // CBOR-encoded default for new fields
    required: bool,                         // false = optional field (can be absent)
}
```

## Schema Compatibility Rules

Compatibility between schema versions is **programmatically verifiable**, not purely declared by the developer. A new schema is **additive-compatible** with an old schema if and only if all of the following hold:

```
Additive compatibility rules (checked by runtime):

  1. NO REMOVED FIELDS: Every field in the old schema exists in the new schema
     with the same name and same CRDT type.

  2. NO TYPE CHANGES: A field's CRDT type CANNOT change between versions.
     Rationale: CRDT merge semantics are type-dependent. A GCounter merged
     with an LWWRegister produces undefined behavior.
     If a field must change type → breaking migration required.

  3. NEW FIELDS ONLY: The new schema may add fields not present in the old schema.
     New fields MUST have default_value specified.

  4. REQUIRED → OPTIONAL allowed: A required field can become optional.
     OPTIONAL → REQUIRED forbidden (would break old state missing the field).

Compatibility checker (runs locally at install/upgrade time):
  fn is_compatible(old_schema: &StateSchema, new_schema: &StateSchema) -> bool {
      for old_field in &old_schema.fields {
          match new_schema.fields.find(|f| f.name == old_field.name) {
              None => return false,                    // field removed
              Some(new_field) => {
                  if new_field.crdt_type != old_field.crdt_type {
                      return false;                    // type changed
                  }
                  if new_field.required && !old_field.required {
                      return false;                    // optional → required
                  }
              }
          }
      }
      true
  }
```

The `compatible_with` field in StateSchema lists schema hashes that pass this check. At install time, the runtime verifies the declaration by running the compatibility checker. A manifest that declares `compatible_with` for an incompatible schema is rejected.

## Old Code Encountering New Schema State

When a node running old code encounters new-schema state via CRDT merge:

```
Forward-compatibility behavior:

  Old node receives state with unknown fields:
    1. Unknown fields are preserved as opaque bytes during CRDT merge
    2. Old code ignores unknown fields for application logic
    3. Unknown fields are forwarded in gossip (pass-through)
    4. When the node upgrades, previously-merged unknown fields
       become usable with the new schema

  This works because CRDT merges are per-field:
    - Known fields: merge normally using the field's CRDT type
    - Unknown fields: merge using a generic LWWRegister fallback
      (last-writer-wins by timestamp — safe for pass-through)

  If the unknown field uses a CRDT type the old node doesn't
  understand (e.g., a new CRDT type added in a later protocol version):
    - The field is stored as opaque bytes
    - Merge uses byte-level LWW fallback
    - On upgrade, the node re-merges using the correct CRDT type
    - Temporary merge inaccuracy during the transition is self-correcting
```

## Migration Contract Execution Semantics

When a breaking schema change requires a `migration_contract`, the execution follows a strict protocol:

```
Migration contract execution:

  Input delivery:
    The migration contract receives the FULL old state as a single CBOR-encoded
    input via the LOAD opcode (key = "migration_input").
    Rationale: incremental migration adds complexity without benefit —
    state sizes are bounded by device tier (ESP32: 32 KB, Pi: 1 MB,
    Gateway: 256 MB), so full-state delivery is practical.

  Contract interface:
    // Entry point
    fn migrate(old_state: CBOR) -> Result<CBOR, MigrationError>

    // The contract:
    //   1. Reads old state from LOAD("migration_input")
    //   2. Transforms fields according to the new schema
    //   3. Writes new state to STORE("migration_output")
    //   4. Returns HALT (success) or ABORT (failure)

  Success criteria:
    1. Contract terminates with HALT (not ABORT)
    2. Output at STORE("migration_output") is valid CBOR
    3. Output conforms to the new StateSchema (all required fields present,
       correct CRDT types)
    4. Migration completes within max_cycles (from contract declaration)

  Failure modes:
    - Runtime exception (ABORT opcode): migration_failed, old state preserved
    - Wrong output shape (schema validation fails): migration_failed
    - Timeout (max_cycles exceeded): migration_failed, old state preserved
    - All failures are recoverable — old app version remains functional

  Determinism guarantee:
    Migration contracts MUST be deterministic (same as all MHR-Byte/WASM).
    Two nodes migrating the same state produce identical outputs.
    If nondeterminism is detected (different nodes get different outputs
    for the same input — detected via hash comparison during CRDT sync):
      - The output with the LOWER Blake3 hash wins (arbitrary but deterministic)
      - This should never happen if the contract is correctly written
      - Detection triggers a warning to the app publisher

  Rollback:
    No automatic rollback. If migration succeeds but causes application bugs:
      1. User can pin to old manifest hash (old state still accessible by hash)
      2. Publisher can release a new version with a fix
      3. Old DataObjects remain in MHR-Store indefinitely

  Partial migration:
    NOT supported. Migration is all-or-nothing per state object.
    Rationale: partial migration creates inconsistent state that violates
    schema invariants. If some fields can migrate independently, they
    should be separate DataObjects in the schema design.
```

## Partition Behavior

:::caution[Trade-off]
Breaking schema migrations are all-or-nothing per state object — partial migration is not supported. If a migration contract fails (runtime exception, wrong output shape, or timeout), the old version is preserved. This prioritizes state consistency over upgrade flexibility.
:::

A partitioned node that missed an upgrade continues running the old version. On reconnection:
1. CRDT state merges normally if schema is compatible
2. If schema is breaking: node detects version mismatch during CRDT sync
3. Node fetches new manifest via MHR-Name re-resolution
4. Runs migration locally, then state converges

## Rollback

There is no protocol-level rollback mechanism. If a new version is broken:
- Users can pin to an old manifest hash (local override)
- The publisher can publish a newer version that reverts changes
- Old manifests, contracts, and state remain available by content hash

## Example: Decentralized Forum

A community forum using Mehr primitives:

```
Forum application:

  State (MHR-Store):
    - ForumConfig: CRDT DataObject with forum name, rules, moderator list
    - Thread: one DataObject per thread (append-only CRDT log of post references)
    - Post: one DataObject per post (mutable — author can edit)

  Logic (MHR-Compute):
    - PostValidator contract: checks post format, size limits, rate limits
    - ModerationContract: checks if author is banned, if content matches filter rules
    - Runs on any node (MHR-Byte — works on ESP32)

  Events (MHR-Pub):
    - subscribe(Scope(Topic("forums", "portland-general")), Push)
    - New posts trigger envelope notifications to all subscribers

  Identity:
    - Forum members are Ed25519 keypairs
    - Moderators are listed in ForumConfig (by NodeID)
    - No separate registration — just start posting

  Discovery:
    - Forum name registered via MHR-Name: "portland-general@geo:portland"
    - Threads discoverable via MHR-DHT by content hash
```

**User experience**: Subscribe to the forum topic. Receive post notifications via MHR-Pub. Browse post envelopes (free). Fetch full posts on demand (paid if outside trust network). Post by creating a DataObject and publishing a notification. Moderators update the ForumConfig to ban users — the ModerationContract enforces it at validation time.

### Forum AppManifest

```
AppManifest {
    manifest_version: 1,
    app_version: 1,
    publisher: 0x3a7f...b2c1,                // forum developer
    created: 1042,                             // epoch 1042

    app_type: 0,                               // Full (contracts + UI)
    min_tier: 1,                               // Community (needs UI rendering)
    compute_tier: 1,                           // MHR-Byte (runs on ESP32)

    contract_count: 2,
    contracts: [
        Blake3("PostValidator bytecode"),
        Blake3("ModerationContract bytecode"),
    ],
    entry_contract: 0,                         // PostValidator is entry point

    ui_root: Some(Blake3("forum UI root")),

    state_schema_hash: Some(Blake3("forum state schema")),

    pub_topic_count: 1,
    pub_topics: [
        { scope_type: 0, suffix: "forums" },   // Geo — inherits user's geo scope
    ],

    dependency_count: 0,
    dependencies: [],

    name: "Mehr Forum",
    description_hash: Some(Blake3("README")),

    signature: Ed25519Sig(...),
}

Published as: "forum-app@topic:apps/forums" → AppManifest(manifest_hash)
```

**Upgrade to v2 (adds search)**:
1. Publisher adds a SearchIndex contract (contract_count: 3)
2. State schema adds `search_index` CRDT field (compatible_with includes v1 schema hash)
3. New manifest: app_version=2, new hashes
4. Rebind MHR-Name, notify via MHR-Pub
5. Users: fetch new manifest, download SearchIndex, init search_index field
6. Old state merges cleanly — additive migration

## Example: Collaborative Wiki

A wiki where multiple authors edit shared documents:

```
Wiki application:

  State (MHR-Store):
    - WikiPage: CRDT DataObject per page (text CRDT — e.g., RGA or Peritext)
    - PageIndex: CRDT DataObject mapping page titles to content hashes
    - EditHistory: append-only log of edit metadata (author, timestamp, summary)

  Logic (MHR-Compute):
    - MergeContract: CRDT merge rules for concurrent edits
    - AccessControl: checks editor permissions (open wiki vs. invited editors)
    - Runs as WASM on Community-tier+ (text CRDTs need more memory than MHR-Byte)

  Events (MHR-Pub):
    - subscribe(Node(wiki_owner_id), Push) for page update notifications
    - Editors receive real-time notifications of concurrent edits

  Identity:
    - Editors identified by Ed25519 keypair
    - Edit attribution is cryptographic (signed edits)

  Discovery:
    - Wiki registered via MHR-Name: "mehr-wiki@topic:documentation"
    - Pages discoverable by title via PageIndex or by hash via MHR-DHT
```

**Offline editing**: An editor on a partitioned node edits a page locally. The text CRDT records the operations. On reconnection, the CRDT merges automatically — no manual conflict resolution. Two editors changing different paragraphs merge cleanly. Two editors changing the same sentence produce a deterministic merge (last-writer-wins per character, or interleaving, depending on CRDT choice).

### Wiki AppManifest

```
AppManifest {
    manifest_version: 1,
    app_version: 1,
    publisher: 0x8e2d...f4a9,
    created: 1050,

    app_type: 0,                               // Full
    min_tier: 1,                               // Community (WASM + UI)
    compute_tier: 2,                           // WASM-Light

    contract_count: 2,
    contracts: [
        Blake3("MergeContract bytecode"),
        Blake3("AccessControl bytecode"),
    ],
    entry_contract: 0,

    ui_root: Some(Blake3("wiki UI root")),
    state_schema_hash: Some(Blake3("wiki state schema")),

    pub_topic_count: 1,
    pub_topics: [
        { scope_type: 1, suffix: "documentation" },  // Topic scope
    ],

    dependency_count: 0,
    dependencies: [],

    name: "Mehr Wiki",
    description_hash: Some(Blake3("Wiki README")),

    signature: Ed25519Sig(...),
}

Published as: "wiki-app@topic:apps/collaboration" → AppManifest(manifest_hash)
```
