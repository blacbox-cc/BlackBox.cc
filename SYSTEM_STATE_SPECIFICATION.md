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

## 4. Implemented Capabilities (In Scope)

### Context Management

**Responsibilities:**
- Maintain conversation history within single session
- Store up to 20 recent interactions in memory (configurable via `short_term_memory_max`)
- Provide retrieval of recent context for NLU pipeline
- Clear context on session end

**Inputs:**
- User input text
- Intent recognition results
- Skill execution outcomes

**Outputs:**
- Ordered list of recent interactions
- Context summary for current session

**Guarantees:**
- Thread-safe access to conversation history
- No data persistence between process restarts in v0.0.3
- Context cleared automatically if memory limit exceeded

### Memory System

**Responsibilities:**
- Persist conversations to SQLite database
- Store factual knowledge with confidence weights
- Record system events with timestamps
- Support retrieval of historical data

**Inputs:**
- Conversation pairs (user input, system response)
- Facts as key-value pairs with confidence scores
- Events as typed messages with payloads

**Outputs:**
- Last N conversations ordered by recency
- Facts by key with confidence and update timestamp
- Events filtered by type and time range

**Guarantees:**
- Thread-safe database operations using locks
- Automatic database creation if missing
- No data loss during normal shutdown
- Conversations persist indefinitely

### Skill System

**Responsibilities:**
- Register skills mapped to intent names
- Validate skill availability before execution
- Dispatch intents to corresponding skill classes
- Return structured results from skill execution

**Inputs:**
- Intent name (string)
- Entities dictionary (extracted from NLU)
- System state or JarvisCore instance

**Outputs:**
- Success/failure indication
- Result data or error message
- Execution metadata (timing, resources used)

**Guarantees:**
- Skills execute in isolation
- Failed skill execution does not crash system
- Unregistered intents return explicit error
- Skills receive validated inputs only

**Available Skills (v0.0.3):**
- get_time: Returns current system time
- system_status: Reports runtime metrics
- create_note: Writes text to filesystem
- search_file: Finds files by name pattern
- summarize_recent_activity: Reports session summary
- analyze_session_value: Evaluates session productivity
- research_and_contextualize: Provides context for queries
- analyze_system_health: Reports component health
- what_do_you_know_about_me: Lists stored user facts
- evaluate_user_session: Analyzes user behavior patterns
- system_auto_optimization: Reports optimization opportunities
- auto_programming: Code generation assistance

### Eventing and Scheduling

**Responsibilities:**
- Publish events to registered subscribers
- Queue events for asynchronous processing
- Execute scheduled tasks at specified times
- Manage worker threads for concurrent event handling

**Inputs:**
- Event objects with type and data payload
- Handler functions subscribed to event types
- Scheduled tasks with cron-like specifications

**Outputs:**
- Event delivery to all subscribers
- Execution logs for handlers
- Task completion notifications

**Guarantees:**
- Events delivered in order within single thread
- No event lost unless system crash
- Handlers execute in isolation
- Scheduler persists across shutdown/restart

**Core Events:**
- EVENT_INPUT_TEXT: User provided text input
- EVENT_INPUT_VOICE: User provided voice input
- EVENT_NLU_INTENT: NLU pipeline produced intent
- EVENT_JARVIS_RESPONSE: System generated response

### Reflection and Insight (Read-Only)

**Responsibilities:**
- Observe skill execution outcomes
- Detect usage patterns in conversation history
- Generate learning insights without system modification
- Identify repeated user requests

**Inputs:**
- Conversation history from storage
- Skill execution results
- Session duration and command count

**Outputs:**
- Pattern summaries (most frequent intents, time distributions)
- Skill gap analysis (requests without matching skills)
- Learning targets (areas for improvement)

**Guarantees:**
- No modification of system configuration
- No automatic behavior changes
- Insights generated only on explicit request
- Analysis limited to single user's data

### CLI Behavior

**Responsibilities:**
- Display formatted output with colors and structure
- Accept text commands and special control sequences
- Show system status and debug information
- Handle voice toggle and mode switching

**Inputs:**
- User text commands
- System responses from skills
- Status updates from core components

**Outputs:**
- Formatted text to stdout
- Color-coded severity levels (info, warning, error)
- Progress indicators for long operations
- Structured tables for status reports

**Special Commands:**
- `ayuda`: Display available skills
- `status`: Show system status
- `sesiones`: List active sessions
- `modo [MODE]`: Switch operational mode
- `voz`: Toggle voice input
- `analizar`: Run active learning analysis
- `propuestas`: Show improvement proposals
- `salir` / `exit`: Shutdown system

**Guarantees:**
- CLI always accepts input even during errors
- Colors disabled if terminal does not support ANSI
- Voice input toggleable at runtime
- Exit command always stops system gracefully

## 5. Non-Goals and Explicit Exclusions

### Not Implemented in v0.0.3

- Configuration validation with schema enforcement
- Health checks for individual components
- Graceful degradation when components fail
- NLU trace visibility in debug mode
- Confidence threshold enforcement
- Error messages with cause and suggested fixes
- Typed exception hierarchy
- Component initialization tracking
- Detailed logging with structured context
- Pre-check validation before skill execution
- Timeout protection for long-running skills
- Parallel skill execution
- Background task management
- User feedback collection for intent corrections
- Decision pattern learning from feedback
- Spell correction in NLU
- Ambiguity detection and handling
- Explicit layered NLU pipeline (normalization → parsing → intent)
- Multi-user session management
- Operational mode restrictions
- Permission system for actions
- Audit logs for executed commands
- Multi-step planning or task decomposition
- Dry-run simulation of commands
- Web dashboard or API endpoints

### Deliberately Unsupported

- Cloud service dependencies
- Third-party API requirements for core features
- Automatic software installation
- Destructive filesystem operations without confirmation
- Network operations without user command
- Background autonomous tasks
- Predictive suggestions without explicit request

## 6. Quality, Testing, and Safety Guarantees

### Test Coverage Expectations

v0.0.3 includes test scripts in `tests_verify/` directory:

- `test_boot.py`: Validates system initialization
- `test_cli.py`: Tests CLI input/output
- `test_integration.py`: End-to-end interaction tests
- `test_jarvis_complete.py`: Full system validation

Tests must pass on clean boot without configuration modifications. Test scripts exit with non-zero status on failure.

### Thread-Safety Assumptions

- JarvisStorage uses locks for SQLite operations
- EventBus queues events safely across threads
- ContextManager assumes single-session access
- Skill execution may occur on worker threads

No guarantee of thread-safety for skills that modify shared state. Skill developers responsible for synchronization.

### Failure Behavior

- Uncaught exceptions print stack trace to stdout
- Failed boot exits with non-zero status code
- Failed skill execution returns error dict
- Voice pipeline failure falls back to CLI automatically
- Missing configuration file causes boot failure

System does not attempt recovery from critical component failures. Explicit restart required.

### Boot Guarantees

- System initializes in under 5 seconds on typical hardware
- All core components initialized before accepting input
- Failed initialization prints component name and error
- Boot sequence deterministic (same order every time)

## 7. Definition of Done for v0.0.3

v0.0.3 is considered complete and valid when:

- All test scripts in `tests_verify/` pass without modification
- System boots without warnings on clean Python 3.9+ environment
- CLI accepts commands and produces output immediately after boot
- At least 10 skills registered and executable
- Conversations persist to database across restarts
- Voice input works with Vosk models when enabled
- EventBus processes events without deadlocks during 100+ command session
- No memory leaks detectable during 24-hour operation
- Documentation in `docs/architecture.md` describes implemented components accurately

v0.0.3 is now frozen. This version serves as baseline for cognitive layer improvements in v0.0.3.1.

---

# v0.0.3.1 — Explicit Reasoning Layer

## 8. Purpose of v0.0.3.1

v0.0.3.1 introduces the first real reasoning layer in JarvisAI without adding intelligence or autonomy. This version exists to make decision-making explicit, observable, and explainable while maintaining complete determinism and backward compatibility.

### Problem Statement

In v0.0.3, the flow is: text → intent → skill

This is pattern matching, not reasoning. The system cannot explain why it chose an action, what alternatives were considered, or why they were rejected.

### Solution Approach

v0.0.3.1 restructures the cognitive pipeline to:

1. Separate observation from interpretation
2. Generate multiple intent hypotheses with explanations
3. Make a single decision with explicit reasoning
4. Record the complete decision context
5. Allow retrospective explanation via "why" command

This is NOT machine learning. This is NOT autonomous behavior. This is structured decision representation.

### Scope Boundaries

v0.0.3.1 changes internal representation only. From a user perspective:
- System behaves identically to v0.0.3 by default
- No new skills added
- No autonomous actions introduced
- No external dependencies required
- All existing tests continue to pass

The only visible change is the ability to ask "why" after any command.

## 9. Cognitive Architecture Changes

### New Cognitive Pipeline

The system now enforces this explicit pipeline:

```
UserInput
  ↓
Observation (raw text capture)
  ↓
Interpretation (NLU produces multiple hypotheses)
  ↓
Decision (select one hypothesis with reasoning)
  ↓
Action (execute skill if confidence sufficient)
  ↓
Outcome (capture result)
  ↓
Record (persist decision trace)
```

Each stage has distinct responsibilities and produces observable artifacts.

### Decision Model

New central data structure in `brain/decision.py`:

**Decision class contains:**
- decision_id: Unique UUID for this decision
- decision_timestamp: When decision was made
- raw_input: Original user text
- normalized_input: Text after normalization
- intent_candidates: List of IntentHypothesis objects
- selected_intent: Chosen intent name or None
- confidence: Float 0.0-1.0 for selected intent
- rejected_intents: List of intent names not chosen
- reasoning: Human-readable explanation of choice
- entities: Extracted entities dictionary
- execution_allowed: Boolean indicating if action may proceed
- decision_trace: List of reasoning steps

**Guarantees:**
- Decision object created for every input
- Decision contains complete context for retrospection
- Decision does not execute actions
- Decision serializable to JSON for persistence

### IntentHypothesis Model

Each hypothesis represents one possible interpretation:

**IntentHypothesis class contains:**
- intent_name: String identifier
- score: Float 0.0-1.0 confidence
- matched_patterns: List of regex/rule matches
- explanation: String describing why this intent matches
- supporting_entities: Entities that support this interpretation

**Scoring Rules:**
- Score computed deterministically from pattern matches
- Higher score indicates stronger pattern match
- Score does NOT use ML models or neural networks
- Ties broken by pattern specificity or registration order

### NLU Pipeline Refactoring

NLUPipeline modified to produce structured decisions:

**What Changes:**

1. Normalization remains unchanged (deterministic rules)

2. New method `generate_hypotheses(normalized_text)`:
   - Returns List[IntentHypothesis]
   - Minimum 0 hypotheses (unknown input)
   - Maximum N hypotheses (all patterns checked)
   - Each hypothesis includes explanation

3. New method `select_intent(hypotheses)`:
   - Takes List[IntentHypothesis]
   - Applies deterministic selection rules
   - Returns Decision object
   - Generates reasoning text

4. Modified method `process(text, eventbus)`:
   - Returns Decision object instead of dict
   - Maintains backward compatibility through Decision.to_dict()
   - Emits semantic events (INTERPRETATION_COMPLETED, DECISION_MADE)

**Selection Algorithm:**

```
IF no hypotheses:
  selected_intent = "unknown"
  reasoning = "No patterns matched input"
ELSE:
  selected = hypothesis with highest score
  reasoning = f"Selected {selected.intent_name} (score={score}) because {selected.explanation}"
  IF score < confidence_threshold:
    reasoning += "; low confidence, requesting confirmation"
```

**Guarantees:**
- Every input produces exactly one Decision
- Selection deterministic for identical input
- Reasoning text always generated
- No external API calls

### Dispatcher Responsibility Reduction

SkillDispatcher no longer interprets intent. Responsibilities now:

**What Dispatcher Does:**
- Receives Decision object (not raw text)
- Validates Decision.execution_allowed
- Checks confidence against threshold
- Retrieves skill from registry
- Executes skill.run()
- Returns execution result

**What Dispatcher Does NOT Do:**
- Parse text
- Generate intents
- Calculate confidence
- Make decisions about which skill to run

**Interface Change:**

Old: `dispatcher.dispatch(intent_name, entities, core)`
New: `dispatcher.dispatch_decision(decision, core)`

Decision object contains all necessary context. Dispatcher trusts Decision.selected_intent.

### Semantic Events

EventBus now carries semantic meaning through new event types:

**New Event Types:**
- EVENT_OBSERVATION_CREATED: Raw input captured
- EVENT_INTERPRETATION_COMPLETED: NLU produced hypotheses
- EVENT_DECISION_MADE: Decision object finalized
- EVENT_ACTION_EXECUTED: Skill completed
- EVENT_OUTCOME_RECORDED: Result persisted

**Event Payload Structure:**

```
EVENT_DECISION_MADE:
{
  "decision_id": "uuid-string",
  "selected_intent": "intent_name",
  "confidence": 0.85,
  "alternatives_count": 3,
  "reasoning": "Selected because...",
  "timestamp": "iso-timestamp"
}
```

**Guarantees:**
- Events emitted in pipeline order
- Each event contains decision_id for correlation
- Event data immutable after emission
- Handlers receive read-only event objects

## 10. Observable Intelligence Features

### Why Command

New CLI special command: `why`

**Functionality:**
- Displays reasoning for last executed decision
- Shows selected intent with confidence
- Lists alternative hypotheses with scores
- Prints rejection reasoning for top alternatives
- Shows matched patterns and entities

**Output Format:**

```
[DECISION] Last command: "open spotify"

Selected: open_app (confidence: 87%)
Reason: Matched pattern "abrir|lanzar|iniciar {app_name}" with entity app_name=spotify

Alternatives considered:
  search_file (42%) - Matched pattern "buscar {filename}" but no filename entity detected
  get_info (31%) - Matched pattern "información" with low specificity

Rejected: search_file, get_info
Entities: {"app_name": "spotify"}
```

**Guarantees:**
- Command works immediately after any input
- Reasoning reflects actual decision logic
- No post-hoc rationalization
- Output deterministic for same decision

### Decision Trace Visibility

Decision objects stored in-memory for current session:

**Storage:**
- Last 20 decisions kept in RuntimeState.decision_history
- Accessible via core.get_last_decision()
- Cleared on session end
- Not persisted to database in v0.0.3.1

**Access:**
- CLI `why` command uses last decision
- Debugging tools can inspect decision_history
- Future skills can query decision context

## 11. Backward Compatibility Guarantees

### What Does NOT Change

**User Experience:**
- All existing commands work identically
- Same response times
- Same skill execution behavior
- Same error handling
- No new configuration required

**APIs:**
- NLUPipeline.process() returns compatible object
- Decision.to_dict() produces same structure as v0.0.3
- Skills receive same parameters
- EventBus interface unchanged

**Tests:**
- All v0.0.3 test scripts pass without modification
- Test assertions remain valid
- No test rewrites required

**Performance:**
- Decision object creation adds under 1ms overhead
- Hypothesis generation deterministic
- No network calls
- No blocking operations

### Migration Path

Systems running v0.0.3 upgrade to v0.0.3.1 with zero code changes:

1. Decision objects backward compatible with dict access
2. EventBus accepts new semantic events without handler registration
3. SkillDispatcher supports both old and new dispatch methods temporarily
4. CLI recognizes `why` command but does not require it

## 12. Implementation Constraints

### What is Explicitly Forbidden

- Machine learning models
- Neural networks
- Probabilistic inference beyond simple scoring
- Autonomous action execution
- Multi-step planning
- Self-modification
- External API dependencies
- Async/await introduction
- Refactoring existing working code unnecessarily

### What is Explicitly Required

- Decision object for every user input
- IntentHypothesis list for every interpretation
- Reasoning text for every decision
- Deterministic selection algorithm
- No execution within Decision class
- Complete decision trace
- "why" command functionality

### Technical Standards

**Code Quality:**
- Type hints for all new classes
- Docstrings for all public methods
- Unit tests for Decision and IntentHypothesis
- Integration test for "why" command

**Documentation:**
- "How Jarvis Decides" document created
- Decision model documented with examples
- Reasoning algorithm specified
- Event flow diagram updated

## 13. Definition of Done for v0.0.3.1

v0.0.3.1 is considered complete when:

### Functional Completeness

- Decision class implemented in `brain/decision.py`
- IntentHypothesis class implemented in `brain/decision.py`
- NLUPipeline refactored to generate hypotheses
- NLUPipeline.select_intent() creates Decision objects
- SkillDispatcher accepts Decision objects
- EventBus emits semantic events (OBSERVATION_CREATED through OUTCOME_RECORDED)
- CLI `why` command displays last decision reasoning
- RuntimeState stores decision_history (last 20)

### Behavioral Verification

- All v0.0.3 tests pass without modification
- New test: `test_decision_creation.py` validates Decision structure
- New test: `test_hypothesis_generation.py` validates multiple hypotheses
- New test: `test_why_command.py` validates reasoning display
- Integration test: 100 commands produce 100 valid Decision objects
- Stress test: 1000 decisions created without memory leak

### Documentation Completeness

- `docs/how_jarvis_decides.md` created with:
  - Pipeline diagram
  - Decision model specification
  - Selection algorithm pseudocode
  - Reasoning generation rules
  - Examples of good/bad decisions
- `SYSTEM_STATE_SPECIFICATION.md` updated (this document)
- Docstrings in all new classes
- Comments explaining non-obvious selection logic

### Performance Guarantees

- Decision creation under 1ms overhead
- Hypothesis generation under 5ms for typical input
- "why" command responds in under 100ms
- No degradation in skill execution time
- Memory usage increase under 5MB for decision_history

### Explainability Validation

- Every Decision has non-empty reasoning text
- Reasoning accurately reflects selection algorithm
- Alternative hypotheses listed when applicable
- Rejection reasons explicit
- No placeholder or generic text

### Backward Compatibility Confirmation

- v0.0.3 configuration files work unchanged
- Skills receive same parameters
- Event handlers function without modification
- CLI commands (except "why") behave identically
- Upgrade requires no manual intervention

v0.0.3.1 introduces reasoning infrastructure without changing observable behavior. Users gain explainability. Developers gain structured decision artifacts. The system remains deterministic, local, and safe.

---

# v0.0.4 — Stability & Observability Release

## 14. Purpose of v0.0.4

v0.0.4 exists to make JarvisAI production-ready at small scale by addressing operational reliability and debuggability. While v0.0.3.1 provides explicit reasoning capabilities, v0.0.4 ensures the system fails gracefully, reports problems clearly, and remains maintainable under operational stress.

### Problems Solved

- Silent failures: Components fail without notification
- Unclear errors: Users see stack traces instead of actionable messages
- Invalid configuration: No validation until runtime crash
- Component coupling: Failures cascade unpredictably
- Missing health monitoring: Cannot detect degraded state
- Insufficient error context: Cannot debug remote failures

Note: NLU decision transparency already addressed in v0.0.3.1 through Decision model and "why" command.

v0.0.4 adds no major features. All changes strengthen reliability and observability of v0.0.3.1 functionality.

## 9. Scope of Changes (In Scope)

### Error Handling Improvements

**What is Added:**

Typed exception hierarchy in `system/core/exceptions.py`:
- JarvisException: Base class with message and context
- BootError: Critical initialization failure
- NLUError: Intent recognition failure
- SkillError: Skill execution failure (SkillNotFoundError, SkillTimeoutError, SkillDependencyError)
- ConfigError: Configuration validation failure (ConfigValidationError, MissingConfigError)
- MemoryError: Storage operation failure (MemoryQueryError)
- SessionError: Session management failure (SessionNotFoundError)
- VoiceIOError: Audio input/output failure (STTError, TTSError)

**What Changes:**

All component initialization wrapped in try-catch blocks. Exceptions include context dictionaries with diagnostic information. Error messages distinguish between user-facing explanation and technical details.

**Error Presentation:**

New ErrorPresenter in `system/core/error_presenter.py` formats exceptions as:
- User message: Plain language explanation
- Cause: Why the error occurred
- Context: Relevant state information
- Suggestion: Recommended action

Example output:
```
[ERROR] Failed to execute skill
Cause: Skill 'open_app' not found in registry
Context: Available skills: get_time, system_status, create_note
Suggestion: Use 'ayuda' command to see available skills
```

**Guarantees:**

- No uncaught exceptions in core components
- All errors logged with full context
- Stack traces suppressed unless `crash_on_error` config is true
- Users never see technical jargon without explanation

### Configuration Validation

**What is Added:**

ConfigValidator in `system/config_validator.py`:
- Schema-based validation with type checking
- Required field enforcement
- Default value injection
- Custom validator functions
- Enum-like options validation

Schema defines all configuration fields:
- name (string, required)
- version (string, required)
- data_collection (boolean, default: false)
- tts (boolean, default: false)
- voice_enabled (boolean, default: true)
- workers (integer, default: 4, validator: 1-16 range)
- debug_nlu (boolean, default: false)
- log_level (string, options: DEBUG, INFO, WARNING, ERROR)
- short_term_memory_max (integer, default: 20, validator: 5-100 range)
- crash_on_error (boolean, default: false)

**What Changes:**

JarvisCore.__init__ validates configuration before initializing components. Invalid configuration raises ConfigValidationError with specific field and reason. Missing required fields identified before any component initialization.

**Behavior Changes:**

System refuses to start with invalid configuration. Validation errors printed to stdout before exit. No partial initialization occurs.

**Guarantees:**

- Configuration validated in under 100ms
- Validation errors specify exact field and reason
- Unknown fields logged as warnings but not rejected
- Default values applied consistently

### Health Checks

**What is Added:**

HealthChecker in `system/health_checker.py`:
- Per-component health registration
- Synchronous health check execution
- Health status levels: HEALTHY, DEGRADED, FAILED
- Required vs optional component distinction
- Health check timeout enforcement (5 seconds default)
- Detailed health reports with diagnostic information

ComponentHealth class tracks:
- Component name
- Required flag
- Current status
- Status message
- Last check timestamp
- Check duration
- Detailed diagnostics
- Error information if applicable

**What is Hardened:**

JarvisCore tracks component initialization success/failure in `_components_initialized` and `_components_failed` lists. Non-critical component failures (voice_pipeline, data_collector) logged but do not prevent boot. Critical component failures (logger, runtime, output_adapters) halt initialization immediately.

**Observability:**

`system_status` skill enhanced to report:
- Component health status
- Uptime
- Memory usage
- Event queue depth
- Scheduler task count
- Failed components with reasons

**Guarantees:**

- Health checks complete within timeout or marked FAILED
- System continues with DEGRADED status if optional components fail
- Required component failure prevents system start
- Health check results cached for 30 seconds

### Observability and Tracing

**What is Added:**

Debug modedetailed NLU trace output
- Displays confidence scores for all intents
- Shows alternative intents considered
- Logs complete decision reasoning

Note: v0.0.3.1 Decision model already provides reasoning structure. v0.0.4 adds trace-level visibility into hypothesis generation process.

NLU trace output format (extends v0.0.3.1 Decision trace):
```
[NLU TRACE] for: 'open spotify'
  [1] normalize: 'open spotify' → 'abrir spotify'
  [2] hypothesis_gen: Generated 3 hypotheses
  [3] entities: Detected app_name=spotify
  [4] scoring: open_app=0.92, search_file=0.42, get_info=0.31
  [5] selection: open_app (highest score, above threshold)
  [RESULT] Decision created with reasoning
```

**What Changes:**

EventHandlers.handle_nlu_trace enhanced to display Decision.decision_trace when debug enabled. JarvisLogger records full Decision objects with hypothesis details.

**Guarantees:**

- Trace overhead negligible when debug disabled
- All trace steps recorded regardless of success/failure
- Confidence scores computed deterministically (from v0.0.3.1)
- Debug output does not interfere with skill execution
- Trace correlates with Decision.reasoning fieldre
- Confidence scores computed deterministically
- Debug output does not interfere with skill execution

### CLI Improvements

**What is Added:**

Enhanced AdvancedCLI methods:
- print_error_detailed: Shows error with cause, context, suggestion
- print_trace: Formats Decision.decision_trace steps (from v0.0.3.1)
- print_confidence: Displays confidence bar graph
- print_alternatives: Lists IntentHypothesis alternatives (from v0.0.3.1)
- print_health_report: Formats component health status

Special commands expanded (builds on v0.0.3.1 "why"):
- `!correct`: Mark last decision as correct
- `!wrong`: Mark last decision as incorrect
- `!correct [intent]`: Provide correct intent
- `!feedback [notes]`: Add feedback notes

**What Changes:**

Error messages use multi-line formatted output with sections. Confidence scores displayed as percentage with visual bar. Alternative intents shown after low-confidence decisions.

Note: v0.0.3.1 "why" command provides reasoning. v0.0.4 feedback commands enable learning from corrections.

**Behavior Changes:**

Unknown intents now list available skills instead of executing incorrect skill. Low confidence intents (< 0.5) prompt user for confirmation before execution.

**Guarantees:**

- Error messages always show suggested action
- Confidence displayed for every intent recognition (from v0.0.3.1 Decision)
- Users can provide feedback without restarting
- CLI remains responsive during skill execution
- Feedback commands reference Decision objects

### NLU Trace Visibility

**What is Added:**
Hypothesis generation process (v0.0.3.1 IntentHypothesis creation)
- Entity extraction results
- Scoring calculation for each hypothesis
- Selection reasoning (from Decision.reasoning)
- Alternative intents with scores (from Decision.intent_candidates)

EventBus emits EVENT_NLU_TRACE with full trace data including Decision object. EventHandlers.handle_nlu_trace formats and displays trace information.

**What Changes:**

NLUPipeline._trace method records every processing step into Decision.decision_trace. IntentParser logs all patterns checked and match scores for each IntentHypothesis. EntityExtractor reports all detected entities.

Note: v0.0.3.1 provides Decision and IntentHypothesis structure. v0.0.4 adds trace-level instrumentation for debugging.

**Guarantees:**

- Trace available regardless of intent recognition success
- Performance impact under 10% when debug enabled
- Trace format stable and parseable
- No sensitive data exposed in traces
- Trace aligns with Decision.reasoning explanationt recognition success
- Performance impact under 10% when debug enabled
- Trace format stable and parseable
- No sensitive data exposed in traces
Decision object (from v0.0.3.1) with full context
- Stores IntentHypothesis alternatives
- Tracks skill execution outcome
- Associates user feedback with Decision.decision_id
- Identifies patterns in corrections

Logged information per decision (extends v0.0.3.1 Decision model):
- Decision object (contains all v0.0.3.1 fields)
- Skill execution success/failure
- Execution duration
- User feedback (if provided via !correct/!wrong)
- Correction metadata

**What is Hardened:**

SkillDispatcher tracks execution statistics per intent:
- Total executions
- Success count
- Failure count
- Average execution time
- Last error message
- Timeout count

**Guarantees:**

- All Decision objects logged before skill execution
- Feedback associated with correct Decision.decision_id
- Statistics persisted across restarts
- No performance impact on execution
- Decision.reasoning preserved in logs
**Guarantees:**

- All decisions logged before skill execution
- Feedback associated with correct decision record
- Statistics persisted across restarts
- No performance impact on execution

## 10. What v0.0.4 Still Does NOT Do

### Features Intentionally Postponed

- Spell correction in NLU normalization
- Ambiguity resolution through user dialog
- Multi-step planning or task decomposition
- Supervised autonomous execution
- Concurrent multi-task handling
- Permission system for dangerous operations
- Audit trail for compliance
- Role-based access control
- User profiling and preference learning
- Automatic consolidation of short-term to long-term memory
- Proactive recommendations without request
- Background optimization tasks
- Self-modification of configuration
- Dynamic skill loading without restart
- A/B testing of NLU algorithms
- Machine learning model training

### Explicit Technical Limitations

- No async/await in skill execution (uses thread pools)
- No transaction support in skill dispatcher
- No rollback mechanism for failed skills
- No inter-skill communication protocol
- No skill dependency resolution
- No versioning of skills or core components
- No migration system for database schema changes
- No backup/restore functionality
- No clustering or distributed operation
- No authentication or encryption
- No rate limiting or resource quotas
- No plugin sandboxing or isolation

### Scope Boundariesv0.0.3.1 functionality. It does not add new skills, integrate external services, or change the fundamental interaction model. The Decision model from v0.0.3.1 remains the core cognitive structure. v0.0.4 adds error handling, validation, and health monitoring around that structure.



v0.0.4 improves reliability of existing functionality. It does not add new skills, integrate external services, or change the fundamental interaction model. Users still provide explicit commands and receive immediate responses. No autonomous behavior is introduced.

## 11. User-Visible Improvements

### Error Understanding

Users now see why errors occurred instead of stack traces. Every error includes:
- What happened in plain language
- Why it happened
- What state caused the problem
- What action to take next

Example before v0.0.4:
```
Traceback (most recent call last):
  File "dispatcher.py", line 45, in dispatch
    skill = self.skills[intent]
KeyError: 'open_app'
```

Example in v0.0.4:
```
[ERROR] Cannot execute command
Cause: No skill registered for intent 'open_app'
Available skills: get_time, system_status, create_note, search_file
Try: Use 'ayuda' to see all available commands
``` (extends v0.0.3.1 "why" command with trace details):
- Text normalization steps
- Hypothesis generation process (IntentHypothesis objects)
- Entities detected
- Patterns matched per hypothesis
- Score calculation for each hypothesis
- Selection reasoning (Decision.reasoning)
- Alternative interpretations (Decision.intent_candidates)

This allows users to understand and correct misinterpretations without developer assistance.

Note: v0.0.3.1 provides reasoning via "why" command. v0 (from v0.0.3.1 Decision.confidence). Low confidence triggers confirmation prompt. Users can reject incorrect interpretations before execution.

Example (uses v0.0.3.1 Decision and IntentHypothesis data):
```
>> search file project
[DECISION] Interpreted as: search_file (confidence: 73%)
Reasoning: Selected search_file because pattern "buscar {filename}" matched with entity filename=project
### Confidence Awareness

Every intent recognition displays confidence percentage. Low confidence triggers confirmation prompt. Users can reject incorrect interpretations before execution.

Example:
```
>> search file project
[NLU] Interpreted as: search_file (confidence: 73%)
Alternatives: open_file (42%), create_file (31%)
Continue? (y/n)
```

### System Health Visibility

`status` command now reports:
- Component health status (HEALTHY/DEGRADED/FAILED) (extends v0.0.3.1 "why" command):
- `!wrong` marks last Decision as incorrect
- `!correct [intent]` provides correct interpretation (references Decision.decision_id)
- `!feedback [notes]` adds context for learning (stored with Decision object)

System remembers corrections via Decision.decision_id association. Reflection system identifies patterns in user corrections by analyzing Decision.intent_candidates vs. user-provided

### Feedback Loop

Users can correct mistakes through feedback commands:
- `!wrong` marks last decision as incorrect
- `!correct [intent]` provides correct interpretation
- `!feedback [notes]` adds context for learning

System remembers corrections and adjusts confidence for similar inputs. Reflection system identifies patterns in user corrections.

### Startup Reliability

Invalid configuration detected before any components initialize. Clear error messages explain exactly what is wrong with configuration and how to fix it.

Example:
```
[CONFIG ERROR] Invalid configuration
Field: workers
Problem: Value 100 exceeds maximum 16
Fix: Set workers between 1 and 16 in config.json
```
.1 test scripts still pass without modification
- v0.0.3.1 Decision model and "why" command remain functional
- New validation test suite passes (test_v004_*.py scripts)
- System boots with invalid configuration and prints actionable error
- Every error includes cause, context, and suggestion
- `--debug` flag shows Decision.decision_trace for every input
- Confidence scores computed for all intent recognitions (from v0.0.3.1 Decision)
- Low confidence prompts user confirmation before execution
- Component health checks execute successfully
- Failed optional components logged but do not prevent boot
- Failed required components prevent boot with clear message
- Users can provide feedback with `!correct` and `!wrong` commands (references Decision.decision_id)
- Reflection observer records all Decision objectand prints actionable error
- Every error includes cause, context, and suggestion
- `--debug` flag shows NLU trace for every input
- Confidence scores computed for all intent recognitions
- Low confidence prompts user confirmation before execution
- Component health checks execute successfully
- Failed optional components logged but do not prevent boot
- Failed required components prevent boot with clear message
- Users can provide feedback with `!correct` and `!wrong` commands
- Reflection observer records all decisions with full context
- SkillDispatcher tracks execution statistics per intent

### Quality Requirements

- Boot time under 7 seconds (vs 5 seconds in v0.0.3, allows for validation overhead)
- Configuration validation completes in under 100ms
- Health checks complete in under 5 seconds total
- NLU trace overhead under 10% when debug enabled
- No memory leaks during 24-hour operation with health checks enabled
- Error handling adds under 5% CPU overhead
- All exceptions logged with stack trace preserved for debugging

### Documentation Requirements

- `docs/architecture.md` updated with v0.0.4 changes
- Error handling patterns documented with examples
- Configuration schema fully documented
- Health check implementation guide written
- NLU trace format specified
- Feedback system usage explained
- Migration notes from v0.0.3 provided

### Testing Requirements

- Unit tests for ConfigValidator covering all validation rules
- Unit tests for ErrorPresenter covering all error types
- Integration tests for health check system
- Integration tests for NLU tracing
- Integration tests for feedback commands
- Stability test running 1000 commands without failure
- Component failure simulation tests verify graceful degradation

### Operational Requirements.1 reliable, observable, and maintainable. The Decision model and reasoning capabilities from v0.0.3.1 remain unchanged. v0.0.4 adds error handling, health monitoring, and feedback collection around the existing cognitive architecture.

No new user-facing capabilities are added beyond error reporting, debugging tools, and feedback commands. The system behaves identically to v0.0.3.1

- System recovers gracefully from voice pipeline failure
- System continues operating when optional components fail
- Configuration validation errors exit with status code 1
- Logs contain sufficient information for remote debugging
- No sensitive information exposed in traces or errors
- All user-facing messages use consistent terminology
- Help text updated to include new commands and flags

v0.0.4 focuses entirely on making v0.0.3 reliable, observable, and maintainable. No new user-facing capabilities are added beyond error reporting and debugging tools. The system behaves identically to v0.0.3 when all components function correctly.
