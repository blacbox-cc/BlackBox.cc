# 🧠 JarvisAI Roadmap — v0.0.3 → v0.1.0

## Principios no negociables
- Estabilidad > inteligencia bruta
- Inteligencia visible y explicable
- Procesamiento por capas
- Separación estricta entre:
  - Interpretación
  - Decisión
  - Ejecución
  - Reflexión
- Cada versión cierra un loop completo:
  Input → Interpretación → Acción → Reflexión → Valor observable

---

## 📦 v0.0.3 — Baseline Cognitive Core (LOCKED)

### Rol
Base técnica estable, determinista y testeada.

### Estado
✔ Core funcional  
✔ Memoria persistente  
✔ Skills system sólido  
✔ Tests pasando  

### No se agregan features nuevas
Solo fixes críticos si rompen:
- determinismo
- boot
- tests

---

## 🔵 v0.0.4 — Stability & Observability

### Objetivo
Que Jarvis sea **confiable y entendible** incluso cuando falla.

### Core / Infra
- Manejo de errores tipados
- Validación estricta de config (schema)
- Health checks por componente
- Graceful degradation real

### CLI
- `--debug`
- NLU trace visible
- Confidence score por intent
- Errores con causa + sugerencia

### Brain
- ContextManager obligatorio en NLU
- Registro de decisiones
- Reflexión post-skill (solo lectura)

### Docs
- ARCHITECTURE.md actualizado
- “How Jarvis Thinks”
- Guía de contribución a skills
- CHANGELOG formal

📌 Valor:
Jarvis nunca “se rompe en silencio”.

---

## 🟢 v0.0.5 — Explainable NLU & Layered NLP

### Objetivo
NLU simple pero **explicable y trazable**.

### NLU / NLP
- Pipeline por capas:
  1. Normalización
  2. Parsing
  3. Intent detection
  4. Confidence scoring
- Threshold de confianza
- Manejo de ambigüedad
- Spell correction básica

### CLI UX
- Respuesta estructurada:
  - Interpretación
  - Acción
  - Resultado
- Comando `why`

### Skills
- Metadata obligatoria:
  - Qué hace
  - Riesgos
  - Tiempo estimado
- Pre-checks antes de ejecutar

📌 Valor:
Jarvis “piensa en voz alta”.

---

## 🟡 v0.0.6 — Memory That Matters & User Profiling

### Objetivo
Memoria útil, no acumulación ciega.

### Memory
- Short-term vs long-term
- Consolidación automática
- Facts con confidence-weight
- Pruning inteligente

### User Profile
- `what_do_you_know_about_me`
- Preferencias detectadas
- Resumen por sesiones

### Skills nuevas
- summarize_week
- frequent_actions
- patterns_detected

📌 Valor:
Jarvis reconoce patrones reales del usuario.

---

## 🟠 v0.0.7 — Reflection & Recommendation Engine

### Objetivo
Jarvis ayuda a mejorar decisiones (sin ejecutar).

### Reflection Engine
- Análisis de sesiones
- Detección de fricción
- Reglas de mejora

### Recomendaciones
- Automatizaciones sugeridas
- Repeticiones detectadas
- Fallos recurrentes

### Seguridad
- ❌ Ninguna acción automática
- ✔ Todo pasa por aprobación

📌 Valor:
Jarvis piensa sobre cómo trabajás.

---

## 🔴 v0.0.8 — Supervised Autonomy & Concurrency

### Objetivo
Autonomía **controlada y concurrente**.

### Planning
- Descomposición de objetivos
- Plan → aprobación → ejecución
- Simulación previa (dry-run)

### Concurrencia
- Gestión de hilos
- Multi-task controlado
- Cancelación segura

### Sistema
- Permisos por acción
- Logs de impacto
- Auditoría básica

📌 Valor:
Jarvis ejecuta, pero nunca sin permiso.

---

## 🟣 v0.1.0 — Serious Alpha Product

### Objetivo
Jarvis usable por terceros técnicos.

### Producto
- CLI robusta
- Voice estable
- Multi-session real
- Estado persistente confiable

### Ingeniería
- API interna estable
- Versionado semántico
- Tests de regresión
- Benchmarks automáticos

### Seguridad
- Roles
- Auditoría completa
- Safe defaults

📌 Resultado:
Jarvis deja de ser experimento y pasa a ser producto alfa serio.

---

## ✅ Definition of Done (todas las versiones)

- Boot sin warnings
- Tests pasando
- Docs actualizadas
- Valor observable desde CLI
- Ninguna feature a medias
- Cero deuda escondida
