"""
Special Commands Handler for v0.0.3.1
Handles system commands including "why" for decision explanation
"""

import logging

logger = logging.getLogger(__name__)


class SpecialCommandsHandler:
    """Handle special system commands"""
    
    def __init__(self, jarvis_core):
        self.core = jarvis_core
        self.commands = {
            '--debug': self._handle_debug,
            '--debug on': self._handle_debug_on,
            '--debug off': self._handle_debug_off,
            '--status': self._handle_status,
            '--skills': self._handle_skills,
            '--pc': self._handle_pc_status,
            '--tasks': self._handle_tasks,
            'skills': self._handle_skills,
            'status': self._handle_status,
            'debug': self._handle_debug,
            'debug on': self._handle_debug_on,
            'debug off': self._handle_debug_off,
            'why': self._handle_why,  # V0.0.3.1
        }
    
    def is_special_command(self, text: str) -> bool:
        """Check if text is a special command"""
        normalized = text.strip().lower()
        # Check for exact match or feedback commands
        return (normalized in self.commands or 
                normalized.startswith('!correct') or 
                normalized.startswith('!wrong') or 
                normalized.startswith('!feedback'))
    
    def handle_command(self, text: str) -> str:
        """Handle special command and return response"""
        normalized = text.strip().lower()
        
        # Handle feedback commands
        if normalized.startswith('!correct'):
            return self._handle_feedback_correct(text)
        elif normalized.startswith('!wrong'):
            return self._handle_feedback_wrong(text)
        elif normalized.startswith('!feedback'):
            return self._handle_feedback_notes(text)
        
        if normalized in self.commands:
            try:
                return self.commands[normalized]()
            except Exception as e:
                logger.error(f"Error handling special command '{text}': {e}")
                return f"Error procesando comando: {e}"
        
        return None
    
    def _handle_why(self):
        """V0.0.3.1: Handle 'why' command to explain last decision"""
        from system.core.special_commands_why import handle_why_command
        try:
            handle_why_command(self.core)
            return ""  # Output already printed by handle_why_command
        except Exception as e:
            return f"Error explaining decision: {e}"
    
    def _handle_debug(self):
        """Toggle debug mode"""
        new_state = self.core.toggle_debug_mode()
        state_text = "ON" if new_state else "OFF"
        return f"Debug mode: {state_text}"
    
    def _handle_debug_on(self):
        """Turn debug mode ON"""
        self.core._debug_mode = True
        if hasattr(self.core, 'nlu') and hasattr(self.core.nlu, 'debug'):
            self.core.nlu.debug = True
        return "Debug mode: ON"
    
    def _handle_debug_off(self):
        """Turn debug mode OFF"""
        self.core._debug_mode = False
        if hasattr(self.core, 'nlu') and hasattr(self.core.nlu, 'debug'):
            self.core.nlu.debug = False
        return "Debug mode: OFF"
    
    def _handle_status(self):
        """Get system status"""
        try:
            status = self.core.get_system_status()
            
            if 'error' in status:
                return f"Error: {status['error']}"
            
            sys_info = status.get('system', {})
            
            response = "🖥️ Sistema Status:\n"
            response += f"  • CPU: {sys_info.get('cpu_percent', 0):.1f}%\n"
            response += f"  • Memoria: {sys_info.get('memory_percent', 0):.1f}%\n"
            response += f"  • Disco: {sys_info.get('disk_percent', 0):.1f}%\n"
            response += f"  • Procesos: {sys_info.get('processes', 0)}"
            
            return response
        except Exception as e:
            return f"Error obteniendo status: {e}"
    
    def _handle_skills(self):
        """List all available skills"""
        try:
            skills = self.core.get_available_skills()
            
            if not skills:
                return "No skills available"
            
            response = f"📚 Skills Disponibles ({len(skills)}):\n"
            for i, skill in enumerate(skills[:15], 1):  # Show first 15
                response += f"  {i}. {skill['name']}\n"
            
            if len(skills) > 15:
                response += f"  ... y {len(skills) - 15} más"
            
            return response
        except Exception as e:
            return f"Error listando skills: {e}"
    
    def _handle_pc_status(self):
        """Get detailed PC status"""
        return self._handle_status()
    
    def _handle_tasks(self):
        """Show background tasks"""
        try:
            tasks = self.core.get_background_tasks()
            
            if not tasks:
                return "No background tasks running"
            
            response = f"📋 Background Tasks ({len(tasks)}):\n"
            for task in tasks[:10]:
                task_id = task.get('id', 'unknown')
                task_name = task.get('name', 'unknown')
                status = task.get('status', 'unknown')
                response += f"  • {task_id}: {task_name} ({status})\n"
            
            return response
        except Exception as e:
            return f"Error listando tasks: {e}"
    
    def _handle_feedback_correct(self, text: str):
        """
        Handle !correct command - confirm last decision was correct
        Usage: !correct  (marks last as correct)
               !correct search_file  (corrects to specific intent)
        """
        try:
            parts = text.strip().split()
            
            if not hasattr(self.core, 'reflection_observer'):
                return "[ERROR] Reflection system not available"
            
            reflection = self.core.reflection_observer
            
            if not reflection.current_reflection:
                return "[ERROR] No recent decision to confirm"
            
            if len(parts) == 1:
                # Just !correct - confirm current decision
                reflection.apply_feedback(
                    feedback_type="correct",
                    alternative=None
                )
                return f"[OK] Confirmed: '{reflection.current_reflection.intent}' was correct"
            else:
                # !correct <intent> - correct to different intent
                correct_intent = parts[1]
                reflection.apply_feedback(
                    feedback_type="alternative",
                    alternative=correct_intent
                )
                return f"[OK] Noted: Should have been '{correct_intent}' instead of '{reflection.current_reflection.intent}'"
        
        except Exception as e:
            return f"[ERROR] Error procesando feedback: {e}"
    
    def _handle_feedback_wrong(self, text: str):
        """
        Handle !wrong command - last decision was wrong
        Usage: !wrong  (marks last as wrong)
        """
        try:
            if not hasattr(self.core, 'reflection_observer'):
                return "[ERROR] Reflection system not available"
            
            reflection = self.core.reflection_observer
            
            if not reflection.current_reflection:
                return "[ERROR] No recent decision to correct"
            
            # Save alternatives before apply_feedback sets current_reflection to None
            alternatives = reflection.current_reflection.alternatives
            intent_name = reflection.current_reflection.intent
            
            reflection.apply_feedback(
                feedback_type="wrong",
                alternative=None
            )
            
            alt_str = ", ".join([alt[0] for alt in alternatives[:3]]) if alternatives else "ninguna"
            
            return f"[ERROR-NOTED] '{intent_name}' was wrong.\nAlternatives: {alt_str}"
        
        except Exception as e:
            return f"[ERROR] Error procesando feedback: {e}"
    
    def _handle_feedback_notes(self, text: str):
        """
        Handle !feedback command - add notes to last decision
        Usage: !feedback This was confusing because...
        """
        try:
            if not hasattr(self.core, 'reflection_observer'):
                return "[ERROR] Reflection system not available"
            
            parts = text.split(None, 1)  # Split on first space
            if len(parts) < 2:
                return "[INFO] Usage: !feedback <notes>"
            
            notes = parts[1]
            reflection = self.core.reflection_observer
            
            if not reflection.current_reflection:
                return "[ERROR] No recent decision to annotate"
            
            reflection.current_reflection.user_notes = notes
            reflection.apply_feedback(
                feedback_type="notes",
                alternative=None
            )
            
            return f"[OK] Notes saved: {notes[:50]}..."
        
        except Exception as e:
            return f"[ERROR] Error procesando notas: {e}"

