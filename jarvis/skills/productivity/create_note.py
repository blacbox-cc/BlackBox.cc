# actions/skills/create_note.py
import os
from datetime import datetime


class CreateNoteSkill:
    """Crea notas de texto"""
    
    patterns = [
        r"\b(crea|crear|create|escrib[ie]|anot[ae]|nota)\b",
        r"\b(nueva nota|new note)\b"
    ]
    
    entity_hints = {
        "note_content": {"pattern": r"nota\s+(.+)"}
    }
    
    def __init__(self):
        # Crear carpeta de notas si no existe
        self.notes_dir = os.path.join(os.path.expanduser("~"), "jarvis_notes")
        os.makedirs(self.notes_dir, exist_ok=True)
    
    def run(self, entities, core):
        # Extraer contenido
        content = entities.get("note_content", "Nota sin contenido")
        if isinstance(content, list):
            content = " ".join(content)
        
        title = f"nota_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Crear archivo
        filename = f"{title}.txt"
        filepath = os.path.join(self.notes_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n")
                f.write(f"Creado: {datetime.now()}\n\n")
                f.write(content)
            
            return {
                "attempted": True,
                "success": True,
                "error": None,
                "data": {
                    "filename": filename,
                    "path": filepath,
                    "content": content
                }
            }
            
        except Exception as e:
            return {
                "attempted": True,
                "success": False,
                "error": f"No se pudo crear nota: {str(e)}",
                "data": None
            }