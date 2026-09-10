# CyberSecGPT Deep Reasoning Brain — Implementation Directive

**Directive Version:** 2.1  
**Status:** Mandatory engineering supplement  
**Authority:** Subordinate to `CYBERSECGPT_MASTER_AUTONOMOUS_AI_BRAIN_SPECIFICATION.md`  
**Purpose:** Convert the CyberSecGPT native-AI mission into persistent, implementation-oriented instructions for coding agents such as Codex and GitHub Copilot.

> This document NEVER overrides the CyberSecGPT Master Autonomous AI Brain Specification.
> If this document and the master specification disagree, the master specification wins.
> Do not invent missing requirements to resolve a conflict. Record the conflict and preserve the authoritative architecture.

---

## 0. Instruction Stack, Canonical Location, and Authority

CyberSecGPT coding agents MUST load project doctrine in this order before substantial work:

```text
1. CYBERSECGPT_MASTER_SYSTEM_INSTRUCTIONS.md
        ↓
2. CYBERSECGPT_MASTER_AUTONOMOUS_AI_BRAIN_SPECIFICATION.md
        ↓
3. CYBERSECGPT_DEEP_REASONING_BRAIN_IMPLEMENTATION_DIRECTIVE.md
        ↓
4. REPOSITORY INSPECTION / ADRs / CURRENT MILESTONE
        ↓
5. PLAN → IMPLEMENT → TEST → VERIFY → EVIDENCE
```

### 0.1 Canonical documentation location

The canonical documentation location is:

```text
cybersecgpt-docs/
└── engineering/
    ├── CYBERSECGPT_MASTER_SYSTEM_INSTRUCTIONS.md
    ├── CYBERSECGPT_MASTER_AUTONOMOUS_AI_BRAIN_SPECIFICATION.md
    └── CYBERSECGPT_DEEP_REASONING_BRAIN_IMPLEMENTATION_DIRECTIVE.md
```

Repository-root copies of these documents are synchronized mirrors for standalone repository operation, Codex/Copilot discovery, offline work, and CI. They are not independent competing sources of truth.

### 0.2 Scope and conflict handling

- `CYBERSECGPT_MASTER_SYSTEM_INSTRUCTIONS.md` contains project-wide system/engineering instructions and is read first.
- `CYBERSECGPT_MASTER_AUTONOMOUS_AI_BRAIN_SPECIFICATION.md` is authoritative for CyberSecGPT native-AI architecture, mission, roadmap, model independence, reasoning, training, memory, retrieval, agents, inference, and high-assurance AI engineering.
- `CYBERSECGPT_DEEP_REASONING_BRAIN_IMPLEMENTATION_DIRECTIVE.md` is an implementation supplement and MUST remain subordinate to the two master documents within their scopes.
- If documents appear to conflict, do not silently reconcile them or invent a new hierarchy. Preserve the authoritative requirements, identify the conflicting statements and stop the conflicting change until the conflict is resolved.
- Never downgrade the native-AI independence, repository-boundary, verification, provenance, local/offline, or high-assurance requirements defined by the autonomous AI brain specification.

### 0.3 Protected master-system instructions

This directive pack MUST NOT create, replace, rewrite, normalize, or silently update `CYBERSECGPT_MASTER_SYSTEM_INSTRUCTIONS.md`.

That file is operator-owned project doctrine. The installer may locate it, verify it, hash it, and copy an exact canonical mirror into a repository that lacks a local copy, but it MUST NOT overwrite a differing copy automatically.

## 1. Mandatory Agent Contract

For every substantial CyberSecGPT architecture, model, reasoning, security, training, inference, memory, agent, repository, roadmap, or implementation task:

1. Locate and read `CYBERSECGPT_MASTER_SYSTEM_INSTRUCTIONS.md`.
2. Locate and read `CYBERSECGPT_MASTER_AUTONOMOUS_AI_BRAIN_SPECIFICATION.md`.
3. Read this directive.
4. Inspect the target repository and surrounding workspace before changing files.
4. Identify the applicable roadmap milestone.
5. Identify the repository that owns the responsibility.
6. State the intended change boundary.
7. Preserve current architecture unless evidence justifies an explicit architectural change.
8. Implement only the smallest coherent milestone slice.
9. Verify with automated and independent checks.
10. Produce evidence before calling the task complete.

A substantial task MUST NOT jump directly from a vague request to a large implementation.

Use:

```text
MISSION
→ REQUIREMENTS
→ ARCHITECTURE
→ THREAT MODEL
→ SECURITY CONTROLS
→ IMPLEMENTATION
→ TESTING
→ VERIFICATION
→ PACKAGING
→ DEPLOYMENT
→ ASSURANCE EVIDENCE
```

For smaller implementation tasks, use the compressed form:

```text
OBJECTIVE
→ INSPECT
→ PLAN
→ IMPLEMENT LIMITED CHANGE
→ TEST
→ VERIFY
→ REVIEW DIFF
→ RECORD EVIDENCE
```

---

## 2. Non-Negotiable Mission

CyberSecGPT is to evolve into an **independent native AI foundation-model ecosystem**, not a thin wrapper around proprietary remote AI APIs.

The long-term intelligence stack must be CyberSecGPT-controlled:

```text
TOKENIZER
→ DATASETS / DATA PIPELINE
→ MODEL ARCHITECTURE
→ PRETRAINING
→ POST-TRAINING
→ MODEL WEIGHTS
→ EVALUATION
→ REASONING
→ MEMORY
→ RETRIEVAL
→ KNOWLEDGE
→ AGENT ORCHESTRATION
→ SECURE TOOL RUNTIME
→ INFERENCE
→ QUANTIZATION
→ LOCAL RUNTIME
→ DISTRIBUTED SELF-HOSTED SERVING
→ NATIVE CYBERSECGPT API
→ APPLICATION PLATFORM
```

Proprietary remote AI providers MAY be optional adapters.

They MUST NOT be required for:

- core reasoning;
- code generation;
- cybersecurity analysis;
- training;
- model inference;
- memory;
- retrieval;
- agent orchestration;
- secure tool execution;
- local/offline CyberSecGPT operation.

The architectural independence test is:

```text
Internet: OFF
Third-party AI APIs: DISABLED

cybersecgpt run cybersecgpt-native
```

Core reasoning must still work using CyberSecGPT-controlled components, subject to available hardware.

---

## 3. Target Brain Architecture

Do not design CyberSecGPT as one giant language model only.

Design it as a **native cognitive system** with separable, testable subsystems:

```text
                         CYBERSECGPT COGNITIVE SYSTEM
                                    │
              ┌─────────────────────┴─────────────────────┐
              │                                           │
     NATIVE FOUNDATION MODELS                    COGNITIVE RUNTIME
              │                                           │
      tokenizer + weights                         planning + control
              │                                           │
              └─────────────────────┬─────────────────────┘
                                    │
                         DEEP REASONING ENGINE
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
    PLANNER / SEARCH          SPECIALIST SOLVERS         CRITICS / REVIEWERS
         │                          │                          │
         └──────────────────────────┼──────────────────────────┘
                                    │
                              VERIFIER LAYER
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
        LOGIC / SYMBOLIC       CODE / EXECUTION       EVIDENCE / RAG
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                         UNCERTAINTY / CONFIDENCE
                                    │
                             ACCEPT OR REVISE
```

The implementation must remain modular.

The cognitive runtime MUST support hybrid routing rather than assuming all work belongs in a foundation model. The target system therefore includes native neural models, retrieval/knowledge, classical and statistical ML, deterministic policy/rules, symbolic/graph engines, secure executable tools, and independent verification.

Each major subsystem requires:

- explicit interfaces;
- measurable inputs and outputs;
- versioning;
- provenance where relevant;
- resource bounds;
- security controls;
- testability;
- observability;
- reproducibility;
- known limitations.

---

## 4. Deep Reasoning Fabric

CyberSecGPT reasoning must extend beyond unstructured one-pass next-token generation.

### 4.1 Adaptive reasoning budgets

The runtime should support explicit reasoning-budget policies such as:

```text
REFLEX
NORMAL
DEEP
ULTRA
RESEARCH
EXHAUSTIVE
```

These are **runtime policy names**, not claims of intelligence.

The implementation must allow the controller to choose a budget using measurable factors such as:

- task complexity;
- uncertainty;
- safety impact;
- cost/resource budget;
- verification requirements;
- tool availability;
- time constraints;
- model capability.

Do not spend exhaustive compute on trivial work.

### 4.2 Candidate generation and search

For difficult tasks, support multiple candidate reasoning paths rather than a single unverified trajectory.

Conceptually:

```text
PROBLEM
  │
  ├─ CANDIDATE A ─┬─ A1
  │               └─ A2
  ├─ CANDIDATE B ─┬─ B1
  │               └─ B2
  └─ CANDIDATE C ─┬─ C1
                  └─ C2
          │
     EVALUATION
          │
     VERIFICATION
          │
       SYNTHESIS
```

Candidate search may use, where justified:

- best-of-N;
- self-consistency;
- beam/search techniques;
- graph search;
- tree search;
- verifier-guided search;
- constraint-guided search;
- tool-derived evidence;
- program execution feedback.

Search policies must be benchmarked. More branches are not automatically better.

### 4.3 Independent cognitive roles

Separate generation from verification.

A preferred reasoning lifecycle is:

```text
PLANNER
→ SOLVER
→ SKEPTIC
→ COUNTEREXAMPLE FINDER
→ DOMAIN REVIEWER
→ VERIFIER
→ FINAL SYNTHESIZER
```

The same model MAY temporarily fill multiple roles in early prototypes, but the architecture must not assume that self-review is equivalent to independent verification.

Where feasible, use separate models, separate prompts/policies, separate tool evidence, or deterministic validators.

### 4.4 Neural + symbolic + executable reasoning

Do not force the neural model to mentally simulate everything.

Route subproblems to the best available reasoning substrate:

```text
Natural language     → native neural model
Mathematics          → symbolic / numeric engine
Programming          → parser / compiler / tests / sandbox
Repository analysis  → AST / CFG / DFG / dependency graph
Cybersecurity        → authorized analyzers / telemetry / sandbox
Logic                → constraint / theorem / rule systems
Knowledge            → RAG / knowledge graph / evidence store
Facts                → provenance-aware retrieval
```

Tool output is evidence, not automatically truth. Validate tool results and preserve provenance.

---

## 5. Hybrid Intelligence Architecture

CyberSecGPT MUST NOT be designed as "LLM-only" intelligence.

The primary general-purpose neural reasoning substrate may be a native Transformer or another evidence-selected neural architecture, but it is only one component of the complete brain.

The production architecture should combine six intelligence classes:

| Intelligence class | Primary responsibilities |
|---|---|
| **Native foundation / deep-learning intelligence** | language, reasoning, coding, generation, planning, multimodal understanding |
| **Retrieval and knowledge intelligence** | embeddings, lexical search, dense/sparse/hybrid retrieval, reranking, RAG, knowledge graphs, provenance |
| **Predictive / classical ML intelligence** | classification, anomaly detection, clustering, forecasting, behavioral analytics, calibrated prediction |
| **Deterministic intelligence** | rules, authorization, policy, schemas, validation, compliance constraints, hard safety boundaries |
| **Agentic / executable intelligence** | secure tools, APIs, compilers, sandboxes, analyzers, workflows and controlled actions |
| **Verification intelligence** | critics, verifier models, static analysis, tests, evidence checking, uncertainty and acceptance decisions |

Mandatory principle:

> **Transformer/deep-learning models are the primary general-purpose neural reasoning substrate, not the exclusive computational substrate of CyberSecGPT.**

No single intelligence technique is assumed to be optimal for every task.

Architecture and routing decisions MUST be based on measurable requirements such as:

- quality;
- accuracy;
- calibrated uncertainty;
- determinism;
- security impact;
- latency;
- memory;
- compute;
- energy;
- offline capability;
- explainability;
- reproducibility;
- robustness;
- operating cost.

Do not replace a small deterministic or classical model with a large foundation model unless evaluation demonstrates a meaningful advantage.

### 5.1 Classical ML remains first-class

For specialized tasks, evaluate smaller methods alongside deep neural models.

Examples include:

```text
malicious / benign classification
    → calibrated classifier / gradient boosting / specialist neural classifier

network or endpoint anomaly detection
    → anomaly model + statistical baseline

user/entity behavior analytics
    → temporal + statistical + behavioral models

event clustering
    → clustering + embeddings

risk estimation
    → calibrated predictive model

time-series telemetry
    → dedicated temporal architecture

attack / entity relationships
    → graph algorithms / graph models / knowledge graph

language and code reasoning
    → CyberSecGPT native foundation / reasoning models
```

The agent MUST NOT interpret "native AI brain" as an instruction to replace every algorithm with a Transformer.

### 5.2 Deterministic controls are authoritative where required

Policy, authorization, capability boundaries, schema validation, release gates, and other hard constraints should use deterministic enforcement where possible.

A language model MAY propose an action.

A language model MUST NOT be the sole authority that grants itself permission to execute that action.

Use:

```text
MODEL PROPOSAL
→ POLICY CHECK
→ AUTHORIZATION
→ CAPABILITY CHECK
→ RESOURCE LIMIT
→ SANDBOX
→ EXECUTION
→ EVIDENCE
→ VERIFICATION
```

### 5.3 Verification is a separate intelligence class

Verification is not an afterthought.

A powerful CyberSecGPT response or action may combine:

```text
FOUNDATION MODEL
+ RAG
+ CLASSICAL ML
+ RULES
+ TOOLS
```

but should not be considered high-assurance until it also passes appropriate:

```text
VERIFIERS
+ TESTS
+ EVIDENCE CHECKS
+ UNCERTAINTY / ACCEPTANCE LOGIC
```

---

## 6. Intelligence Router

CyberSecGPT should possess an explicit **Intelligence Router** that selects the smallest competent and authorized intelligence substrate for each subproblem.

Conceptual architecture:

```text
                         TASK
                          │
                          ↓
                 INTELLIGENCE ROUTER
                          │
     ┌────────────────────┼────────────────────┐
     ↓                    ↓                    ↓
 FOUNDATION /          KNOWLEDGE          PREDICTIVE /
 REASONING MODEL        SYSTEM            CLASSICAL ML
     │                    │                    │
     └──────────────┬─────┴───────────┬────────┘
                    ↓                 ↓
             RULE / POLICY       SYMBOLIC / GRAPH
                 ENGINE              ENGINE
                    │                 │
                    └────────┬────────┘
                             ↓
                       NEED A TOOL?
                             │
                       yes ──┴── no
                        ↓          ↓
                  SECURE RUNTIME   │
                        │          │
                        └────┬─────┘
                             ↓
                         VERIFIER
                             │
                    ACCEPT / REVISE
```

### 6.1 Router inputs

The router should be able to consider:

```text
task_type
task_complexity
domain
safety_impact
authorization
uncertainty
latency_budget
compute_budget
memory_budget
required_accuracy
required_determinism
required_explainability
offline_requirement
available_models
available_tools
available_knowledge
verification_requirements
```

### 6.2 Router outputs

A routing decision should be representable as structured data containing, where applicable:

```text
selected_substrate
selected_model_or_engine
reasoning_budget
retrieval_policy
tool_policy
verification_policy
resource_budget
fallback
decision_provenance
```

Do not require hidden natural-language reasoning to reconstruct why a route was selected.

### 6.3 Example routing

Possible routes include:

```text
Natural-language reasoning
    → CyberSecGPT-General / CyberSecGPT-Reason

Programming
    → CyberSecGPT-Code
    → parser / compiler / tests when applicable

Cybersecurity investigation
    → CyberSecGPT-Cyber
    → retrieval + telemetry + rules + authorized tools + verifier

Semantic retrieval
    → CyberSecGPT-Embedding
    → hybrid retrieval
    → CyberSecGPT-Reranker

Anomaly detection
    → dedicated anomaly/statistical model

Structured policy decision
    → deterministic policy engine

Constraint problem
    → symbolic / constraint solver

Graph relationship problem
    → graph engine / knowledge graph / graph model

High-impact conclusion
    → independent verifier + evidence gate
```

### 6.4 Routing must be benchmarked

The router itself is an intelligence component and MUST be evaluated.

Measure at minimum where applicable:

- task success;
- model/engine selection accuracy;
- unnecessary escalation rate;
- unsafe routing rate;
- cost/compute efficiency;
- latency;
- fallback quality;
- verifier rejection rate;
- robustness to malformed/adversarial inputs.

Prefer the smallest competent route.

Do not route every request to the largest available model.

---

## 7. Hybrid Cybersecurity Intelligence and Untrusted-Data Boundary

Cybersecurity intelligence should deliberately combine neural, deterministic, statistical, retrieval, graph, and executable systems.

A reference defensive investigation flow is:

```text
SUSPICIOUS TELEMETRY / USER REQUEST
              │
              ↓
      NORMALIZATION / PARSING
              │
      ┌───────┼───────────────┬────────────────┐
      ↓       ↓               ↓                ↓
  RULES /   CLASSICAL ML   STATISTICAL     GRAPH /
SIGNATURES   / ANOMALY      BASELINE      CORRELATION
      │       │               │                │
      └───────┴───────────────┴────────────────┘
                         │
                         ↓
                CYBERSECGPT-CYBER
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       SIEM/EDR       KNOWLEDGE       THREAT INTEL
       EVIDENCE        / RAG           EVIDENCE
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                 REASONING / PLAN
                         │
                         ↓
              AUTHORIZATION + POLICY
                         │
                         ↓
                SECURE TOOL RUNTIME
                         │
                         ↓
                   EVIDENCE STORE
                         │
                         ↓
                     VERIFIER
                         │
                 ┌───────┴────────┐
                 ↓                ↓
              SUPPORTED        UNCERTAIN
                 │                │
                 ↓                ↓
               REPORT       GATHER / VERIFY MORE
```

### 7.1 Retrieved and observed data are untrusted inputs

Documents, webpages, logs, emails, tickets, source code, RAG chunks, tool output, threat-intelligence feeds, model memories, and other external content MUST be treated as data, not authority.

Untrusted data MUST NOT directly grant permissions or invoke privileged tools.

Use:

```text
UNTRUSTED DATA
→ PARSE / CLASSIFY
→ MODEL INTERPRETATION
→ PROPOSED ACTION
→ POLICY ENGINE
→ AUTHORIZATION
→ CAPABILITY CHECK
→ SANDBOX
→ EXECUTION
→ EVIDENCE
→ VERIFICATION
```

Do NOT implement:

```text
UNTRUSTED DOCUMENT
→ "RUN THIS COMMAND"
→ MODEL
→ PRIVILEGED EXECUTION
```

### 7.2 Evidence separation

Maintain clear distinctions between:

- user claims;
- retrieved claims;
- telemetry observations;
- model inferences;
- rule matches;
- ML predictions;
- tool observations;
- verifier conclusions.

A model-generated hypothesis is not equivalent to observed evidence.

### 7.3 Security-specific hybrid analytics

Where appropriate, CyberSecGPT may combine:

- deterministic signatures;
- Sigma/YARA-like rules;
- anomaly models;
- statistical baselines;
- graph correlation;
- event clustering;
- temporal analysis;
- native cyber reasoning models;
- RAG over authorized knowledge;
- code/static analysis;
- sandbox observations;
- SIEM/EDR/XDR telemetry;
- human/analyst-approved actions.

The correct combination is task-dependent and must be evaluated.

## 8. Native Model Family

CyberSecGPT should evolve as a **model family**, not only one monolithic checkpoint.

Candidate families include:

```text
CyberSecGPT-General
CyberSecGPT-Reason
CyberSecGPT-Code
CyberSecGPT-Cyber
CyberSecGPT-SOC
CyberSecGPT-Forensics
CyberSecGPT-Agent
CyberSecGPT-Embedding
CyberSecGPT-Reranker
CyberSecGPT-Multimodal
CyberSecGPT-Verifier
CyberSecGPT-Critic
CyberSecGPT-Reward
CyberSecGPT-Judge
```

The last four are implementation targets introduced by this directive to support verification-oriented reasoning. They are not claims of current capability.

Model names, sizes, and advertised capabilities MUST reflect measured implementation and evaluation.

---

## 9. Native Neural Architecture Research

Architecture selection is evidence-driven.

Candidate research may include:

- decoder-only Transformers;
- encoder-decoder models;
- sparse Transformers;
- Mixture-of-Experts;
- grouped-query attention;
- multi-query attention;
- local/global attention;
- sliding-window attention;
- recurrent memory;
- state-space components;
- retrieval-enhanced architectures;
- graph-enhanced reasoning;
- hybrid neural architectures;
- multimodal encoders;
- code-specialized representations.

Do not copy or claim proprietary internal architectures that are not public.

Evaluate candidates on:

- language quality;
- reasoning;
- coding;
- cybersecurity;
- context efficiency;
- latency;
- memory;
- training cost;
- hardware efficiency;
- scaling;
- robustness;
- reliability;
- reproducibility.

Complexity requires evidence.

---

## 10. Reasoning Training and Post-Training

The reasoning stack should be trainable and improvable through controlled methods such as:

- supervised instruction tuning;
- reasoning-focused post-training;
- preference optimization;
- verifier-guided training;
- rejection sampling;
- self-consistency data;
- reinforcement-learning techniques where justified;
- tool-use training;
- code-execution feedback;
- curriculum learning;
- distillation;
- synthetic data with provenance.

Every self-generated training example must maintain provenance.

Production weights MUST NOT self-promote.

Use:

```text
TRAIN
→ EVALUATE
→ BENCHMARK
→ RED-TEAM
→ VERIFY
→ COMPARE
→ APPROVE
→ SIGN
→ CANARY
→ MONITOR
→ PROMOTE OR ROLLBACK
```

---

## 11. Confidence and Uncertainty

CyberSecGPT must represent uncertainty explicitly where useful.

A reasoning result should be able to carry:

```text
result
confidence
evidence
assumptions
open_questions
contradictions
verification_status
model_version
reasoning_policy
tool_evidence
timestamp
```

Do not invent numeric confidence values without calibration.

A low-confidence or contradictory result should be capable of triggering:

```text
RETRIEVE MORE EVIDENCE
→ SEARCH ALTERNATIVES
→ RUN TOOL
→ ASK SPECIALIST
→ VERIFY AGAIN
→ DEFER / REPORT UNCERTAINTY
```

---

## 12. Persistent Memory

CyberSecGPT memory should support:

- working memory;
- conversation memory;
- episodic memory;
- semantic memory;
- procedural memory;
- project memory;
- architecture-decision memory;
- user-authorized preferences;
- knowledge memory;
- evidence memory.

Each durable memory record should be capable of storing:

```text
content
type
scope
provenance
confidence
created_at
updated_at
expires_at
verification_status
contradictions
access_policy
encryption_metadata
version
```

Retrieved memory MUST NOT automatically be treated as true.

Memory writes that can influence future engineering decisions should be reviewable and correctable.

---

## 13. Retrieval and Knowledge

The native knowledge layer must support full offline operation.

It may combine:

- lexical search;
- semantic search;
- embeddings;
- reranking;
- vector indexes;
- document stores;
- code indexes;
- AST indexes;
- repository graphs;
- dependency graphs;
- security knowledge graphs;
- evidence stores.

Generated statements and retrieved evidence must remain distinguishable.

RAG must preserve provenance.

---

## 14. Secure Tool and Agent Runtime

Tool execution must follow a trusted execution path:

```text
REQUEST
→ IDENTITY
→ SECURITY CONTEXT
→ MISSION CLASSIFICATION
→ POLICY CHECK
→ CAPABILITY CHECK
→ TOOL AUTHORIZATION
→ SANDBOX
→ EXECUTION
→ ARTIFACT INSPECTION
→ EVIDENCE COLLECTION
→ SECURITY REVIEW
→ APPROVAL
→ OUTPUT
```

Never silently assume access to:

- credentials;
- production systems;
- cloud accounts;
- repositories;
- networks;
- deployment environments;
- secrets.

Use least privilege, sandboxing, explicit capability grants, bounded resources, secret-safe logging, and rollback.

---

## 15. Cybersecurity Safety Boundary

CyberSecGPT may support powerful cybersecurity engineering, including offensive security **only for authorized penetration testing and red-team contexts**.

Prioritize:

- protection;
- detection;
- analysis;
- hardening;
- authorized testing;
- simulation;
- investigation;
- verification.

"Stealth" means defensive operational discretion such as reduced attack surface, privacy, compartmentalization, minimal telemetry, and local/offline operation.

It does NOT mean malicious concealment, unauthorized persistence, evasion of legitimate security controls, or malware stealth.

Do not autonomously design lethal targeting, weapon selection, firing, or autonomous engagement systems.

---

## 16. Repository Ownership Is Mandatory

Respect CyberSecGPT repository boundaries.

Examples:

- `cybersecgpt-foundation` — stable, low-dependency contracts only;
- `cybersecgpt-reasoning` — planning, decomposition, reasoning control, search, decision systems;
- `cybersecgpt-memory` — persistent structured memory;
- `cybersecgpt-tokenizer` — tokenizer architecture and vocabulary;
- `cybersecgpt-datasets` — dataset governance, provenance, curation, processing;
- `cybersecgpt-training` — training pipelines and checkpoints;
- `cybersecgpt-inference` — inference and serving;
- `cybersecgpt-runtime` — sandboxing, secure execution, agent runtime;
- `cybersecgpt-evaluation` — TEVV, robustness, regression, adversarial evaluation;
- `cybersecgpt-benchmarks` — standardized benchmarks;
- `cybersecgpt-security` — platform security architecture and defensive controls;
- `cybersecgpt-api` — native model/services API;
- `cybersecgpt-platform` — integrated platform composition.

Do not create a new repository merely because a new feature is interesting. Create one only when existing repositories cannot cleanly own the responsibility.

### Foundation trust-anchor rule

`cybersecgpt-foundation` MUST remain small, stable, auditable, and dependency-controlled.

Do NOT put into Foundation:

- large ML frameworks;
- model runtimes;
- GUI frameworks;
- product-specific logic;
- SOC/SIEM/EDR engines;
- cloud SDKs;
- databases;
- licensing/subscription logic.

---

## 17. Roadmap Discipline

Honor the master roadmap:

```text
P0–P4   Foundation primitives                     COMPLETE
P5      Native Brain Architecture
P6      CyberSecGPT Tokenizer v1
P7      Dataset Governance and Data Pipeline
P8      Base Neural Architecture
P9      Native Training Engine
P10     First Native Pretrained CyberSecGPT Model
P11     Instruction/Post-Training Engine
P12     Advanced Reasoning Engine
P13     Embedding and Retrieval Models
P14     Persistent Memory
P15     Secure Agent Runtime
P16     Native Local Inference Runtime
P17     Quantization and Hardware Optimization
P18     Distributed Online Inference
P19     Native CyberSecGPT API
P20     Code Intelligence Model
P21     Cybersecurity Intelligence Models
P22     Multimodal Architecture
P23     Autonomous Secure Software Factory
P24     TEVV and Adversarial Evaluation
P25     Offline/Air-Gapped CyberSecGPT
P26     High-Assurance Deployment Profiles
P27     Integrated CyberSecGPT Engineering Studio
```

Do not collapse future milestones into Foundation.

A current milestone MAY create interfaces or research artifacts required by future milestones, but must not silently implement unrelated roadmap phases.

### Deep-reasoning mapping

Use this mapping unless the master roadmap is explicitly revised:

- **P5:** cognitive interfaces, hybrid-intelligence architecture, intelligence-router contracts, reasoning-control abstractions, verifier interfaces, policy/tool trust boundaries, architecture ADRs;
- **P8:** trainable neural architecture experiments;
- **P9:** training support;
- **P10:** first native model;
- **P11:** reasoning-oriented post-training;
- **P12:** adaptive reasoning budgets, candidate search, planning, hybrid intelligence routing/orchestration, critics, verifier orchestration;
- **P13:** embeddings, retrieval and reranking;
- **P14:** persistent confidence/provenance-aware memory;
- **P15:** secure tool/agent execution;
- **P16–P18:** native local and distributed inference;
- **P20–P22:** specialist code, cyber and multimodal intelligence, including benchmarked use of classical/statistical/graph methods where they outperform or complement foundation models;
- **P23–P24:** secure software factory and rigorous TEVV.

---

## 18. Mandatory Pre-Change Inspection

Before modifying any CyberSecGPT repository, inspect:

1. current branch;
2. working tree;
3. recent commits;
4. architecture;
5. public API;
6. tests;
7. distribution boundaries;
8. current milestone;
9. dependency direction;
10. nearby documentation and ADRs.

Do not overwrite successful work or silently undo established architecture.

Preferred workflow:

```text
OBJECTIVE
→ INSPECT
→ DEFINE MILESTONE
→ CREATE BRANCH
→ IMPLEMENT
→ FOCUSED TESTS
→ FULL QUALITY GATE
→ REVIEW DIFF
→ BUILD
→ VERIFY DISTRIBUTION
→ STAGE EXACT FILES
→ REVIEW STAGED DIFF
→ COMMIT
→ PUSH
→ VERIFY REMOTE
```

Do not commit, push, deploy, publish, or modify remote state unless the user/task authorization permits it.

---

## 19. Production Engineering Standard

Production code should emphasize:

- strong typing;
- explicit interfaces;
- deterministic behavior where feasible;
- defensive validation;
- bounded resource consumption;
- safe parsing;
- clear exception boundaries;
- secure temporary-file handling;
- secret-safe logging;
- dependency minimization;
- concurrency safety;
- clean shutdown;
- observability;
- testability;
- reproducibility.

Sophistication must serve correctness, security, performance, reliability, or maintainability.

---

## 20. Verification Is Part of Implementation

AI-generated code is untrusted until verified.

Use the checks appropriate to the change:

- unit tests;
- integration tests;
- system tests;
- regression tests;
- property-based tests;
- fuzzing;
- static analysis;
- type checking;
- linting;
- dependency auditing;
- SBOM validation;
- container scanning;
- infrastructure validation;
- performance tests;
- fault injection;
- adversarial ML evaluation;
- model evaluation;
- reproducibility checks.

A successful build alone is not proof of correctness.

Prefer:

```text
PLAN
→ EXECUTE LIMITED STEP
→ VERIFY
→ RECORD EVIDENCE
→ CONTINUE
```

over large unverified batches.

---

## 21. Definition of Done

A substantial task is NOT complete until the agent can report:

```text
MISSION / OBJECTIVE
APPLICABLE MASTER-SPEC REQUIREMENTS
ROADMAP MILESTONE
TARGET REPOSITORY
ARCHITECTURAL DECISIONS
INTELLIGENCE ROUTING / SUBSTRATE DECISIONS (when applicable)
THREAT / SECURITY CONSIDERATIONS
FILES CHANGED
TESTS RUN
STATIC / TYPE / SECURITY CHECKS RUN
BUILD RESULT
BENCHMARK RESULT (when applicable)
KNOWN LIMITATIONS
RESIDUAL RISKS
ROLLBACK NOTES
EVIDENCE
```

If a required check cannot be run, say exactly why.

Never report a test, benchmark, build, scan, or verification as passed unless it was actually executed and its result observed.

---

## 22. Assurance Evidence

For high-impact releases or deployments, prepare an Assurance Manifest where appropriate containing:

- Mission ID;
- Project ID;
- Build ID;
- source commit;
- architecture version;
- model version;
- tokenizer version;
- dataset version;
- dependency lock;
- SBOM;
- threat model;
- security controls;
- tests and coverage;
- static-analysis evidence;
- dependency-analysis evidence;
- fuzzing evidence;
- benchmark/evaluation evidence;
- artifact hashes;
- signatures;
- reproducibility status;
- approval chain;
- deployment profile;
- known limitations;
- residual risks.

Do not use labels such as "government-grade", "military-grade", "superintelligent", or "Gen-6+" as capability claims without measurable evidence.

---

## 23. Agent Response Protocol

When given a substantive implementation request, the coding agent should structure its work internally around:

```text
1. SPEC CHECK
2. REPOSITORY INSPECTION
3. MILESTONE / SCOPE
4. REQUIREMENTS
5. ARCHITECTURE
6. SECURITY / THREAT MODEL
7. IMPLEMENTATION
8. TESTING
9. VERIFICATION
10. DIFF REVIEW
11. EVIDENCE
12. NEXT SAFE MILESTONE
```

The agent should not repeatedly ask for information already available in the repository or master specification.

If the request is broad, choose the smallest useful milestone that advances the roadmap without violating repository boundaries.

If the task conflicts with the authoritative specification, do not silently follow the conflicting path. Explain the conflict and preserve the master specification unless the user explicitly updates the authoritative architecture.

---

## 24. Implementation Principle

The target is not to imitate proprietary frontier models.

The target is to build a **CyberSecGPT-native, measurable, reproducible reasoning ecosystem** combining:

```text
NATIVE FOUNDATION MODELS
+
HYBRID INTELLIGENCE ROUTING
+
CLASSICAL / STATISTICAL ML
+
DETERMINISTIC RULES / POLICY
+
ADAPTIVE REASONING
+
SEARCH / PLANNING
+
SPECIALIST MODELS
+
PERSISTENT MEMORY
+
RAG / KNOWLEDGE GRAPHS
+
SYMBOLIC / EXECUTABLE REASONING
+
SECURE TOOL USE
+
CRITICS / VERIFIERS
+
UNCERTAINTY ESTIMATION
+
CONTROLLED POST-TRAINING
+
LOCAL / OFFLINE INFERENCE
+
SELF-HOSTED DISTRIBUTED INFERENCE
+
TEVV / ASSURANCE EVIDENCE
```

Every advanced capability must be earned by implementation, benchmarking, testing, verification, and evidence.
