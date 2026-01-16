import os
import shutil
import re
import time
import json

PROJECTS_DIR = "projects"
TRASH_DIR = ".trash"
TRASH_PROJECTS = os.path.join(TRASH_DIR, "projects")
TRASH_TASKS = os.path.join(TRASH_DIR, "tasksfiles")
TRASH_MANIFEST = os.path.join(TRASH_DIR, "manifest.json")

class ProjectAgent:
    def __init__(self):
            self.current_project = None 
            self.current_tasks_file = None
            self.pending_delete = None
            self.undo_stack = []
            self._init_trash()
            self.setup_tools()
            self.messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un agente que gestiona proyectos. "
                        "Debes usar select_project antes de trabajar en un proyecto."
                    )
                }
            ]   
            
    def _init_trash(self):
        os.makedirs(TRASH_PROJECTS, exist_ok=True)
        os.makedirs(TRASH_TASKS, exist_ok=True)
        if not os.path.exists(TRASH_MANIFEST):
            with open(TRASH_MANIFEST, "w") as f:
                json.dump([], f)
                
    def _log_trash(self, entry):
        with open(TRASH_MANIFEST, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

    def _pop_last_trash(self):
        with open(TRASH_MANIFEST, "r+", encoding="utf-8") as f:
            data = json.load(f)
            if not data:
                return None
            entry = data.pop()
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
            return entry

    def setup_tools(self):
        self.tools = [
                        {
                ############PROJECTS##############
                
                #Create project
                "type": "function",
                "name": "create_project",
                "description": (
                    "Crea un nuevo proyecto si no existe y lo selecciona automáticamente"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string",
                            "description": "Nombre del proyecto a crear"
                        }
                    },
                    "required": ["project"]
                }
            },
            {
                #Select project
                "type": "function",
                "name": "select_project",
                "description": (
                    "Selecciona el proyecto activo sobre el que trabajará el agente a partir de ahora"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string",
                            "description": "Nombre del proyecto a seleccionar"
                        }
                    },
                    "required": ["project"]
                }
            },
             {
                #Summarize Project
                "type": "function",
                "name": "summarize_project",
                "description": (
                    "Genera un resumen del archivo de tareas activo del proyecto"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
             {
                 #Rename Project
                "type": "function",
                "name": "rename_project",
                "description": (
                    "Renombra el proyecto actualmente seleccionado cambiando el nombre "
                    "de su carpeta dentro del directorio projects/"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "new_name": {
                            "type": "string",
                            "description": "Nuevo nombre para el proyecto"
                        }
                    },
                    "required": ["new_name"]
                }
            },

            {
                #Delete Project
                "type": "function",
                "name": "delete_project",
                "description": (
                    "Solicita la eliminación del proyecto actualmente seleccionado "
                    "y pide confirmación antes de borrar"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                #Confirm Delete
                "type": "function",
                "name": "confirm_delete",
                "description": (
                    "Confirma y ejecuta la eliminación del proyecto previamente marcado"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                #Cancel Delete
                "type": "function",
                "name": "cancel_delete",
                "description": (
                    "Cancela la eliminación de un proyecto que estaba pendiente de confirmación"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                #########FILES########
                
                #List files
                "type": "function",
                "name": "list_files",
                "description": (
                    "Lista los archivos del proyecto actualmente seleccionado"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                #Read Files
                "type": "function",
                "name": "read_file",
                "description": (
                    "Lee el contenido de un archivo dentro del proyecto seleccionado"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Nombre del archivo a leer (ej: tasks.md)"
                        }
                    },
                    "required": ["filename"]
                }
            },
            {
                #Edit Files
                "type": "function",
                "name": "edit_file",
                "description": (
                    "Edita o crea un archivo dentro del proyecto seleccionado, "
                    "reemplazando texto o escribiendo contenido nuevo"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Nombre del archivo (ej: tasks.md)"
                        },
                        "prev_text": {
                            "type": "string",
                            "description": "Texto a reemplazar (vacío si es archivo nuevo)",
                            "default": ""
                        },
                        "new_text": {
                            "type": "string",
                            "description": "Texto nuevo a escribir"
                        }
                    },
                    "required": ["filename", "new_text"]
                }
            },
                ###########Tasks###############
            
            {
                #Create Task File
                "type": "function",
                "name": "create_tasks_file",
                "description": (
                    "Crea un nuevo archivo de tareas dentro del proyecto seleccionado "
                    "y lo establece como el archivo de tareas activo"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Nombre del archivo de tareas (ej: backend_tasks.md)"
                        }
                    },
                    "required": ["filename"]
                }
            },
            {
                #Select Task File
                "type": "function",
                "name": "select_tasks_file",
                "description": (
                    "Selecciona un archivo de tareas existente como el archivo de tareas activo "
                    "dentro del proyecto actual"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Nombre del archivo de tareas a seleccionar"
                        }
                    },
                    "required": ["filename"]
                }
            },

            {
                
                #Create Task
                "type": "function",
                "name": "create_task",
                "description": (
                    "Agrega una nueva tarea al archivo tasks.md del proyecto seleccionado"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Descripción de la tarea"
                        }
                    },
                    "required": ["task"]
                }
            },
            {
                #Listar Tasks
                "type": "function",
                "name": "list_tasks",
                "description": (
                    "Lista las tareas del archivo tasks.md del proyecto seleccionado, "
                    "incluyendo su estado (pendiente o completada)"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                #Complete Task
                "type": "function",
                "name": "complete_task",
                "description": (
                    "Marca una tarea como completada [x] en el archivo tasks.md "
                    "del proyecto seleccionado"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Texto exacto de la tarea a completar"
                        }
                    },
                    "required": ["task"]
                }
            },
            {
                #Delete Task
                "type": "function",
                "name": "delete_task_file",
                "description": (
                    "Elimina un archivo de tareas específico dentro del proyecto seleccionado "
                    "(por ejemplo: frontend_tasks.md o tasks.md). "
                    "No afecta a otros archivos ni al proyecto completo."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Nombre exacto del archivo de tareas a eliminar"
                        }
                    },
                    "required": ["filename"]
                }
            },
            {
                #Rename Task File
                "type": "function",
                "name": "rename_task_file",
                "description": (
                    "Renombra un archivo de tareas dentro del proyecto seleccionado "
                    "(por ejemplo: tasks.md → backend_tasks.md)"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "old_name": {
                            "type": "string",
                            "description": "Nombre actual del archivo (ej: tasks.md)"
                        },
                        "new_name": {
                            "type": "string",
                            "description": "Nuevo nombre del archivo (ej: backend_tasks.md)"
                        }
                    },
                    "required": ["old_name", "new_name"]
                }
            },
            ################# UNDO ########################
            
            ##Eliminación###
            #Undo Delete
            {
                "type": "function",
                "name": "undo_delete",
                "description": (
                    "Deshace la última eliminación (proyecto o archivo) "
                    "restaurándolo desde la papelera"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
                },
                {
                #Restore From Trash
                    
                "type": "function",
                "name": "restore_from_trash",
                "description": (
                    "Restaura el último proyecto o archivo eliminado desde la papelera. "
                    "Si existe un conflicto de nombre, se restaurará con un sufijo automático."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
                },
                {
                 #Undo Last Action
                "type": "function",
                "name": "undo_last_action",
                "description": (
                    "Deshace la última eliminación realizada durante esta sesión, "
                    "restaurando el proyecto o archivo eliminado más recientemente."
                    ),
                "parameters": {
                    "type": "object",
                    "properties": {}
                    }
                }



        ]

 ########PROJECTS#########
    
    #Create Project
    def create_project(self, project):
        if not re.match(r'^[a-zA-Z0-9_-]+$', project):
            return "Nombre de proyecto inválido. Usa solo letras, números, guiones y underscores."

        path = f"{PROJECTS_DIR}/{project}"
        
        if os.path.isdir(path):
            return f"El proyecto '{project}' ya existe."
        
        os.makedirs(path)
        tasks_path = f"{path}/tasks.md"
        with open(tasks_path, "w", encoding="utf-8") as f:
            f.write("# Tareas del proyecto\n\n")
        
        self.current_project = project
        self.current_tasks_file = "tasks.md"
        
        self.undo_stack.append(
            {
            "action": "create_project",
            "payload": {
                "project": project
            }
            })


        return f"Proyecto '{project}' creado y seleccionado."
    
    #Select Project
    def select_project(self, project):
        path = f"projects/{project}"
        self.current_tasks_file = None

        if not os.path.isdir(path):
            return f"El proyecto '{project}' no existe."

        self.current_project = project
        return f"Proyecto activo: {project}"
    
    #Rename Project
    def rename_project(self, new_name):
        if not self.current_project:
            return "No hay proyecto seleccionado."
        if not re.match(r'^[a-zA-Z0-9_-]+$', new_name):
            return "Nombre de proyecto inválido."

        old_path = os.path.join(PROJECTS_DIR, self.current_project)
        new_path = os.path.join(PROJECTS_DIR, new_name)

        if not os.path.isdir(old_path):
            return f"El proyecto '{self.current_project}' no existe."

        if os.path.exists(new_path):
            return f"Ya existe un proyecto llamado '{new_name}'."
        
        old_name = self.current_project

        os.rename(old_path, new_path)
        
        self.current_project = new_name
        
        self.undo_stack.append(
        {
        "action": "rename_project",
        "payload": {
            "old_name": old_name,
            "new_name": new_name
                     }
        })


        return f"Proyecto '{old_name}' renombrado a '{new_name}'."

    #Delete Project
    def delete_project(self):
        if not self.current_project:
            return "No hay proyecto seleccionado."

        self.pending_delete = {
        "type": "project",
        "name": self.current_project
        }

        return (
            f"¿Estás seguro que deseas eliminar el proyecto "
            f"'{self.current_project}'?\n"
            f"Escribe 'confirmar' para continuar."
        )
    
    #Confirm Delete
    def confirm_delete(self):   
        if not self.pending_delete:
            return "No hay ninguna eliminación pendiente."

        if self.pending_delete["type"] == "project":
            project = self.pending_delete["name"]
            src = os.path.join(PROJECTS_DIR, project)

            timestamp = int(time.time())
            trash_name = f"{project}__{timestamp}"
            dst = os.path.join(TRASH_PROJECTS, trash_name)

            shutil.move(src, dst)

            self._log_trash({
                "type": "project",
                "original_name": project,
                "trash_name": trash_name,
                "timestamp": timestamp
                })

            self.current_project = None
            self.current_tasks_file = None

            self.pending_delete = None
            return "Proyecto movido a la papelera."
        
    #Cancel Delete
    def cancel_delete(self):
        if not self.pending_delete:
            return "No hay ninguna eliminación pendiente que cancelar."

        cancelled = self.pending_delete
        self.pending_delete = None

        return f"Eliminación del proyecto '{cancelled['name']}' cancelada."
    
    #Summarize Project
    def summarize_project(self):
        tasks_file = self._get_tasks_file()
        if not tasks_file or not os.path.exists(tasks_file):
            return "No hay archivo de tareas activo."
        
        with open(tasks_file, "r", encoding="utf-8") as f:
            content = f.read()

        total = content.count("- [")
        completed = content.count("- [x]")
        pending = total - completed

        return (
            f"Estado del proyecto '{self.current_project}':\n"
            f"- Total: {total}\n"
            f"- Completadas: {completed}\n"
            f"- Pendientes: {pending}"
        )

    #########FILES###############
    
    #list Files
    def list_files(self):
        if not self.current_project:
            return "No hay proyecto seleccionado."

        path = f"projects/{self.current_project}"
        return os.listdir(path)

    #Read Files
    def read_file(self, filename):
        if not self.current_project:
            return "No hay proyecto seleccionado."

        path = f"projects/{self.current_project}/{filename}"

        if not os.path.exists(path):
            return "El archivo no existe."

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    #Edit Files
    def edit_file(self, filename, prev_text="", new_text=""):
        if not self.current_project:
            return "No hay proyecto seleccionado."

        path = os.path.join(PROJECTS_DIR, self.current_project, filename)

        existed = os.path.exists(path)
        before_content = ""

        if existed:
            with open(path, "r", encoding="utf-8") as f:
                before_content = f.read()
            content = before_content.replace(prev_text, new_text)
        else:
            content = new_text

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        #Registrar undo
        self.undo_stack.append({
            "action": "edit_file",
            "payload": {
                "project": self.current_project,
                "filename": filename,
                "before": before_content,
                "existed": existed
            }
        })

        return f"✏️ Archivo '{filename}' actualizado."

    ################TASKS##################
    
    #Create Tasks Files
    def create_tasks_file(self, filename):
        if not self.current_project:
            return "No hay proyecto seleccionado."

        if not filename.endswith(".md"):
            return "El archivo debe tener extensión .md"

        project_path = os.path.join(PROJECTS_DIR, self.current_project)
        file_path = os.path.join(project_path, filename)

        if os.path.exists(file_path):
            return f"El archivo '{filename}' ya existe."

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Tareas\n\n")

        self.current_tasks_file = filename
        
        self.undo_stack.append({
            "action": "create_tasks_file",
            "payload": {
                "project": self.current_project,
                "filename": filename
            }
        })

        return f"📄 Archivo de tareas '{filename}' creado y activado."
    
    #Select Tasks File
    def select_tasks_file(self, filename):
        if not self.current_project:
            return "No hay proyecto seleccionado."

        project_path = os.path.join(PROJECTS_DIR, self.current_project)
        file_path = os.path.join(project_path, filename)

        if not os.path.isfile(file_path):
            return f"El archivo '{filename}' no existe."

        self.current_tasks_file = filename
       

        return f"Archivo de tareas activo: {filename}"

    #Create Task
    def create_task(self, task):
        tasks_file = self._get_tasks_file()

        with open(tasks_file, "a", encoding="utf-8") as f:
            f.write(f"- [ ] {task}\n")
        self.undo_stack.append({
        "action": "create_task",
        "payload": {
            "project": self.current_project,
            "tasks_file": self.current_tasks_file,
            "task": task
        }
    })


        return f"Tarea creada: {task}"
    
    #Get Tasks Files
    def _get_tasks_file(self):
        if not self.current_project:
            return None

        if not self.current_tasks_file:
            return None

        return os.path.join(
            PROJECTS_DIR,
            self.current_project,
            self.current_tasks_file
        )

    #List Tasks
    def list_tasks(self):
        if not self.current_project or not self.current_tasks_file:
            return "No hay archivo de tareas activo."

        tasks_file = self._get_tasks_file()

        if not os.path.exists(tasks_file):
            return "No hay archivo de tareas."

        tasks = []

        with open(tasks_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("- [ ]"):
                    tasks.append({"task": line[6:], "status": "pending"})
                elif line.startswith("- [x]"):
                    tasks.append({"task": line[6:], "status": "completed"})

        if not tasks:
            return "No hay tareas."

        lines = []
        for i, t in enumerate(tasks, 1):
            status = "[x]" if t["status"] == "completed" else "[]"
            lines.append(f"{i}. {status} {t['task']}")

        return "\n".join(lines)
    
    #Complete Task
    def complete_task(self, task):
        tasks_file = self._get_tasks_file()
        

        with open(tasks_file, "r", encoding="utf-8") as f:
            content = f.read()

        if f"- [ ] {task}" not in content:
            return "La tarea no existe o ya está completada."

        updated = content.replace(f"- [ ] {task}", f"- [x] {task}")

        with open(tasks_file, "w", encoding="utf-8") as f:
            f.write(updated)
        self.undo_stack.append({
            "action": "complete_task",
            "payload": {
                "project": self.current_project,
                "tasks_file": self.current_tasks_file,
                "task": task
            }
        })

        return f"Tarea completada: {task}"
    
    #Delete Task File
    def delete_task_file(self, filename):
        
        if not self.current_project:
            return "No hay proyecto seleccionado."

        project_path = os.path.join(PROJECTS_DIR, self.current_project)
        src = os.path.join(project_path, filename)
        
        if not os.path.isfile(src):
            return f"El archivo '{filename}' no existe."

        timestamp = int(time.time())
        dst_name = f"{filename}__{timestamp}"
        dst = os.path.join(TRASH_TASKS, dst_name)

        shutil.move(src, dst)

        self._log_trash({
            "type": "task_file",
            "original_name": filename,
            "project": self.current_project,
            "trash_name": dst_name,
            "timestamp": timestamp
        })

        if self.current_tasks_file == filename:
            self.current_tasks_file = None

        return f"Archivo '{filename}' movido a la papelera."

    #Rename Task File
    def rename_task_file(self, old_name, new_name):
        if not self.current_project:
            return "No hay proyecto seleccionado."

        if not old_name.endswith(".md") or not new_name.endswith(".md"):
            return "Solo se pueden renombrar archivos .md"

        project_path = os.path.join(PROJECTS_DIR, self.current_project)
        old_path = os.path.join(project_path, old_name)
        new_path = os.path.join(project_path, new_name)

        if not os.path.isfile(old_path):
            return f"El archivo '{old_name}' no existe."

        if os.path.exists(new_path):
            return f"Ya existe un archivo llamado '{new_name}'."

        os.rename(old_path, new_path)
        self.undo_stack.append(
            {
        "action": "rename_task_file",
        "payload": {
        "project": self.current_project,
        "old_name": old_name,
        "new_name": new_name
                    }
            })

        if self.current_tasks_file == old_name:
            self.current_tasks_file = new_name


        return f"Archivo renombrado: {old_name} → {new_name}"

    ##################### UNDO ##########################
    
    #Undo Delete
    def undo_delete(self):
        entry = self._pop_last_trash()
        if not entry:
            return "No hay eliminaciones para deshacer."

        if entry["type"] == "project":
            src = os.path.join(TRASH_PROJECTS, entry["trash_name"])
            dst = os.path.join(PROJECTS_DIR, entry["original_name"])
        else:
            src = os.path.join(TRASH_TASKS, entry["trash_name"])
            dst = os.path.join(
                PROJECTS_DIR,
                entry["project"],
                entry["original_name"]
            )
            
        dst = self._resolve_restore_collision(dst)
        shutil.move(src, dst)
        
        if entry["type"] == "project":
            self.current_project = entry["original_name"]
            self.current_tasks_file = None

        if entry["type"] == "task_file":
            self.current_project = entry["project"]
            self.current_tasks_file = entry["original_name"]
                    
        return f"Restaurado: {entry['original_name']}"
    
    #Resolve Restore Collision
    def _resolve_restore_collision(self, path):
        if not os.path.exists(path):
            return path

        base, ext = os.path.splitext(path)
        i = 1
        while os.path.exists(f"{base}_restored({i}){ext}"):
            i += 1
        return f"{base}_restored({i}){ext}"
   
    #Restore From Trash
    def restore_from_trash(self):
        return self.undo_delete()


    #Undo Last Action
    def undo_last_action(self):
        if not self.undo_stack:
            return "No hay acciones para deshacer."

        action_entry = self.undo_stack.pop()
        action = action_entry.get("action")
        payload = action_entry.get("payload", {})

        # Undo rename project
        if action == "rename_project":
            old_name = payload["old_name"]
            new_name = payload["new_name"]

            old_path = os.path.join(PROJECTS_DIR, old_name)
            new_path = os.path.join(PROJECTS_DIR, new_name)

            if not os.path.isdir(new_path):
                return "No se puede deshacer: la carpeta ya no existe."

            if os.path.exists(old_path):
                return "No se puede deshacer: el nombre original ya existe."

            os.rename(new_path, old_path)
            if self.current_project == new_name:
                self.current_project = old_name

            return f"Proyecto restaurado: {new_name} → {old_name}"

        # Undo create project
        if action == "create_project":
            project = payload["project"]
            path = os.path.join(PROJECTS_DIR, project)

            if os.path.isdir(path):
                shutil.rmtree(path)

            if self.current_project == project:
                self.current_project = None
                self.current_tasks_file = None

            return f"Proyecto '{project}' eliminado (undo create)."

        # Undo edit file
        if action == "edit_file":
            path = os.path.join(
                PROJECTS_DIR,
                payload["project"],
                payload["filename"]
            )

            if payload["existed"]:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(payload["before"])
                return f"Cambios revertidos en '{payload['filename']}'."
            else:
                if os.path.exists(path):
                    os.remove(path)
                return f"Archivo '{payload['filename']}' eliminado (undo edit)."
        
        # Undo create tasks file
        if action == "create_tasks_file":
            project = payload["project"]
            filename = payload["filename"]

            path = os.path.join(PROJECTS_DIR, project, filename)

            if os.path.exists(path):
                os.remove(path)

            if self.current_tasks_file == filename:
                self.current_tasks_file = None

            return f"Archivo de tareas '{filename}' eliminado (undo create)."

        # Undo rename task file
        if action == "rename_task_file":
            project = payload["project"]
            old_name = payload["old_name"]
            new_name = payload["new_name"]

            project_path = os.path.join(PROJECTS_DIR, project)
            new_path = os.path.join(project_path, new_name)
            old_path = os.path.join(project_path, old_name)

            if os.path.exists(new_path):
                os.rename(new_path, old_path)

            if self.current_tasks_file == new_name:
                self.current_tasks_file = old_name

            return f"Archivo restaurado: {new_name} → {old_name}"

        # Undo complete task
        if action == "complete_task":
            path = os.path.join(
                PROJECTS_DIR,
                payload["project"],
                payload["tasks_file"]
            )

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            content = content.replace(
                f"- [x] {payload['task']}",
                f"- [ ] {payload['task']}"
            )

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"Tarea desmarcada: {payload['task']}"

        # Undo create task
        if action == "create_task":
            path = os.path.join(
                PROJECTS_DIR,
                payload["project"],
                payload["tasks_file"]
            )

            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            task_line = f"- [ ] {payload['task']}\n"
            if task_line in lines:
                lines.remove(task_line)

            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            return f"Tarea eliminada: {payload['task']}"

        return "Acción no reversible."


####################### PROCESS RESPONSE #################################
  
    def process_response(self, response):
        self.messages += response.output

        for output in response.output:
            if output.type == "function_call":
                fn_name = output.name
                args = json.loads(output.arguments)
                

                if self.pending_delete and fn_name not in ("confirm_delete", "cancel_delete","restore_from_trash","undo_delete"):
                    return "Debes confirmar o cancelar la eliminación pendiente."


                project_required = (
                    "list_files", "read_file", "edit_file",
                    "create_tasks_file", "select_tasks_file",
                    "create_task", "list_tasks", "complete_task",
                    "delete_task_file", "rename_task_file", "rename_project"
                )

                if fn_name in project_required and not self.current_project:
                    result = "Debes seleccionar un proyecto primero."

                    self.messages.append({
                        "type": "function_call_output",
                        "call_id": output.call_id,
                        "output": json.dumps({"result": result})
                    })
                    return True

                tasks_required = (
                    "create_task", "list_tasks","complete_task"
                    )

                if fn_name in tasks_required and not self.current_tasks_file:
                    result = "Debes seleccionar o crear un archivo de tareas primero."

                    self.messages.append({
                        "type": "function_call_output",
                        "call_id": output.call_id,
                        "output": json.dumps({"result": result})
                    })
                    return True
            
                #Projects
                
                if fn_name == "create_project":
                    result = self.create_project(**args)
                elif fn_name == "select_project":
                    result = self.select_project(**args)
                elif fn_name == "rename_project":
                    result = self.rename_project(**args)
                elif fn_name == "delete_project":
                    result = self.delete_project()
                elif fn_name == "confirm_delete":
                    result = self.confirm_delete()
                elif fn_name == "cancel_delete":
                    result = self.cancel_delete()
                elif fn_name == "summarize_project":
                    result = self.summarize_project()
                    
                #files
                
                elif fn_name == "list_files":
                    result = self.list_files()
                elif fn_name == "read_file":
                    result = self.read_file(**args)
                elif fn_name == "edit_file":
                    result = self.edit_file(**args)
                    
                #Tasks
                
                elif fn_name == "create_tasks_file":
                    result = self.create_tasks_file(**args)
                elif fn_name == "select_tasks_file":
                    result = self.select_tasks_file(**args)
                elif fn_name == "create_task":
                    result = self.create_task(**args)
                elif fn_name == "list_tasks":
                    result = self.list_tasks()
                elif fn_name == "complete_task":
                    result = self.complete_task(**args)
                elif fn_name == "delete_task_file":
                    result = self.delete_task_file(**args)
                elif fn_name == "rename_task_file":
                    result = self.rename_task_file(**args)
                    
                    #UNDO
                    
                elif fn_name == "undo_delete":
                    result = self.undo_delete()
                elif fn_name == "restore_from_trash":
                    result = self.restore_from_trash()
                elif fn_name == "undo_last_action":
                    result = self.undo_last_action()
                else:
                    result = "Herramienta no reconocida"
                
                self.messages.append({
                    "type": "function_call_output",
                    "call_id": output.call_id,
                    "output": json.dumps({"result": result})
                })

                return True

            elif output.type == "message":
                reply = "\n".join(part.text for part in output.content)
                print(f"Asistente: {reply}")

        return False


