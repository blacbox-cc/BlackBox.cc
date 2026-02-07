# system/core/special_commands_why.py
"""
V0.0.3.1: "why" command implementation
Displays reasoning for last decision
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from system.core.engine import JarvisCore


def handle_why_command(core: 'JarvisCore'):
    """
    Display reasoning for last executed decision.
    Shows selected intent, confidence, alternatives, and rejection reasoning.
    """
    last_decision = core.state.get_last_decision()
    
    if not last_decision:
        core.cli.print_warning("No decisions made yet in this session")
        return
    
    # Header
    core.cli.print_section("DECISION ANALYSIS")
    print(f"Last command: \"{last_decision.raw_input}\"")
    print()
    
    # Selected intent
    core.cli.print_info(f"Selected: {last_decision.selected_intent} (confidence: {last_decision.confidence:.0%})")
    
    # Reasoning
    if last_decision.reasoning:
        print(f"Reason: {last_decision.reasoning}")
    print()
    
    # Alternatives
    if last_decision.intent_candidates:
        alternatives = last_decision.get_top_alternatives(3)
        if alternatives:
            core.cli.print_section("Alternatives considered:")
            for alt in alternatives:
                conf_percent = f"{alt.score:.0%}"
                explanation = alt.explanation or "pattern match"
                print(f"  {alt.intent_name} ({conf_percent}) - {explanation}")
            print()
    
    # Rejected intents
    if last_decision.rejected_intents:
        rejected_str = ", ".join(last_decision.rejected_intents[:5])
        if len(last_decision.rejected_intents) > 5:
            rejected_str += f", +{len(last_decision.rejected_intents) - 5} more"
        print(f"Rejected: {rejected_str}")
        print()
    
    # Entities
    if last_decision.entities:
        entity_str = ", ".join(f"{k}={v}" for k, v in last_decision.entities.items())
        print(f"Entities: {entity_str}")
        print()
    
    # Execution status
    if last_decision.execution_allowed:
        core.cli.print_success("Execution was allowed")
    else:
        core.cli.print_warning("Execution was blocked (low confidence or error)")
    
    print()
