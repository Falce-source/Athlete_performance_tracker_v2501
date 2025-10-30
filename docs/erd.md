🧠 Núcleo de identidad
┌────────────┐
│  usuarios  │
├────────────┤
│ id_usuario (PK) │
│ nombre           │
│ email            │
│ rol              │
└────────────┘
        │
        ▼
┌────────────┐
│  atletas   │
├────────────┤
│ id_atleta (PK)   │
│ id_usuario (FK)  │
│ nombre           │
│ edad, talla...   │
└────────────┘

📅 Interfaz principal
┌────────────────────┐
│ calendario_eventos │
├────────────────────┤
│ id_evento (PK)      │
│ id_atleta (FK)      │
│ fecha               │
│ tipo_evento         │
│ valor, notas        │
└────────────────────┘

┌────────────┐
│  sesiones  │
├────────────┤
│ id_sesion (PK)     │
│ id_atleta (FK)     │
│ fecha              │
│ tipo_sesion        │
│ planificado_json   │
│ realizado_json     │
└────────────┘

┌────────────┐
│  metricas  │
├────────────┤
│ id_metrica (PK)    │
│ id_atleta (FK)     │
│ fecha              │
│ tipo_metrica       │
│ valor, unidad      │
└────────────┘

┌──────────────┐
│ comentarios  │
├──────────────┤
│ id_comentario (PK) │
│ id_atleta (FK)     │
│ id_autor (FK)      │
│ texto              │
│ visible_para       │
└──────────────┘

🧪 Tests y evaluaciones
┌────────────────────┐
│ test_composicion   │
├────────────────────┤
│ id_test (PK)        │
│ id_atleta (FK)      │
│ fecha               │
│ skinfolds, circ...  │
└────────────────────┘

┌────────────────────┐
│ test_metabolismo   │
├────────────────────┤
│ id_test (PK)        │
│ id_atleta (FK)      │
│ fecha               │
│ sudor, bicarbonato…│
└────────────────────┘

┌────────────────────────────┐
│ test_rendimiento_fuerza    │
├────────────────────────────┤
│ id_test (PK)                │
│ id_atleta (FK)              │
│ fecha                       │
│ ejercicio, kg, potencia…    │
└────────────────────────────┘

┌────────────────────────────┐
│ test_rendimiento_saltos    │
├────────────────────────────┤
│ id_test (PK)                │
│ id_atleta (FK)              │
│ fecha                       │
│ tipo_salto, RSI, FV50…      │
└────────────────────────────┘

🧍 Exploración musculoesquelética
┌────────────────────────────┐
│ exploracion_musculoesq     │
├────────────────────────────┤
│ id_exploracion (PK)         │
│ id_atleta (FK)              │
│ fecha                       │
│ zona, descripcion, severidad│
└────────────────────────────┘

🏋️ Prescripción de fuerza
┌────────────────────────────┐
│ planificaciones_fuerza     │
├────────────────────────────┤
│ id_plan (PK)                │
│ id_atleta (FK)              │
│ fecha, notas                │
└────────────────────────────┘
        │
        ▼
┌────────────────────────────┐
│ ejercicios_fuerza          │
├────────────────────────────┤
│ id_ejercicio (PK)          │
│ id_plan (FK)               │
│ nombre, kg, series, reps   │
└────────────────────────────┘

🍽️ Prescripción de nutrición
┌────────────────────────────┐
│ prescripcion_nutricion     │
├────────────────────────────┤
│ id_presc (PK)               │
│ id_atleta (FK)              │
│ fecha                       │
│ suplemento, macros, notas   │
└────────────────────────────┘

---

## 🔗 Relaciones clave

- `usuarios` ↔ `atletas` → 1:N o 1:1  
- `atletas` ↔ todas las demás tablas → 1:N  
- `planificaciones_fuerza` ↔ `ejercicios_fuerza` → 1:N  
- `comentarios` ↔ `usuarios` (autor) → 1:N  
- `sesiones` puede incluir métricas derivadas (RPE, FC reposo) que se reflejan en `metricas`

---

## 🧩 Espacio reservado para futuras extensiones

- `api_integraciones` → sincronización con plataformas externas (TrainingPeaks, etc.)  
- `alertas` → notificaciones internas (competición próxima, lesión activa, etc.)  
- `versiones` → trazabilidad de cambios en prescripciones o tests

---

