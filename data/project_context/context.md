# agent.md – Reglas y Contexto para el Agente de Desarrollo de Yari Medic

## Descripción General del Proyecto
Yari Medic es una plataforma SaaS multi-tenant de salud digital para LATAM, con aislamiento por ForeignKey (no esquemas separados).  
Objetivo principal: unificar clínicas, consultorios, médicos independientes, farmacias externas, laboratorios externos y pacientes en un ecosistema con fuerte componente de IA médica.

Versión actual (enero 2026): **6.2.0**  
Tecnologías principales:
- Backend: Django 5.2 + Python 3.11+
- Base de datos: PostgreSQL (shared schema + TenantModelMixin + TenantMiddleware)
- Frontend: Templates Django con Crispy Forms, Tailwind CSS o similar (espacios-y-4, btn-primary), AJAX/HTMX para interacciones dinámicas
- Cache / Tareas: Redis + Celery
- IA: Yari-AI (Chat MCP + voz con Whisper/Faster-Whisper) → planeado MedGemma 1.5 en servicio separado
- Despliegue: Docker / Docker Compose → Railway / VPS
- Otras: UV para paquetes, Mido/Midiutil para multimedia (si aplica), Snappy para compresión, no internet externo excepto proxies configurados (Polygon/Coingecko)
- Sistema creado con Django: Todo el core es Django-based, no introducir frameworks alternos sin justificación

## Apps Instaladas (de settings.py – INSTALLED_APPS)
Mantener coherencia con estas apps existentes; no agregar nuevas sin verificar redundancia:
- 'django.contrib.admin'
- 'django.contrib.auth'
- 'django.contrib.contenttypes'
- 'django.contrib.sessions'
- 'django.contrib.messages'
- 'django.contrib.staticfiles'
- 'crispy_forms' (para forms consistentes)
- 'core' (clínica, tenant middleware)
- 'softmedic' (configuración principal)
- 'crm' (casos, comunicaciones, seguimiento)
- 'pacientes' (gestión pacientes)
- 'citas' (agendamiento)
- 'historia_clinica' (EMR)
- 'facturacion' (unificada)
- 'facturacion_fiscal' (SENIAT)
- 'contaduria' (libros contables)
- 'empleados' (RRHH)
- 'laboratorios' (interno)
- 'laboratorios_externos' (externos)
- 'farmacia' (interna)
- 'farmacias' (externas)
- 'yari_ai' (IA dashboard)
- 'chat_mcp' (Model Context Protocol)
- 'analytics' (métricas)
- 'portal_paciente' (portal público)
- Otras posibles: 'celery', 'redis', 'rest_framework' (si APIs), 'haystack' (si búsqueda indexada ya existe)

## Reglas Obligatorias del Agente (NO NEGOCIABLES)

1. **Nunca duplicar ni romper lo existente**
   - Antes de crear cualquier modelo, vista, función, endpoint o template: **revisar exhaustivamente** si ya existe funcionalidad similar.
   - Buscar en: models.py, views.py, urls.py, templates/, signals.py, middleware, apps.py, settings.

2. **Conservar patrones y lógica actual**
   - Multi-tenant por FK → TenantModelMixin + TenantMiddleware + filtrado automático en querysets.
   - No cambiar a django-tenants ni esquemas separados.
   - No eliminar ni renombrar modelos/vistas existentes.
   - Mantener naming conventions actuales (ej: core.Clinica como tenant principal, farmacias.Farmacia, laboratorios_externos.Laboratorio).

3. **Coherencia total frontend-backend-BD**
   - Todo feature nuevo debe tener match completo: modelo → serializer/view → template/HTMX → portal correspondiente.
   - Conservar siempre el dashboard principal y los portales existentes (/crm/paciente/, /crm/medico/, etc.).
   - No introducir UI radicalmente diferente sin aprobación explícita.

4. **Buenas prácticas obligatorias**
   - Seguir estrictamente las **buenas prácticas de Django**: PEP8, DRY (Don't Repeat Yourself), Fat Models / Skinny Views.
   - Usar señales para automatizaciones (ej: crear perfil al guardar tenant).
   - Validaciones en clean() + full_clean().
   - Auditoría (logs o modelo Auditoria* cuando corresponda).
   - Internacionalización y multi-moneda (EUR/USD ya soportado en facturación).
   - Seguridad: nunca exponer datos sensibles sin anonimizar.
   - Tests: proponer al menos unit tests para lógica crítica.

5. **Filosofía de Desarrollo Yari Medic (KISS & Clean Code)**
   - **Principio KISS (Keep It Simple, Stupid)**: Evitar la sobre-ingeniería. La solución más simple y mantenible es siempre la preferida.
   - **No Hardcodear**: Prohibido el uso de valores quemados en el código. Usar `settings.py`, variables de entorno o constantes centralizadas.
   - **Arquitectura Multitenant Nativa**: Cada línea de código debe ser consciente del aislamiento por FK. Nunca olvidar el `TenantModelMixin` y el filtrado por `clinica`.
   - **Mejora Continua**: El código se deja mejor de lo que se encontró (Boy Scout Rule). Refactorizar proactivamente si se detecta deuda técnica.

5. **Flujo de trabajo estricto**
   1. Leer el **MCP** (Medical Context Protocol / propósito general del sistema).
   2. Analizar la tarea del usuario.
   3. Verificar si ya existe (modelo, vista, endpoint, template).
   4. Si existe → proponer mejoras/robustez (sin romper).
   5. Si no existe → diseñar solución coherente con arquitectura actual.
   6. Proponer rama git: feature/nombre-tarea o fix/nombre-bug.
   7. Documentar cambios en el commit y en docs/ si es relevante.
   8. Antes de merge: verificar migraciones, tests, coherencia UI/UX.

6. **Prohibiciones absolutas**
   - No crear mocks, placeholders ni data fake en producción.
   - No cambiar lógica de negocio sin consultar stakeholders.
   - No eliminar código funcional.
   - No introducir dependencias nuevas sin justificar (y preferir las ya existentes).
   - No tocar el portal paciente ni dashboard principal sin necesidad explícita.

## Estado Actual del Sistema – Módulos y Features Existentes (enero 2026)

### Core / Multi-Tenant
- core.Clinica → tenant principal + tipo_tenant
- TenantModelMixin + TenantMiddleware (filtrado automático por clinica_id)
- Provisionamiento automático (farmacias/labs crean Clinica interna)

### Módulos principales completos o avanzados
- pacientes/ → gestión pacientes, ficha, antecedentes
- citas/ → agendamiento inteligente, recordatorios
- historia_clinica/ → EMR, evoluciones, CIE-10
- hospitalizacion/ → camas, admisiones, altas
- emergencias/ → atención rápida
- imagenologia/ → ecografías, estudios, informes
- farmacia/ → interna (POS, insumos)
- farmacias/ → externas (inventario, lotes, vencimientos, delivery, turnos)
- laboratorios/ → interno
- laboratorios_externos/ → externos (pruebas, reactivos, turnos 24/7)
- facturacion/ → unificada, cargos, copagos
- facturacion_fiscal/ → SENIAT, hashes SHA-256
- contaduria/ → libros, balances, estados financieros
- finanzas/ → tesorería, conciliación, multi-moneda (USD/VES + cripto)
- empleados/ → RRHH básico
- crm/ → casos, seguimiento 360°, chat interno, comunicaciones
- portal_paciente/ → autogestión citas, resultados, pagos
- yari_ai/ → dashboard IA, Chat MCP, asistente voz
- analytics/ → métricas, tracking

### Features clave ya implementados
- Buscador inteligente (asíncrono): médicos, clínicas, farmacias turno, precios medicamentos, pruebas labs, donantes sangre
- Reviews equilibrados (Wilson Score) en perfiles públicos
- Pagos multi-moneda + P2P (Binance/BitPay, órdenes cobro, facturas, abonos)
- Integración aseguradoras (verificación pólizas, beneficiarios, cortes factura)
- Fidelización: sistema puntos + campañas marketing (segmentadas por rol/usuario)
- Administración central: RRHH, compras, contabilidad, facturación, control precios
- Presupuestos automáticos post-consulta → enviados al CRM del paciente (red farmacias/labs)
- Chat que inicia historial médico + seguimiento evolución vía CRM

### Tracción y límites actuales
- 2 laboratorios activos
- 1 clínica en pruebas
- 1 clínica próxima a entrar
- Freemium: 1 mes gratis → core 500 USD (clínicas) / 300 USD (farmacias/labs) + 100 USD/módulo adicional

## Patrones de Implementación para Evitar Redundancia y Alucinaciones

### 1. Análisis de Módulos Relacionados
- Siempre verificar módulos que usan entidades similares (ej: pacientes en citas, historia_clinica, emergencias, hospitalizacion, facturacion, crm).
- Usar código existente como referencia: buscar en pacientes/views.py para patrones de búsqueda, emergencias/views.py para manejo estados, crm/views.py para integración empresas.

### 2. Desarrollo Incremental No Destructivo
- Agregar campos con defaults y blank=True para migraciones suaves.
- Ejecutar siempre makemigrations y migrate.

### 3. Consistencia Frontend-Backend
- Frontend: Mantener estructuras como <form method="post" class="space-y-4"> con {% csrf_token %} y {{ form|crispy }} + <button class="btn btn-primary">.
- Backend: Usar clases View con get/post, form.valid() → save() → redirect().

### 4. Verificación de Contexto
- Revisar CHANGELOG.md para cambios recientes.
- Consultar CHECKLIST.md para estado módulos.
- Verificar tecnologías en README.md.

### 5. Validación de Datos Cruzada
- Asegurar flujo: form valida → modelo guarda → template muestra.

### 6. Integración Segura
- Usar APIs existentes (CRM, Yari AI).
- Preservar middleware y decoradores (@login_required, @permission_required).
- Manejo errores: try/except con logger.error + render error.html.

## Indexación y Mejora de Búsquedas
- Usar Django Search (full-text search con PostgreSQL) o Haystack (si instalado) para indexación.
- Patrones existentes: búsquedas asíncronas en buscador inteligente – extender con SearchIndex/SearchQuerySet si no existe, pero verificar primero si hay redundancia en yari_ai o analytics.
- Para precisión: agregar índices en BD (ej: models.Index(fields=['campo_busqueda'])) en migraciones, sin duplicar queries existentes.

## Instrucciones finales para el agente
- Siempre priorizar: coherencia > velocidad > nuevas features
- Si hay duda sobre si algo ya existe → preguntar explícito antes de actuar
- Mantener el foco en producción: código limpio, migraciones seguras, cero breaking changes sin aviso
- Documentar todo en docs/ (PLAN_MAESTRO_DESARROLLO.md, ARQUITECTURA_*.md)

Última actualización de este archivo: enero 2026