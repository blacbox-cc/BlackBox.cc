# JarvisAI — System State & Version Scope

## 1. High-Level System Overview

JarvisAI is a local-first, event-driven cognitive assistant designed to execute user commands through natural language understanding while maintaining strict determinism and safety guarantees. At this stage, the system functions as a personal automation and information retrieval tool that operates entirely on the user's machine without requiring external API dependencies for core functionality.

### What JarvisAI Solves

- Provides natural language interface to system-level operations (file management, application control, information retrieval)
- Maintains conversation context and persistent memory across sessions
- Learns from user interactions through explicit feedback mechanisms
- Offers transparent decision-making with confidence scoring and trace visibility

### Explicit Non-Goals at This Stage

- Autonomous decision-making without user approval
- Predictive or proactive behavior without explicit user triggers
- Real-time continuous learning that modifies system behavior automatically
- Multi-user environments or networked operation
- Production-grade web interface or API endpoints
- Complex multi-step planning or task decomposition
- Integration with cloud services or third-party APIs as core dependencies

## 2. Core Architectural Principles

### Determinism

Every input produces a consistent, reproducible output given identical system state. NLU parsing, intent recognition, and skill dispatching follow deterministic rules. Confidence scores are computed using fixed algorithms without probabilistic elements unless explicitly configured.

### Separation of Concerns

The system enforces strict layering:

- Input Layer: Handles text, voice, and CLI input without processing logic
- NLU Layer: Transforms input to structured intent without execution
- Decision Layer: Selects skills based on intent without performing actions
- Execution Layer: Runs skills without interpreting results
- Reflection Layer: Analyzes outcomes without modifying system behavior

No layer may bypass another or perform responsibilities outside its scope.

### Local-First Design

All core functionality operates without network connectivity. Storage uses SQLite. Speech recognition uses offline models (Vosk). Configuration and data reside on local filesystem. External integrations are optional and never required for boot or basic operation.

### Safety and Explicit Approval Model

Skills execute only after successful intent recognition. Users maintain control through operational modes (SAFE, PASSIVE, ACTIVE). System never modifies configuration, installs software, or performs destructive operations without explicit user command. All actions are logged with full context.

### Layered Cognitive Processing

Processing follows a fixed pipeline: Normalization → Parsing → Intent Detection → Entity Extraction → Confidence Scoring → Skill Selection → Execution → Reflection. Each stage produces observable output. Failures at any stage halt processing and return explicit error information.

---

# v0.0.3 — Baseline Cognitive Core

## 3. Purpose of v0.0.3

v0.0.3 establishes the foundational technical infrastructure for JarvisAI. It serves as a stable baseline that proves the core architecture functions correctly without advanced features. This version exists to:

- Validate event-driven architecture with EventBus and Scheduler
- Demonstrate persistent memory across sessions
- Prove skill registration and dispatching mechanisms work reliably
- Establish testing methodology for future development
- Create a frozen reference point for architectural decisions

v0.0.3 is considered locked. No new features may be added. Only critical bugs that prevent boot, break determinism, or fail existing tests warrant fixes.

[Document continues with full specification for v0.0.3 and v0.0.4...]