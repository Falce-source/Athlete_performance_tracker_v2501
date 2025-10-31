# Gestión de la base de datos con manage.py

Este script permite **inicializar, resetear y poblar con datos de prueba** la base de datos `base.db`.

---

## 📂 Ubicación
El archivo se encuentra en:

test/manage.py

---

## 🚀 Uso recomendado

Siempre ejecuta los comandos desde la **raíz del proyecto** (no desde dentro de `tests/`).

### Inicializar la base de datos
Crea `base.db` con todas las tablas (`usuarios`, `atletas`, `eventos`):

```bash
python -m tests.manage init

### Resetear la base de datos
Elimina base.db y la recrea desde cero:

python -m tests.manage reset

### Poblar con datos de prueba
Inserta usuarios, atletas y eventos de ejemplo:

python -m tests.manage seed

### ⚠️ Notas importantes
- Si ejecutas python tests/manage.py ... directamente, puede dar error ModuleNotFoundError: No module named 'src'.
Por eso se recomienda usar python -m tests.manage ... desde la raíz.
- El comando reset borra todos los datos de base.db. Úsalo solo en desarrollo.
- El comando seed es útil para probar la interfaz de Streamlit con datos ficticios.

###✅ Flujo típico de trabajo
- Resetear la base:
python -m tests.manage reset
- Poblarla con datos de prueba:
python -m tests.manage seed
- Ejecutar la app:
streamlit run app.py



