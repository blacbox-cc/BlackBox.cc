┌──────── Input Layer ────────┐
│ CLI / Voice / API           │
└────────────┬───────────────┘
             ↓
┌──────── NLU Layer ──────────┐
│ Normalization               │
│ Intent Detection            │
│ Confidence Scoring          │
│ Entity Extraction           │
│ Context Injection           │
└────────────┬───────────────┘
             ↓
┌────── Decision Layer ───────┐
│ Intent Resolution           │
│ Ambiguity Handling          │
│ Skill Selection             │
│ Plan Generation (future)    │
└────────────┬───────────────┘
             ↓
┌────── Execution Layer ──────┐
│ Skill Execution             │
│ Thread / Task Management    │
│ Permissions / Safety        │
└────────────┬───────────────┘
             ↓
┌────── Reflection Layer ─────┐
│ Result Analysis             │
│ Memory Update               │
│ Pattern Detection           │
│ Recommendations             │
└────────────────────────────┘
