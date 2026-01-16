# AI-Agent-projects
Un agente de IA en Python que permite gestionar proyectos y tareas usando lenguaje natural, apoyándose en herramientas (tools) y el filesystem local.  El agente puede crear proyectos, manejar múltiples archivos de tareas (.md), editar archivos, completar tareas y deshacer acciones (undo), incluyendo eliminaciones mediante una papelera temporal.

Desarrollado como proyecto educativo para aprender:

Agents

-Tool calling
-Manejo de estado
-Filesystem + undo
-Diseño de software orientado a IA

Características principales

📁 Gestión de proyectos

-Crear proyectos
-Seleccionar proyecto activo
-Renombrar proyectos
-Eliminar proyectos (con confirmación)
-Restaurar proyectos eliminados (undo)

📝 Gestión de archivos

-Listar archivos de un proyecto
-Leer archivos
-Editar o crear archivos
-Renombrar archivos
-Eliminar archivos de tareas (tasks.md, backend_tasks.md, etc.)

✅ Gestión de tareas

-Crear múltiples archivos de tareas por proyecto
-Seleccionar archivo de tareas activo
-Crear tareas
-Listar tareas
-Completar tareas

♻️ Undo / Deshacer

Undo de:
-creación de proyectos
-renombrado de proyectos
-creación / renombrado de archivos de tareas
-edición de archivos
-creación y completado de tareas
-eliminación de proyectos y archivos (vía papelera)

🗑️ Papelera  (.trash)

-Los proyectos y archivos eliminados no se borran inmediatamente
-Se mueven a .trash/
-Se guarda un manifest.json con metadatos
-Se pueden restaurar mientras la sesión esté activa
-Se evitan colisiones de nombres al restaurar (_restored(n))

🏗️ Estructura del proyecto
.
├── agent.py              # Lógica principal del agente
├── main.py               # Loop de ejecución + OpenAI API
├── projects/             # Proyectos creados por el agente
│   └── mi_proyecto/
│       ├── tasks.md
│       └── backend_tasks.md
├── .trash/               # Papelera temporal
│   ├── projects/
│   ├── tasksfiles/
│   └── manifest.json
├── requirements.txt
├── README.md
└── .env  

¿Cómo funciona el agente?

-Usa OpenAI Responses API con tools (function calling)
-El modelo decide:
  -cuándo responder con texto
  -cuándo llamar a una herramienta
-process_response:
  -valida contexto (proyecto seleccionado, archivo activo, confirmaciones)
  -ejecuta funciones reales en Python
  -devuelve el resultado al modelo

El agente no inventa acciones:
todo lo que hace está definido explícitamente en setup_tools.

🔐 Seguridad y diseño

-Validación estricta de nombres (regex)
-Prevención de path traversal
-Confirmación obligatoria para eliminaciones
-Undo controlado por sesión
-Sin borrado definitivo accidental

📦 Dependencias
openai
python-dotenv
