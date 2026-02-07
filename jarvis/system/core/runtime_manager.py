# system/core/runtime_manager.py
"""
Runtime Manager for JarvisAI Core
Handles the main execution loop and user interaction
"""

import time
from typing import TYPE_CHECKING
from jarvis_io.voice_pipeline import VoiceIOPipeline

if TYPE_CHECKING:
    from .core import JarvisCore


class RuntimeManager:
    """
    Manages the main runtime loop and user interactions
    """

    def __init__(self, core: 'JarvisCore'):
        self.core = core
        self.debug_mode = False  # Track debug mode state
        self.nlu_trace_enabled = False  # Show detailed NLU trace

    def run(self):
        """
        Main execution loop with advanced CLI and session management
        """
        if not self.core.state.wait_ready(timeout=5.0):
            raise RuntimeError("Core not ready to run")

        self.core.state.set("RUNNING")
        self.core.logger.logger.info("[START] Main loop started")

        # Advanced CLI welcome
        self._show_welcome()

        try:
            while self.core.state.is_running():
                try:
                    # Get user input with advanced CLI
                    user_input = self.core.cli.input_prompt()

                    if user_input.lower() in ['salir', 'exit', 'quit']:
                        break

                    # Handle special commands
                    if self._handle_special_command(user_input):
                        continue

                    # Process as regular command
                    self._process_regular_command(user_input)

                    # Small delay to prevent busy loop
                    time.sleep(0.01)

                except KeyboardInterrupt:
                    self.core.cli.print_thought("Interrupción detectada")
                    break
                except Exception as e:
                    self.core.logger.log_error("CORE_LOOP_ERROR", str(e))
                    self.core.cli.print_result({"success": False, "error": f"Error en loop principal: {str(e)}"})
                    if self.core.config.get("crash_on_error", False):
                        break
        finally:
            self.core.stop()

    def _show_welcome(self):
        """Show welcome screen with system information"""
        self.core.cli.print_header("JARVIS AI v0.0.3.1 - EXPLICIT REASONING")

        self.core.cli.print_system_status({
            "estado": "LISTO",
            "sesiones_activas": len(self.core.session_manager.list_active_sessions()),
            "modo_voz": self.core.voice_pipeline.is_voice_available(),
            "skills_registradas": len(self.core.skill_dispatcher.skills)
        })

        # Show session info
        session_info = {
            "session_id": self.core.current_session_id,
            "mode": self.core.session_manager.get_session_mode(self.core.current_session_id),
            "created_at": self.core.session_manager.get_session(self.core.current_session_id).created_at.isoformat() if self.core.session_manager.get_session(self.core.current_session_id) else "N/A"
        }
        self.core.cli.print_session_info(session_info)

        # Show menu (V0.0.3.1 includes "why" command)
        menu_options = {
            "voz": "Activar/desactivar modo voz",
            "modo [SAFE|PASSIVE|ACTIVE|ANALYSIS]": "Cambiar modo operacional",
            "sesiones": "Ver sesiones activas",
            "status": "Estado del sistema",
            "why": "Explicar última decisión",  # V0.0.3.1
            "ayuda": "Mostrar esta ayuda",
            "salir": "Salir del sistema"
        }
        self.core.cli.print_menu(menu_options)
        self.core.cli.print_separator()

    def _handle_special_command(self, user_input: str) -> bool:
        """
        Handle special commands that don't go through NLU

        Returns:
            bool: True if command was handled, False if it should go to NLU
        """
        command = user_input.lower().strip()

        # Debug mode commands
        if command == '--debug':
            self.debug_mode = not self.debug_mode
            status = "ACTIVADO" if self.debug_mode else "DESACTIVADO"
            self.core.cli.print_thought(f"Debug mode {status}")
            self.core.nlu.debug = self.debug_mode
            return True

        elif command == '--debug-nlu':
            self.nlu_trace_enabled = not self.nlu_trace_enabled
            status = "ACTIVADO" if self.nlu_trace_enabled else "DESACTIVADO"
            self.core.cli.print_thought(f"NLU trace {status}")
            return True

        elif command == '--health':
            self._show_health_report()
            return True

        elif command == '--version':
            self.core.cli.print_thought(f"JarvisAI v{self.core.config.get('version', 'unknown')}")
            return True

        elif command == 'ayuda':
            self._show_help()
            return True

        elif command == 'status':
            self._show_status()
            return True

        elif command == 'sesiones':
            self._show_sessions()
            return True

        elif command.startswith('modo '):
            self._change_mode(user_input)
            return True

        elif command == 'voz':
            self._toggle_voice()
            return True

        # Auto-improvement commands
        elif command == 'analizar':
            self._run_codebase_analysis()
            return True

        elif command == 'propuestas':
            self._show_improvement_proposals()
            return True

        elif command.startswith('ver '):
            proposal_id = command.replace('ver ', '').strip()
            self._show_proposal_details(proposal_id)
            return True

        elif command.startswith('aprobar '):
            proposal_id = command.replace('aprobar ', '').strip()
            self._approve_proposal(proposal_id)
            return True

        elif command.startswith('rechazar '):
            proposal_id = command.replace('rechazar ', '').strip()
            self._reject_proposal(proposal_id)
            return True

        elif command == 'insights':
            self._show_learning_insights()
            return True

        return False

    def _show_help(self):
        """Show help menu"""
        menu_options = {
            "voz": "Activar/desactivar modo voz",
            "modo [SAFE|PASSIVE|ACTIVE|ANALYSIS]": "Cambiar modo operacional",
            "sesiones": "Ver sesiones activas",
            "status": "Estado del sistema",
            "ayuda": "Mostrar esta ayuda",
            "salir": "Salir del sistema"
        }
        self.core.cli.print_menu(menu_options)

    def _show_status(self):
        """Show system status"""
        self.core.cli.print_system_status({
            "estado": "EJECUTANDO",
            "sesiones_activas": len(self.core.session_manager.list_active_sessions()),
            "modo_voz": self.core.voice_pipeline.is_voice_available(),
            "skills_registradas": len(self.core.skill_dispatcher.skills)
        })

    def _show_sessions(self):
        """Show active sessions"""
        sessions = self.core.session_manager.list_active_sessions()
        self.core.cli.print_thought(f"Encontré {len(sessions)} sesiones activas")
        for session in sessions:
            print(f"  ID: {session['session_id']} | Modo: {session['mode']} | Creada: {session['created_at']}")

    def _change_mode(self, user_input: str):
        """Change operational mode"""
        try:
            new_mode = user_input.split(' ', 1)[1].upper()
            self.core.session_manager.set_session_mode(self.core.current_session_id, new_mode)
            self.core.cli.print_result({"success": True, "result": f"Modo cambiado a {new_mode}"})
        except ValueError as e:
            self.core.cli.print_result({"success": False, "error": str(e)})
        except IndexError:
            self.core.cli.print_result({"success": False, "error": "Uso: modo [SAFE|PASSIVE|ACTIVE|ANALYSIS]"})

    def _toggle_voice(self):
        """Toggle voice mode"""
        current_voice = self.core.config.get("voice_enabled", False)
        new_voice_state = not current_voice
        self.core.config["voice_enabled"] = new_voice_state

        if new_voice_state:
            # Reinitialize voice pipeline with voice enabled
            self.core.voice_pipeline = VoiceIOPipeline(self.core.config)
            if self.core.voice_pipeline.start():
                self.core.cli.print_result({"success": True, "result": "Modo voz activado"})
            else:
                self.core.cli.print_result({"success": False, "error": "No se pudo activar el modo voz (dependencias faltantes?)"})
        else:
            self.core.voice_pipeline.stop()
            self.core.cli.print_result({"success": True, "result": "Modo voz desactivado"})

    def _run_codebase_analysis(self):
        """Run codebase analysis and show results"""
        try:
            if 'auto_programming' not in self.core.skill_dispatcher.skills:
                self.core.cli.print_result({"success": False, "error": "Skill auto_programming no disponible"})
                return

            skill = self.core.skill_dispatcher.get_skill('auto_programming')
            result = skill.run('analyze')

            if result.get('success'):
                self.core.cli.print_code_analysis(result['analysis'])
            else:
                self.core.cli.print_result(result)

        except Exception as e:
            self.core.cli.print_result({"success": False, "error": f"Error en análisis: {str(e)}"})

    def _show_improvement_proposals(self):
        """Show all improvement proposals"""
        try:
            if 'auto_programming' not in self.core.skill_dispatcher.skills:
                self.core.cli.print_result({"success": False, "error": "Skill auto_programming no disponible"})
                return

            skill = self.core.skill_dispatcher.get_skill('auto_programming')
            result = skill.run('review_proposals')

            if result.get('success'):
                self.core.cli.print_proposals_summary(result)
            else:
                self.core.cli.print_result(result)

        except Exception as e:
            self.core.cli.print_result({"success": False, "error": f"Error mostrando propuestas: {str(e)}"})

    def _show_proposal_details(self, proposal_id: str):
        """Show detailed information about a specific proposal"""
        try:
            if 'auto_programming' not in self.core.skill_dispatcher.skills:
                self.core.cli.print_result({"success": False, "error": "Skill auto_programming no disponible"})
                return

            skill = self.core.skill_dispatcher.get_skill('auto_programming')
            result = skill.run('get_proposal', proposal_id=proposal_id)

            if result.get('success'):
                self.core.cli.print_proposal_details(result['proposal'])
            else:
                self.core.cli.print_result(result)

        except Exception as e:
            self.core.cli.print_result({"success": False, "error": f"Error obteniendo propuesta: {str(e)}"})

    def _approve_proposal(self, proposal_id: str):
        """Approve an improvement proposal"""
        try:
            if 'auto_programming' not in self.core.skill_dispatcher.skills:
                self.core.cli.print_result({"success": False, "error": "Skill auto_programming no disponible"})
                return

            skill = self.core.skill_dispatcher.get_skill('auto_programming')
            result = skill.run('approve_proposal', proposal_id=proposal_id)

            self.core.cli.print_result(result)

        except Exception as e:
            self.core.cli.print_result({"success": False, "error": f"Error aprobando propuesta: {str(e)}"})

    def _reject_proposal(self, proposal_id: str):
        """Reject an improvement proposal"""
        try:
            if 'auto_programming' not in self.core.skill_dispatcher.skills:
                self.core.cli.print_result({"success": False, "error": "Skill auto_programming no disponible"})
                return

            skill = self.core.skill_dispatcher.get_skill('auto_programming')
            result = skill.run('reject_proposal', proposal_id=proposal_id)

            self.core.cli.print_result(result)

        except Exception as e:
            self.core.cli.print_result({"success": False, "error": f"Error rechazando propuesta: {str(e)}"})

    def _show_learning_insights(self):
        """Show learning engine insights"""
        try:
            if 'learning_engine' not in self.core.skill_dispatcher.skills:
                self.core.cli.print_result({"success": False, "error": "Skill learning_engine no disponible"})
                return

            skill = self.core.skill_dispatcher.get_skill('learning_engine')
            result = skill.run('analyze_session')

            if result.get('success'):
                insights = {
                    'error_patterns': result.get('error_patterns', []),
                    'skill_usage': result.get('skill_usage', []),
                    'unknown_intents': result.get('unknown_intents', []),
                    'improvement_opportunities': result.get('improvement_opportunities', [])
                }
                self.core.cli.print_learning_insights(insights)
            else:
                self.core.cli.print_result(result)

        except Exception as e:
            self.core.cli.print_result({"success": False, "error": f"Error mostrando insights: {str(e)}"})

    def _show_health_report(self):
        """Show comprehensive health report of all components"""
        try:
            health_report = self.core.health_checker.get_health_report()
            
            # Print header
            self.core.cli.print_header("HEALTH CHECK REPORT")
            
            # Overall status
            overall = health_report["overall_status"]
            status_emoji = "✅" if overall == "HEALTHY" else "⚠️" if overall == "DEGRADED" else "❌"
            self.core.cli.print_thought(f"{status_emoji} Overall Status: {overall}")
            
            # Summary
            self.core.cli.print_action("Component Summary", {
                "total": health_report["total_components"],
                "healthy": health_report["healthy_components"],
                "degraded": health_report["degraded_components"],
                "unhealthy": health_report["unhealthy_components"]
            })
            
            # Component details
            if health_report["components"]:
                self.core.cli.print_thought("Component Details:")
                for comp in health_report["components"]:
                    status_icon = "✅" if comp["status"] == "HEALTHY" else "⚠️" if comp["status"] == "DEGRADED" else "❌"
                    print(f"  {status_icon} {comp['name']:20} | Status: {comp['status']:10} | Time: {comp['response_time_ms']}ms")
                    if comp["error_message"]:
                        print(f"     └─ Error: {comp['error_message']}")
            
            # Critical issues
            critical = self.core.health_checker.get_critical_issues()
            if critical:
                self.core.cli.print_thought("⚠️ CRITICAL ISSUES:")
                for comp_name, error_msg in critical:
                    print(f"  - {comp_name}: {error_msg}")
            
            # System readiness
            is_ready = self.core.health_checker.is_system_ready()
            readiness = "READY FOR OPERATION" if is_ready else "NOT READY"
            emoji = "🚀" if is_ready else "⛔"
            self.core.cli.print_thought(f"{emoji} System Readiness: {readiness}")
            
        except Exception as e:
            self.core.cli.print_result({"success": False, "error": f"Error getting health report: {str(e)}"})

    def _process_regular_command(self, user_input: str):
        """Process regular commands through NLU pipeline"""
        self.core.cli.print_action(f"Procesando comando: {user_input}")
        self.core.input.process_text(user_input)