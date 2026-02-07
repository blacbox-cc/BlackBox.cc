# system/core/handlers.py
"""
Event Handlers for JarvisAI Core
Handles various system events and user interactions with enhanced error handling and confidence tracking
"""

import time
import traceback
from typing import TYPE_CHECKING, Dict, Any, Optional
if TYPE_CHECKING:
    from .core import JarvisCore

# Import new v0.0.4 exception system
from system.exceptions import (
    JarvisException, IntentNotRecognizedError, SkillExecutionError,
    SkillTimeoutError, PreCheckError, DegradedError
)
from system.core.special_commands import SpecialCommandsHandler
from system.core.error_presenter import ErrorPresenter


class EventHandlers:
    """
    Collection of event handlers for JarvisAI core events
    """

    def __init__(self, core: 'JarvisCore'):
        self.core = core
        self.special_commands = SpecialCommandsHandler(core)

    def _handle_error_gracefully(self, error_type: str, error: Exception, 
                                 intent: str = "", entities: Dict = None, 
                                 fallback_response: str = None) -> str:
        """
        Handle errors gracefully with detailed cause information and suggestions
        Returns response text and logs error appropriately
        """
        context = {
            "error_type": error_type,
            "intent": intent,
            "entities": entities or {},
        }
        
        # Use ErrorPresenter for better formatting
        error_info = ErrorPresenter.format_error(error, context)
        user_message = error_info['user_message']
        
        # Log with diagnostic information
        diagnostic = ErrorPresenter.get_diagnostic_info(error)
        self.core.logger.log_error(error_type, diagnostic, context)
        
        # Return user message (which includes reason + context + suggestion)
        return fallback_response or user_message

    def handle_input_voice(self, event):
        """Handler for voice input (STT offline)"""
        try:
            text = event.get("data", {}).get("text", "")
            if text:
                self.core.logger.logger.info(f"[VOICE] {text}")
                # Reuse NLU pipeline as if it were text
                self.core.nlu.process(text, self.core.events)
        except SkillExecutionError as e:
            self.core.logger.logger.error(f"[VOICE] {e.user_message()}")
        except JarvisException as e:
            self.core.logger.logger.error(f"[VOICE ERROR] {e.user_message()}")
        except Exception as e:
            response = self._handle_error_gracefully("VOICE_INPUT_ERROR", e, fallback_response="Error al procesar audio")
            self.core.logger.logger.error(response)

    def handle_nlu_trace(self, event):
        """Handler for NLU trace events (when --debug on)"""
        if not hasattr(self.core, 'runtime_manager') or not self.core.runtime_manager.debug_mode:
            return
        
        try:
            data = event.get("data", {})
            trace_steps = data.get("trace", [])
            input_text = data.get("raw", "")
            intent = data.get("intent", "unknown")
            confidence = data.get("confidence", 0.0)
            
            if not trace_steps:
                return
            
            # Print NLU trace
            self.core.cli.print_thought(f"NLU TRACE for: '{input_text}'")
            
            for i, step in enumerate(trace_steps, 1):
                step_name = step.get("step", "?")
                details = step.get("details", "")
                print(f"   [{i}] {step_name}: {details}")
            
            print(f"   [RESULT] intent='{intent}' confidence={confidence:.2%}")
            
        except Exception as e:
            self.core.logger.logger.debug(f"NLU trace handler error: {e}")
    
    def handle_input_text(self, event):
        """Handler for text input with pattern detection"""
        try:
            text = event.get("data", {}).get("text", "")
            if text:
                self.core.command_history.append(text)
                
                # Check for special commands first (including "why")
                if self.special_commands.is_special_command(text):
                    response = self.special_commands.handle_command(text)
                    self.core.events.emit("jarvis_response", {
                        "text": response,
                        "intent": "system_command",
                        "entities": {},
                        "confidence": 1.0
                    })
                    self.core.logger.logger.info(f"[COMMAND] {text} → {response}")
                    return

                # Keep only last 100 commands
                if len(self.core.command_history) > 100:
                    self.core.command_history = self.core.command_history[-100:]

                # Detect patterns every 10 commands
                if len(self.core.command_history) % 10 == 0:
                    patterns = self.core.data_collector.detect_pattern(self.core.command_history)
                    if patterns:
                        self.core.logger.logger.info(f"Patterns detected: {patterns}")
        except Exception as e:
            self.core.logger.log_error("TEXT_INPUT_HANDLER_ERROR", str(e), {"event": event})

    def handle_skill_intent(self, event):
        """
        Handler for intents processed by NLU (v0.0.3.1 Decision-aware).
        Now handles Decision objects with full reasoning context.
        """
        start_time = time.time()
        intent = None
        entities = {}
        raw_text = ""
        confidence = 0.0
        decision_id = None

        try:
            payload = event.get("data", {})

            intent = payload.get("intent", "unknown")
            entities = payload.get("entities", {})
            raw_text = payload.get("raw", "")
            confidence = payload.get("confidence", 0.0)
            alternatives = payload.get("alternatives", [])
            trace = payload.get("trace")
            # V0.0.3.1: Get decision_id if available
            decision_id = payload.get("decision_id")

            # Log NLU result with confidence
            self.core.logger.logger.debug(
                f"NLU Result: intent='{intent}' confidence={confidence:.2f} | entities: {list(entities.keys())}"
            )

            # If confidence is low, warn user about alternatives
            if confidence < 0.6 and alternatives:
                alt_str = ", ".join([f"{alt[0]}({alt[1]:.2f})" for alt in alternatives[:2]])
                self.core.logger.logger.warning(
                    f"Low confidence intent '{intent}'. Alternatives: {alt_str}"
                )

            # Handle unknown intents specially - don't dispatch to skills
            if intent == "unknown":
                try:
                    raise IntentNotRecognizedError(
                        raw_text,
                        suggestions=alternatives,
                        confidence=confidence
                    )
                except IntentNotRecognizedError as e:
                    response_text = self._handle_error_gracefully("UNKNOWN_INTENT", e, intent, entities)
                    self.core.events.emit("jarvis_response", {
                        "text": response_text,
                        "intent": intent,
                        "entities": entities,
                        "confidence": confidence,
                        "alternatives": alternatives
                    })
                    self.core.logger.log_command(raw_text, intent, entities, False)
                    self.core.logger.log_skill_execution(
                        intent, 
                        {"success": False, "error": "unknown_intent", "confidence": confidence}, 
                        time.time() - start_time
                    )
                    return

            # V0.0.3.1: Store decision in history
            # Reconstruct Decision from payload if needed
            last_decision = self.core.state.get_last_decision()
            if last_decision and last_decision.decision_id == decision_id:
                # Store this decision
                pass  # Already stored
            elif decision_id:
                # Decision exists but not stored yet - this should not happen
                self.core.logger.logger.debug(f"Decision {decision_id} not found in state")

            # Check operational mode permissions
            current_mode = self.core.session_manager.get_session_mode(self.core.current_session_id)
            if not self.core.mode_controller.can_execute_action(current_mode, intent):
                try:
                    raise PreCheckError(
                        f"Intent '{intent}' not allowed in mode '{current_mode}'",
                        "mode_restriction",
                        context={"mode": current_mode, "intent": intent}
                    )
                except PreCheckError as e:
                    response_text = self._handle_error_gracefully("MODE_RESTRICTION", e, intent, entities)
                    self.core.events.emit("jarvis_response", {
                        "text": response_text,
                        "intent": intent,
                        "entities": entities,
                        "confidence": confidence
                    })
                    return

            # Dispatch to skill with confidence info and timeout handling
            try:
                # NEW v0.0.4: Start recording reflection (if available)
                reflection = None
                if hasattr(self.core, 'reflection_observer'):
                    reflection = self.core.reflection_observer.start_recording(
                        intent, intent, raw_text, confidence, alternatives
                    )
                
                # Use parallel execution if confidence is low
                if confidence < 0.7 and alternatives:
                    self.core.logger.logger.debug(
                        f"Low confidence ({confidence:.2f}), attempting parallel alternatives"
                    )
                    result = self.core.parallel_executor.attempt_alternatives(
                        intent, alternatives, entities, self.core
                    )
                else:
                    result = self.core.skill_dispatcher.dispatch(intent, entities, self.core)
                
                # Record execution result
                duration = time.time() - start_time
                self.core.reflection_observer.record_execution(
                    success=result.get("success", True) if isinstance(result, dict) else True,
                    result=result,
                    error=None,
                    duration_ms=int(duration * 1000)
                )
            except SkillTimeoutError as e:
                # Record timeout
                self.core.reflection_observer.record_execution(
                    success=False,
                    result=None,
                    error=f"timeout: {str(e)}",
                    duration_ms=int((time.time() - start_time) * 1000)
                )
                
                response_text = self._handle_error_gracefully("SKILL_TIMEOUT", e, intent, entities)
                self.core.events.emit("jarvis_response", {
                    "text": response_text,
                    "intent": intent,
                    "entities": entities,
                    "confidence": confidence
                })
                self.core.logger.log_skill_execution(
                    intent,
                    {"success": False, "error": "timeout", "confidence": confidence},
                    time.time() - start_time
                )
                return
            except SkillExecutionError as e:
                # Record error
                self.core.reflection_observer.record_execution(
                    success=False,
                    result=None,
                    error=str(e),
                    duration_ms=int((time.time() - start_time) * 1000)
                )
                
                response_text = self._handle_error_gracefully("SKILL_EXECUTION", e, intent, entities)
                self.core.events.emit("jarvis_response", {
                    "text": response_text,
                    "intent": intent,
                    "entities": entities,
                    "confidence": confidence
                })
                self.core.logger.log_skill_execution(
                    intent,
                    {"success": False, "error": str(e), "confidence": confidence},
                    time.time() - start_time
                )
                return
            except Exception as e:
                # Record unexpected error
                self.core.reflection_observer.record_execution(
                    success=False,
                    result=None,
                    error=str(e),
                    duration_ms=int((time.time() - start_time) * 1000)
                )
                
                response_text = self._handle_error_gracefully("UNEXPECTED_ERROR", e, intent, entities)
                self.core.events.emit("jarvis_response", {
                    "text": response_text,
                    "intent": intent,
                    "entities": entities,
                    "confidence": confidence
                })
                return
            
            response_text = self._format_response(intent, result, confidence)
            
            # NUEVO: Extract actual success from outcome
            if isinstance(result, dict):
                outcome = result.get("result", {})
                if "attempted" in outcome:
                    # New outcome format
                    actual_success = outcome.get("success", False)
                    error_detail = outcome.get("error")
                else:
                    # Legacy format
                    actual_success = result.get("success", True)
                    error_detail = result.get("error")
            else:
                actual_success = True
                error_detail = None
            
            # Log the decision made: WHY did we execute this skill?
            decision_log = {
                "timestamp": time.time(),
                "input_text": raw_text,
                "recognized_intent": intent,
                "confidence": confidence,
                "alternatives": alternatives,
                "mode": self.core.session_manager.get_session_mode(self.core.current_session_id),
                "reason": f"NLU confidence {confidence:.2f} met threshold ({self.core.nlu.confidence_threshold})"
            }
            self.core.logger.logger.debug(f"[DECISION] {decision_log}")
            
            # Post-skill reflection: Analyze what happened after execution
            reflection_data = {
                "intent": intent,
                "success": actual_success,
                "entities_used": entities,
                "result_preview": str(result)[:100] if result else "No result",
                "duration_ms": int((time.time() - start_time) * 1000),
                "error_detail": error_detail if error_detail else None
            }
            if hasattr(self.core, 'reflection_engine'):
                try:
                    reflection = self.core.reflection_engine.reflect(reflection_data)
                    self.core.logger.logger.debug(f"[POST-SKILL REFLECTION] {reflection}")
                except Exception as e:
                    self.core.logger.logger.debug(f"[REFLECTION ERROR] {str(e)}")
            
            # Emit response with full metadata
            self.core.events.emit("jarvis_response", {
                "text": response_text,
                "intent": intent,
                "entities": entities,
                "confidence": confidence,
                "alternatives": alternatives,
                "trace": trace if self.core.runtime_manager.debug_mode else None,
                "decision_log": decision_log
            })

            # Save to short-term memory
            self.core.short_term_memory.append({
                "intent": intent,
                "entities": entities,
                "raw": raw_text,
                "response": response_text,
                "confidence": confidence,
                "success": actual_success
            })
            if len(self.core.short_term_memory) > self.core.short_term_memory_max:
                self.core.short_term_memory = self.core.short_term_memory[-self.core.short_term_memory_max:]

            self.core.events.emit("memory_short_term_updated", {
                "size": len(self.core.short_term_memory),
                "last": self.core.short_term_memory[-1] if self.core.short_term_memory else None
            })

            # Calculate execution metrics
            duration = time.time() - start_time

            # Logs and metrics
            self.core.logger.log_command(raw_text, intent, entities, actual_success)
            self.core.logger.log_skill_execution(
                intent, 
                {**result, "confidence": confidence} if isinstance(result, dict) else result,
                duration
            )

            # Track app usage if open_app
            if intent == "open_app" and actual_success:
                app_name = None
                if isinstance(result, dict):
                    payload_result = result.get("result")
                    if isinstance(payload_result, dict):
                        app_name = payload_result.get("app")
                if not app_name and isinstance(entities.get("app"), list) and len(entities.get("app")) > 0:
                    app_name = entities.get("app")[0]
                if app_name:
                    self.core.data_collector.track_app_usage(app_name)

            # Log result with honest success status
            status_emoji = "✓" if actual_success else "✗"
            log_msg = f"{status_emoji} {intent} ({confidence:.2f} conf) executed in {duration:.3f}s"
            if not actual_success and error_detail:
                log_msg += f" - {error_detail}"
            self.core.logger.logger.info(log_msg)

        except JarvisException as e:
            # Handle framework exceptions with user messages
            response_text = self._handle_error_gracefully(
                "JARVIS_EXCEPTION",
                e,
                intent,
                entities,
                fallback_response=e.user_message()
            )
            self.core.events.emit("jarvis_response", {
                "text": response_text,
                "intent": intent,
                "entities": entities,
                "confidence": confidence
            })
        except Exception as e:
            response_text = self._handle_error_gracefully(
                "SKILL_EXECUTION_ERROR",
                e,
                intent,
                entities
            )
            
            if self.core.config.get("debug_errors", True):
                self.core.logger.logger.error(f"Error in skill execution:\n{traceback.format_exc()}")
            
            self.core.events.emit("jarvis_response", {
                "text": response_text,
                "intent": intent,
                "entities": entities,
                "confidence": confidence
            })

    def _print_response_with_confidence(self, text: str, intent: str, confidence: float = 1.0, alternatives: list = None):
        """Print response with confidence and alternatives visualization"""
        # Print main response
        self.core.output.send(text)
        
        # Show confidence score (always visible, not just debug)
        if confidence < 1.0:
            conf_percent = int(confidence * 100)
            # Visual confidence bar
            bar_filled = int(conf_percent / 10)
            bar_empty = 10 - bar_filled
            bar = "█" * bar_filled + "░" * bar_empty
            
            # Confidence indicator
            if confidence >= 0.8:
                indicator = "✓ Confianza alta"
            elif confidence >= 0.6:
                indicator = "~ Confianza media"
            else:
                indicator = "⚠ Confianza baja"
            
            self.core.cli.print_thought(f"{indicator}: {conf_percent}% [{bar}]")
        
        # Show alternatives if confidence is low
        if confidence < 0.75 and alternatives:
            self.core.cli.print_thought("Otras interpretaciones posibles:")
            for alt_intent, alt_conf in alternatives[:2]:
                alt_percent = int(alt_conf * 100)
                print(f"   • {alt_intent} ({alt_percent}%)")

    def handle_response(self, event):
        """Handler for Jarvis responses with graceful degradation for TTS"""
        try:
            data = event.get("data", {}) if isinstance(event, dict) else {}
            text = data.get("text")
            if not text:
                return
            
            # Get confidence and alternatives for visualization
            confidence = data.get("confidence", 1.0)
            alternatives = data.get("alternatives", [])
            intent = data.get("intent", "")
            
            # Print response with confidence visualization
            self._print_response_with_confidence(text, intent, confidence, alternatives)
            
            # Try TTS with graceful degradation (optional feature)
            if self.core.config.get("tts", False):
                try:
                    self.core.tts.speak(text)
                except DegradedError as e:
                    self.core.logger.logger.warning(f"TTS degraded: {e.fallback_name}")
                except Exception as tts_error:
                    self.core.logger.logger.debug(f"TTS unavailable: {tts_error}")
                    # Don't fail response if TTS fails - it's optional
        except JarvisException as e:
            self.core.logger.logger.error(f"Response handler error: {e.user_message()}")
        except Exception as e:
            self.core.logger.log_error("RESPONSE_HANDLER_ERROR", str(e), {"event": event})

    def _format_response(self, intent: str, dispatch_result: dict, confidence: float = 1.0) -> str:
        """Format skill execution result into response text"""
        if not intent:
            return "No recibí ninguna intención."

        if intent == "unknown":
            available = self.core.skill_dispatcher.list_skills()
            return "No entendí el comando. Probá con: " + ", ".join(available[:5])

        if not dispatch_result.get("success", True):
            err = dispatch_result.get("error") or "error"
            return f"No pude ejecutar '{intent}': {err}"

        payload = dispatch_result.get("result")
        if isinstance(payload, dict) and payload.get("success") is False:
            err = payload.get("error") or "error"
            return f"No pude ejecutar '{intent}': {err}"

        # Format specific intent responses
        if intent == "open_app" and isinstance(payload, dict):
            return f"Abriendo {payload.get('app', 'la aplicación')}."
        elif intent == "get_time" and isinstance(payload, dict):
            return f"Son las {payload.get('time')} del {payload.get('date')}."
        elif intent == "system_status" and isinstance(payload, dict):
            cpu = (payload.get("cpu") or {}).get("percent")
            mem = (payload.get("memory") or {}).get("percent")
            if cpu is not None and mem is not None:
                return f"Estado del sistema: CPU {cpu}% | RAM {mem}%."
            return "Estado del sistema obtenido."
        elif intent == "create_note" and isinstance(payload, dict):
            return f"Nota creada: {payload.get('filename', 'ok')}."
        elif intent == "search_file" and isinstance(payload, dict):
            return f"Búsqueda completada. Encontré {payload.get('count', 0)} resultados."

        return f"Listo: {intent}."
