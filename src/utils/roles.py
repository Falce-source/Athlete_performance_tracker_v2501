from dataclasses import dataclass
from typing import Dict, List
import src.persistencia.sql as sql

# Pestañas disponibles (normaliza nombres)
TABS = [
    "Inicio",
    "Perfil Atleta",
    "Calendario",
    "Graficas",
    "Comentarios",
    "Tests",
    "Fuerza",
    "Nutricion",
    "Usuarios",
    "Backups",
    "Auditoria",
    "Historial de Validaciones"
]

# Permisos de visibilidad por rol
PERMISOS_TABS: Dict[str, List[str]] = {
    "admin": [
        "Inicio", "Perfil Atleta", "Calendario", "Graficas", "Comentarios", "Tests",
        "Fuerza", "Nutricion", "Usuarios", "Backups", "Auditoria", "Historial de Validaciones"
    ],
    "entrenadora": [
        "Inicio", "Perfil Atleta", "Calendario", "Graficas", "Comentarios", "Tests",
        "Fuerza", "Nutricion"
    ],
    "atleta": [
        "Inicio", "Perfil Atleta", "Calendario", "Graficas"
    ],
}

# Tipos de acciones básicas para granularidad dentro de pestañas
ACCIONES = [
    "ver",          # acceso de lectura a la pestaña o recurso
    "crear",        # crear contenido (eventos, notas, etc.)
    "editar",       # editar contenido
    "borrar",       # borrar contenido
    "exportar",     # exportar datos (CSV/Excel)
    "backup",       # crear/gestionar backups
    "auditar",      # ver auditoría
]

@dataclass(frozen=True)
class Contexto:
    """Contexto mínimo para evaluar permisos de acción.
    - rol_actual: rol del usuario (admin, entrenadora, atleta)
    - usuario_id: id del usuario actual
    - atleta_id: id del atleta en contexto (seleccionado)
    - propietario_id: id del propietario del recurso (opcional, p.ej. dueño del evento)
    """
    rol_actual: str
    usuario_id: int
    atleta_id: int
    propietario_id: int | None = None


def puede_ver_pestana(rol: str, pestana: str) -> bool:
    """Devuelve True si el rol puede ver la pestaña indicada."""
    visibles = PERMISOS_TABS.get(rol, [])
    return pestana in visibles


def tabs_visibles_por_rol(rol: str) -> List[str]:
    """Lista de pestañas visibles para un rol."""
    return PERMISOS_TABS.get(rol, [])


# Políticas de acción (ejemplos prácticos)
def puede_gestionar_usuarios(ctx: Contexto) -> bool:
    """Solo admin puede ver/gestionar Usuarios."""
    return ctx.rol_actual == "admin"


def puede_hacer_backup(ctx: Contexto) -> bool:
    """Backups sólo para admin."""
    return ctx.rol_actual == "admin"


def puede_ver_auditoria(ctx: Contexto) -> bool:
    """Auditoría visible para admin; entrenadora puede ver auditoría filtrada (opcional)."""
    return ctx.rol_actual in ("admin",)


def puede_crear_evento_calendario(ctx: Contexto) -> bool:
    """Crear evento en calendario:
    - admin: siempre
    - entrenadora: sobre atletas que gestiona (asumimos validación previa)
    - atleta: solo sobre sí mismo (ctx.atleta_id == ctx.usuario_id o propietario_id)
    """
    if ctx.rol_actual == "admin":
        return True
    if ctx.rol_actual == "entrenadora":
        # Aquí podrías validar la asignación entrenadora-atleta en SQL.
        return True
    if ctx.rol_actual == "atleta":
        atleta_vinculado = sql.obtener_id_atleta_por_usuario(ctx.usuario_id)
        return atleta_vinculado == (ctx.propietario_id or ctx.atleta_id)
    return False

def puede_editar_evento_calendario(ctx: Contexto) -> bool:
    """Editar evento en calendario: misma política que crear, con control de propietario."""
    if ctx.rol_actual == "admin":
        return True
    if ctx.rol_actual == "entrenadora":
        return True
    if ctx.rol_actual == "atleta":
        atleta_vinculado = sql.obtener_id_atleta_por_usuario(ctx.usuario_id)
        return atleta_vinculado == (ctx.propietario_id or ctx.atleta_id)
    return False

def puede_borrar_evento_calendario(ctx: Contexto) -> bool:
    """Borrar evento en calendario: más restrictivo para atleta (solo lo propio)."""
    if ctx.rol_actual == "admin":
        return True
    if ctx.rol_actual == "entrenadora":
        return True
    if ctx.rol_actual == "atleta":
        atleta_vinculado = sql.obtener_id_atleta_por_usuario(ctx.usuario_id)
        return atleta_vinculado == (ctx.propietario_id or ctx.atleta_id)
    return False


def puede_editar_perfil_atleta(ctx: Contexto) -> bool:
    """Editar perfil:
    - admin: cualquiera
    - entrenadora: atletas que gestiona (validar en SQL)
    - atleta: solo su propio perfil (ctx.atleta_id == ctx.usuario_id)
    """
    if ctx.rol_actual == "admin":
        return True
    if ctx.rol_actual == "entrenadora":
        return True
    if ctx.rol_actual == "atleta":
        atleta_vinculado = sql.obtener_id_atleta_por_usuario(ctx.usuario_id)
        return atleta_vinculado == (ctx.propietario_id or ctx.atleta_id)
    return False
