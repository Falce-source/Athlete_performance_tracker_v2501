from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, date, timezone, UTC
from sqlalchemy import JSON  # si usas SQLAlchemy 1.4+ puedes definir JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, joinedload
import json
import os
import shutil
import src.persistencia.backup_storage as backup_storage
import sqlite3

 # ─────────────────────────────────────────────
 # CONFIGURACIÓN BÁSICA
 # ─────────────────────────────────────────────

DB_PATH = os.path.join("/tmp", "base.db")
# Inicialización robusta: siempre intentamos restaurar el último backup desde Drive.
# Si no hay backups, arrancamos vacíos y generamos el primer backup.
NEED_INIT_SCHEMA = False
try:
    backups = backup_storage.listar_backups()
    if backups:
        ultimo = sorted(backups, key=lambda b: b["createdTime"], reverse=True)[0]
        backup_storage.descargar_backup(ultimo["id"], DB_PATH)
        print(f"📦 Restaurado backup inicial desde Drive: {ultimo['name']}")
    else:
        print("ℹ️ No hay backups en Drive: se iniciará base vacía.")
        # Creamos un archivo vacío; el esquema se creará tras configurar el engine.
        open(DB_PATH, "wb").close()
        NEED_INIT_SCHEMA = True
except Exception as e:
    print(f"⚠️ Error al consultar/restaurar backups: {e}")
    # Fallback: si existe base local en el repo la copiamos; si no, vacía.
    if os.path.exists("base.db"):
        shutil.copy("base.db", DB_PATH)
        print("📄 Copiado base.db local al /tmp como semilla.")
    else:
        open(DB_PATH, "wb").close()
        NEED_INIT_SCHEMA = True

DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

# ─────────────────────────────────────────────
# MIGRACIÓN AUTOMÁTICA: columna password_hash
# ─────────────────────────────────────────────

def ensure_schema():
    """Asegura que la tabla atletas tenga las columnas propietario_id y atleta_usuario_id"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(atletas);")
        cols = [row[1] for row in cursor.fetchall()]
        changed = False
        if "propietario_id" not in cols:
            cursor.execute("ALTER TABLE atletas ADD COLUMN propietario_id INTEGER;")
            changed = True
        if "atleta_usuario_id" not in cols:
            cursor.execute("ALTER TABLE atletas ADD COLUMN atleta_usuario_id INTEGER;")
            changed = True
        if changed:
            conn.commit()
            print("✅ Esquema atletas actualizado (propietario_id / atleta_usuario_id)")
        conn.close()
    except Exception as e:
        print(f"⚠️ Error al asegurar esquema atletas: {e}")

# Helper para sincronizar backup tras cada commit
def _sync_backup():
    try:
        file_id = backup_storage.subir_backup(DB_PATH)
        backup_storage.rotar_backups(max_backups=5)
        print(f"Backup actualizado en Drive: {file_id}")
    except Exception as e:
        print(f"⚠️ Error al subir backup: {e}")

# Si se marcó que no había backups, inicializamos el esquema y creamos el primer backup vacío.
if NEED_INIT_SCHEMA:
    try:
        # Nota: el esquema se define más adelante con los modelos; este bloque se ejecutará al final del import.
        # Para asegurar creación del esquema, lo reforzaremos en init_db() también.
        print("🛠️ Inicializando esquema en base vacía...")
        # La función init_db se define más abajo; si aún no existe en este punto por orden de import,
        # se recomienda llamar a Base.metadata.create_all en init_db() al primer uso.
        # Aquí no llamamos directamente para evitar dependencia del orden: se crea en init_db().
    except Exception as e:
        print(f"⚠️ Error al inicializar esquema: {e}")

# ─────────────────────────────────────────────
# MODELOS
# ─────────────────────────────────────────────

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    rol = Column(String, nullable=False)  # admin, entrenadora, atleta
    password_hash = Column(String, nullable=False)  # 🔑 nuevo campo para login seguro
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relación con atletas como entrenadora asignada
    atletas = relationship("Atleta", back_populates="usuario", foreign_keys="Atleta.id_usuario")

    # Relación con atletas creados (propietario)
    atletas_creados = relationship("Atleta", back_populates="propietario", foreign_keys="Atleta.propietario_id")

    # (Opcional) relación inversa a perfiles que tienen esta cuenta como 'atleta_usuario'
    perfiles_como_atleta = relationship(
        "Atleta",
        back_populates="atleta_usuario",
        foreign_keys="Atleta.atleta_usuario_id"
    )

class Atleta(Base):
    __tablename__ = "atletas"

    id_atleta = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

    # Usuario que creó el atleta (admin o entrenadora)
    propietario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

    # Usuario del propio atleta (cuenta de login del atleta)
    atleta_usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

    atleta_usuario = relationship(
        "Usuario",
        back_populates="perfiles_como_atleta",
        foreign_keys=[atleta_usuario_id]
    )

    nombre = Column(String, nullable=False)
    apellidos = Column(String)
    edad = Column(Integer)
    talla = Column(Integer)
    contacto = Column(String)
    deporte = Column(String)
    modalidad = Column(String)
    nivel = Column(String)
    equipo = Column(String)
    alergias = Column(Text)
    consentimiento = Column(Boolean, default=False)
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Entrenadora asignada
    usuario = relationship("Usuario", back_populates="atletas", foreign_keys=[id_usuario])

    # Propietario (quien creó el atleta)
    propietario = relationship("Usuario", back_populates="atletas_creados", foreign_keys=[propietario_id])

    # Cuenta de usuario del propio atleta (login)
    atleta_usuario = relationship("Usuario", foreign_keys=[atleta_usuario_id])

  # Relación con Evento
    eventos = relationship("Evento", back_populates="atleta", cascade="all, delete-orphan")

    metricas = relationship("Metrica", back_populates="atleta", cascade="all, delete-orphan")
    comentarios = relationship("Comentario", back_populates="atleta", cascade="all, delete-orphan")

class Evento(Base):
    __tablename__ = "eventos"

    id_evento = Column(Integer, primary_key=True, autoincrement=True)
    id_atleta = Column(Integer, ForeignKey("atletas.id_atleta"), nullable=False)

    titulo = Column(String, nullable=False)          # Ej: "Entrenamiento fuerza"
    descripcion = Column(Text)                       # Detalles opcionales
    fecha = Column(DateTime(timezone=True), nullable=False)    # Cuándo ocurre
    lugar = Column(String)                           # Ej: "Gimnasio municipal"
    tipo = Column(String)                            # Ej: "Entrenamiento", "Competición", "Revisión médica"

    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relación con Atleta
    atleta = relationship("Atleta", back_populates="eventos")

# ─────────────────────────────────────────────
# INICIALIZACIÓN
# ─────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# FUNCIONES CRUD: USUARIOS
# ─────────────────────────────────────────────

def crear_usuario(nombre, email, rol, password_hash: str):
    """Crea un usuario con contraseña ya hasheada"""
    with SessionLocal() as session:
        usuario = Usuario(nombre=nombre, email=email, rol=rol, password_hash=password_hash)
        session.add(usuario)
        session.flush()
        session.refresh(usuario)
        session.commit()
        _sync_backup()
        return usuario

def obtener_usuarios():
    with SessionLocal() as session:
        return session.query(Usuario).all()

def obtener_usuario_por_email(email: str):
    """Devuelve un usuario por email o None"""
    with SessionLocal() as session:
        return session.query(Usuario).filter_by(email=email).first()

def obtener_usuario_por_id(id_usuario: int):
    """Devuelve un usuario por id o None"""
    with SessionLocal() as session:
        return session.query(Usuario).filter_by(id_usuario=id_usuario).first()

def actualizar_password(id_usuario: int, nuevo_hash: str):
    """Actualiza la contraseña de un usuario"""
    with SessionLocal() as session:
        usuario = session.query(Usuario).filter_by(id_usuario=id_usuario).first()
        if not usuario:
            return None
        usuario.password_hash = nuevo_hash
        session.commit()
        session.refresh(usuario)
        _sync_backup()
        return usuario

def actualizar_usuario(id_usuario, **kwargs):
    with SessionLocal() as session:
        usuario = session.query(Usuario).filter_by(id_usuario=id_usuario).first()
        if not usuario:
            return None

        # 🚨 Protección: impedir cambiar el rol del último admin
        if "rol" in kwargs and usuario.rol == "admin" and kwargs["rol"] != "admin":
            admins = session.query(Usuario).filter_by(rol="admin").all()
            if len(admins) <= 1:
                raise ValueError("⚠️ No se puede cambiar el rol del último admin del sistema")

        for campo, valor in kwargs.items():
            if hasattr(usuario, campo):
                setattr(usuario, campo, valor)
        session.commit()
        session.refresh(usuario)
        _sync_backup()
        return usuario

def borrar_usuario(id_usuario):
    with SessionLocal() as session:
        usuario = session.query(Usuario).filter_by(id_usuario=id_usuario).first()
        if not usuario:
            return False

        # 🚨 Protección: impedir borrar el último admin
        if usuario.rol == "admin":
            admins = session.query(Usuario).filter_by(rol="admin").all()
            if len(admins) <= 1:
                raise ValueError("⚠️ No se puede eliminar el último admin del sistema")

        session.delete(usuario)
        session.commit()
        _sync_backup()
        return True

# ─────────────────────────────────────────────
# FUNCIONES CRUD: ATLETAS
# ─────────────────────────────────────────────

def crear_atleta(**kwargs):
    with SessionLocal() as session:
        atleta = Atleta(**kwargs)
        session.add(atleta)
        session.flush()
        session.refresh(atleta)
        session.commit()
        _sync_backup()
        return atleta

def obtener_atletas():
    with SessionLocal() as session:
        return session.query(Atleta)\
            .options(joinedload(Atleta.usuario))\
            .all()

def obtener_atletas_por_usuario(id_usuario):
    with SessionLocal() as session:
        return session.query(Atleta)\
            .options(joinedload(Atleta.usuario))\
            .filter_by(id_usuario=id_usuario)\
            .all()

def obtener_atleta_por_id(id_atleta):
    with SessionLocal() as session:
        return session.query(Atleta)\
            .options(joinedload(Atleta.usuario))\
            .filter_by(id_atleta=id_atleta)\
            .first()

def actualizar_atleta(id_atleta, **kwargs):
    """
    Actualiza uno o varios campos de un atleta existente.
    Uso:
        actualizar_atleta(3, nombre="Nuevo", nivel="Avanzado")
    """
    with SessionLocal() as session:
        atleta = session.query(Atleta).filter_by(id_atleta=id_atleta).first()
        if not atleta:
            return None

        # Solo actualizamos los campos que existen en el modelo
        for campo, valor in kwargs.items():
            if hasattr(atleta, campo):
                setattr(atleta, campo, valor)

        session.commit()
        session.refresh(atleta)
        _sync_backup()
        return atleta

def borrar_atleta(id_atleta):
    with SessionLocal() as session:
        atleta = session.query(Atleta).filter_by(id_atleta=id_atleta).first()
        if atleta:
            session.delete(atleta)
            session.commit()
            _sync_backup()

# ─────────────────────────────────────────────
# FUNCIONES CRUD: EVENTOS
# ─────────────────────────────────────────────

def crear_evento(id_atleta, titulo, fecha, descripcion=None, lugar=None, tipo=None):
    with SessionLocal() as session:
        evento = Evento(
            id_atleta=id_atleta,
            titulo=titulo,
            fecha=fecha,
            descripcion=descripcion,
            lugar=lugar,
            tipo=tipo,
        )
        session.add(evento)
        session.flush()
        session.refresh(evento)
        session.commit()
        _sync_backup()
        return evento

def obtener_eventos():
    with SessionLocal() as session:
        return session.query(Evento).all()

def obtener_eventos_basicos_por_atleta(id_atleta):
    """Obtiene eventos de la tabla 'eventos' asociados a un atleta"""
    with SessionLocal() as session:
        return session.query(Evento).filter_by(id_atleta=id_atleta).all()

def actualizar_evento(id_evento, **kwargs):
    with SessionLocal() as session:
        evento = session.query(Evento).filter_by(id_evento=id_evento).first()
        if not evento:
            return None
        for campo, valor in kwargs.items():
            if hasattr(evento, campo):
                setattr(evento, campo, valor)
        session.commit()
        session.refresh(evento)
        _sync_backup()
        return evento

def borrar_evento(id_evento):
    with SessionLocal() as session:
        evento = session.query(Evento).filter_by(id_evento=id_evento).first()
        if evento:
            session.delete(evento)
            session.commit()
            _sync_backup()

# ─────────────────────────────────────────────
# MODELOS EXTRA: CALENDARIO, SESIONES, MÉTRICAS, COMENTARIOS
# ─────────────────────────────────────────────

class CalendarioEvento(Base):
    __tablename__ = "calendario_eventos"

    id_evento = Column(Integer, primary_key=True, autoincrement=True)
    id_atleta = Column(Integer, ForeignKey("atletas.id_atleta"), nullable=False)
    fecha = Column(Date, nullable=False)   # solo fecha, sin hora ni zona horaria
    tipo_evento = Column(String, nullable=False)  # "estado_diario", "competicion", "cita_test"
    valor = Column(Text)  # JSON serializado o string según tipo
    notas = Column(Text)  # notas libres
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

class Sesion(Base):
    __tablename__ = "sesiones"

    id_sesion = Column(Integer, primary_key=True, autoincrement=True)
    id_atleta = Column(Integer, ForeignKey("atletas.id_atleta"), nullable=False)
    fecha = Column(DateTime(timezone=True), nullable=False)
    tipo_sesion = Column(String, nullable=False)
    planificado_json = Column(Text)
    realizado_json = Column(Text)

class Metrica(Base):
    __tablename__ = "metricas"

    id_metrica = Column(Integer, primary_key=True, autoincrement=True)
    id_atleta = Column(Integer, ForeignKey("atletas.id_atleta"), nullable=False)
    fecha = Column(DateTime(timezone=True), nullable=False)
    tipo_metrica = Column(String, nullable=False)
    valor = Column(String)
    unidad = Column(String)

    atleta = relationship("Atleta", back_populates="metricas")


class Comentario(Base):
    __tablename__ = "comentarios"

    id_comentario = Column(Integer, primary_key=True, autoincrement=True)
    id_atleta = Column(Integer, ForeignKey("atletas.id_atleta"), nullable=False)
    id_autor = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    texto = Column(Text, nullable=False)
    visible_para = Column(String, default="staff")
    fecha = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    atleta = relationship("Atleta", back_populates="comentarios")

# ─────────────────────────────────────────────
# CRUD: CALENDARIO
# ─────────────────────────────────────────────
def crear_evento_calendario(id_atleta, fecha, tipo_evento, valor, notas=None):
    with SessionLocal() as session:
        # Normalizamos fecha a medianoche sin zona horaria (naive)
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        elif isinstance(fecha, date):
            fecha = fecha
        elif isinstance(fecha, str):
            try:
                base = datetime.fromisoformat(fecha.replace("Z", "+00:00"))
                fecha = base.date()
            except Exception:
                fecha = date.today()
        else:
            fecha = date.today()

        evento = CalendarioEvento(
            id_atleta=id_atleta,
            fecha=fecha,
            tipo_evento=tipo_evento,
            valor=json.dumps(valor) if isinstance(valor, dict) else valor,
            notas=notas,
        )
        session.add(evento)
        session.commit()
        session.refresh(evento)
        _sync_backup()
        return evento

# ─────────────────────────────────────────────
# HELPERS DE TRANSFORMACIÓN
# ─────────────────────────────────────────────

def evento_to_dict(evento):
    """Convierte un objeto CalendarioEvento en un dict listo para el calendario."""
    try:
        valor_dict = json.loads(evento.valor) if evento.valor else {}
    except Exception:
        valor_dict = {}

        # Normalización de claves antiguas
    mapping = {
        "Síntomas": "sintomas",
        "Sintomas": "sintomas",
        "Menstruacion": "menstruacion",
        "Ovulacion": "ovulacion",
        "Altitud": "altitud",
        "Respiratorio": "respiratorio",
        "Calor": "calor",
        "Lesión": "lesion",
        "Lesion": "lesion",
        "Comentario": "comentario_extra",
        "Comentario_extra": "comentario_extra",
    }
    normalizado = {}
    for k, v in valor_dict.items():
        normalizado[mapping.get(k, k)] = v

    return {
        "id": evento.id_evento,
        # Normalizamos a ISO con hora 00:00 para que FullCalendar lo pinte en el día correcto
        "start": datetime.combine(evento.fecha, datetime.min.time()).isoformat(),
        "allDay": True,
        "tipo_evento": evento.tipo_evento,
        # Aquí ya entregamos el dict deserializado para que mostrar_calendario_interactivo
        # pueda acceder a claves como "Síntomas", "Menstruacion", etc.
        "extendedProps": normalizado,
        "notas": evento.notas or ""
    }

# ─────────────────────────────────────────────
# HELPERS ESPECÍFICOS POR TIPO DE EVENTO
# ─────────────────────────────────────────────

def crear_estado_diario(id_atleta, fecha, valores, notas=None):
    """
    Crea un evento de tipo 'estado_diario' con un JSON de parámetros:
    {"sintomas": "...", "menstruacion": "...", "ovulacion": "...", "altitud": True, ...}
    """
    return crear_evento_calendario(id_atleta, fecha, "estado_diario", valores, notas)

def crear_competicion(id_atleta, fecha, detalles, notas=None):
    """
    Crea un evento de tipo 'competicion'.
    detalles: dict con claves como {"nombre": "Campeonato regional", "lugar": "Madrid"}
    """
    return crear_evento_calendario(id_atleta, fecha, "competicion", detalles, notas)

def crear_cita_test(id_atleta, fecha, detalles, notas=None):
    """
    Crea un evento de tipo 'cita_test'.
    detalles: dict con claves como {"tipo": "Test VO2max", "lugar": "Laboratorio"}
    """
    return crear_evento_calendario(id_atleta, fecha, "cita_test", detalles, notas)

def obtener_competiciones_por_atleta(id_atleta):
    with SessionLocal() as session:
        eventos = session.query(CalendarioEvento).filter_by(
            id_atleta=id_atleta, tipo_evento="competicion"
        ).order_by(CalendarioEvento.fecha.desc()).all()
        return [evento_to_dict(ev) for ev in eventos]

def obtener_citas_test_por_atleta(id_atleta):
    with SessionLocal() as session:
        eventos = session.query(CalendarioEvento).filter_by(
            id_atleta=id_atleta, tipo_evento="cita_test"
        ).order_by(CalendarioEvento.fecha.desc()).all()
        return [evento_to_dict(ev) for ev in eventos]

def actualizar_evento_calendario(id_atleta, fecha, valores_actualizados, notas=None):
    """
    Actualiza un evento de calendario existente para un atleta en una fecha concreta.
    Si no existe, devuelve None.
    """
    with SessionLocal() as session:
        # Normalizamos fecha a medianoche sin zona horaria (naive)
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        elif isinstance(fecha, date):
            fecha = fecha
        elif isinstance(fecha, str):
            try:
                base = datetime.fromisoformat(fecha.replace("Z", "+00:00"))
                fecha = base.date()
            except Exception:
                fecha = date.today()
        else:
            fecha = date.today()

        evento = session.query(CalendarioEvento).filter_by(
            id_atleta=id_atleta,
            fecha=fecha
        ).first()
        if not evento:
            return None

        # Guardamos el dict como JSON serializado
        evento.valor = json.dumps(valores_actualizados) if isinstance(valores_actualizados, dict) else valores_actualizados
        if notas is not None:
            evento.notas = notas

        session.commit()
        session.refresh(evento)
        _sync_backup()
        return evento

def actualizar_evento_calendario_por_id(id_evento: int, valores_actualizados, notas=None):
    """
    Actualiza un evento de calendario existente usando su id_evento único.
    Devuelve el evento actualizado o None si no existe.
    """
    with SessionLocal() as session:
        evento = session.query(CalendarioEvento).filter_by(id_evento=id_evento).first()
        if not evento:
            return None

        evento.valor = json.dumps(valores_actualizados) if isinstance(valores_actualizados, dict) else valores_actualizados
        if notas is not None:
            evento.notas = notas

        session.commit()
        session.refresh(evento)
        _sync_backup()
        return evento

def obtener_eventos_calendario_por_atleta(id_atleta, rol_actual="admin"):
    with SessionLocal() as session:
        query = session.query(CalendarioEvento).filter_by(id_atleta=id_atleta)
        if rol_actual == "admin":
            eventos = query.order_by(CalendarioEvento.fecha.desc()).all()
        elif rol_actual == "entrenadora":
            eventos = query.filter(
                CalendarioEvento.tipo_evento.notin_(["PrivadoAtleta"])
            ).order_by(CalendarioEvento.fecha.desc()).all()
        elif rol_actual == "atleta":
            eventos = query.filter(
                CalendarioEvento.tipo_evento.notin_(["PrivadoStaff"])
            ).order_by(CalendarioEvento.fecha.desc()).all()
        else:
            return []

        # 🔑 Transformamos cada evento a dict con valor deserializado
        return [evento_to_dict(ev) for ev in eventos]

# ─────────────────────────────────────────────
# NUEVO: obtener_eventos_filtrados
# ─────────────────────────────────────────────
def obtener_eventos_filtrados(id_atleta, rol_actual="admin", tipos=None, fecha_inicio=None, fecha_fin=None):
    """Obtiene eventos filtrados dinámicamente por rol, tipo y rango de fechas."""
    with SessionLocal() as session:
        query = session.query(CalendarioEvento).filter_by(id_atleta=id_atleta)

        # Filtro por rol
        if rol_actual == "entrenadora":
            query = query.filter(CalendarioEvento.tipo_evento.notin_(["PrivadoAtleta"]))
        elif rol_actual == "atleta":
            query = query.filter(CalendarioEvento.tipo_evento.notin_(["PrivadoStaff"]))

        # Filtro por tipo de evento
        if tipos:
            query = query.filter(CalendarioEvento.tipo_evento.in_(tipos))

        # Filtro por rango de fechas
        if fecha_inicio:
            query = query.filter(CalendarioEvento.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(CalendarioEvento.fecha <= fecha_fin)

        eventos = query.order_by(CalendarioEvento.fecha.desc()).all()
        return [evento_to_dict(ev) for ev in eventos]

def borrar_evento_calendario(id_evento: int) -> bool:
    """
    Elimina un evento de calendario por su id_evento único.
    Devuelve True si se eliminó, False si no existía.
    """
    with SessionLocal() as session:
        evento = session.query(CalendarioEvento).filter_by(id_evento=id_evento).first()
        if not evento:
            return False
        session.delete(evento)
        session.commit()
        _sync_backup()
        return True

def borrar_evento_calendario_por_fecha(id_atleta, fecha) -> bool:
    """
    Elimina un evento de calendario por atleta y fecha (normalizada a medianoche sin zona horaria).
    Devuelve True si se eliminó, False si no existía.
    """
    with SessionLocal() as session:
        # Normalizamos fecha a medianoche sin zona horaria (naive)
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        elif isinstance(fecha, date):
            fecha = fecha
        elif isinstance(fecha, str):
            try:
                base = datetime.fromisoformat(fecha.replace("Z", "+00:00"))
                fecha = base.date()
            except Exception:
                fecha = date.today()
        else:
            fecha = date.today()

        evento = session.query(CalendarioEvento).filter_by(
            id_atleta=id_atleta,
            fecha=fecha
        ).first()
        if not evento:
            return False

        session.delete(evento)
        session.commit()
        _sync_backup()
        return True

# ─────────────────────────────────────────────
# CRUD: SESIONES
# ─────────────────────────────────────────────
def crear_sesion(id_atleta, fecha, tipo_sesion, planificado_json=None, realizado_json=None):
    with SessionLocal() as session:
        sesion = Sesion(
            id_atleta=id_atleta,
            fecha=fecha,
            tipo_sesion=tipo_sesion,
            planificado_json=planificado_json,
            realizado_json=realizado_json
        )
        session.add(sesion)
        session.commit()
        session.refresh(sesion)
        _sync_backup()
        return sesion

def obtener_sesiones_por_atleta(id_atleta):
    with SessionLocal() as session:
        return session.query(Sesion).filter_by(id_atleta=id_atleta).order_by(Sesion.fecha.desc()).all()

def actualizar_sesion(id_sesion, **kwargs):
    with SessionLocal() as session:
        sesion = session.query(Sesion).filter_by(id_sesion=id_sesion).first()
        if not sesion:
            return None
        for campo, valor in kwargs.items():
            if hasattr(sesion, campo):
                setattr(sesion, campo, valor)
        session.commit()
        session.refresh(sesion)
        _sync_backup()
        return sesion

def borrar_sesion(id_sesion):
    with SessionLocal() as session:
        sesion = session.query(Sesion).filter_by(id_sesion=id_sesion).first()
        if sesion:
            session.delete(sesion)
            session.commit()
            _sync_backup()

# ─────────────────────────────────────────────
# CRUD: MÉTRICAS
# ─────────────────────────────────────────────
def crear_metrica(id_atleta, tipo_metrica, valor, unidad, fecha=None):
    """
    Inserta o actualiza una métrica rápida, garantizando que solo exista
    un registro por día y tipo para cada atleta.
    """
    fecha = fecha or datetime.now(timezone.utc).date()
    # 🔒 Normalizamos fecha para que siempre sea un objeto date
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    elif isinstance(fecha, str):
        # Ajusta el formato según cómo venga desde el calendario (ej. "2025-11-07")
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
    inicio = datetime.combine(fecha, datetime.min.time(), timezone.utc)
    fin = datetime.combine(fecha, datetime.max.time(), timezone.utc)

    with SessionLocal() as session:
        existente = session.query(Metrica).filter(
            Metrica.id_atleta == id_atleta,
            Metrica.tipo_metrica == tipo_metrica,
            Metrica.fecha >= inicio,
            Metrica.fecha <= fin
        ).first()

        if existente:
            # 🔑 Actualizamos en vez de duplicar
            existente.valor = str(valor)
            existente.unidad = unidad
            # Guardamos con la fecha del evento, no con "ahora"
            if isinstance(fecha, datetime):
                fecha = fecha.date()
            elif isinstance(fecha, str):
                fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
            existente.fecha = datetime.combine(fecha, datetime.min.time(), timezone.utc)
            session.commit()
            session.commit()
            session.refresh(existente)
            _sync_backup()
            return existente
        else:
            # Insertar nueva métrica
            if isinstance(fecha, datetime):
                fecha = fecha.date()
            elif isinstance(fecha, str):
                fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
            metrica = Metrica(
                id_atleta=id_atleta,
                fecha=datetime.combine(fecha, datetime.min.time(), timezone.utc),
                tipo_metrica=tipo_metrica,
                valor=str(valor),
                unidad=unidad
            )
            session.add(metrica)
            session.commit()
            session.refresh(metrica)
            _sync_backup()
            return metrica

def borrar_metricas_por_fecha(id_atleta, fecha):
    """
    Elimina todas las métricas rápidas de un atleta en una fecha concreta.
    Se usa al borrar un evento de calendario para que las gráficas se actualicen.
    """
    # 🔒 Normalizamos fecha a objeto date
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    elif isinstance(fecha, str):
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()

    inicio = datetime.combine(fecha, datetime.min.time(), timezone.utc)
    fin = datetime.combine(fecha, datetime.max.time(), timezone.utc)

    tipos = ["hrv", "wellness", "rpe", "peso", "fc_reposo", "deficit_calorico", "sueno"]

    with SessionLocal() as session:
        metricas = session.query(Metrica).filter(
            Metrica.id_atleta == id_atleta,
            Metrica.tipo_metrica.in_(tipos),
            Metrica.fecha >= inicio,
            Metrica.fecha <= fin
        ).all()
        for m in metricas:
            session.delete(m)

        session.commit()
        _sync_backup()
        return len(metricas)

def obtener_metricas_por_tipo(id_atleta, tipo_metrica):
    with SessionLocal() as session:
        return session.query(Metrica).filter_by(id_atleta=id_atleta, tipo_metrica=tipo_metrica).order_by(Metrica.fecha).all()

def actualizar_metrica(id_metrica, **kwargs):
    with SessionLocal() as session:
        metrica = session.query(Metrica).filter_by(id_metrica=id_metrica).first()
        if not metrica:
            return None
        for campo, valor in kwargs.items():
            if hasattr(metrica, campo):
                setattr(metrica, campo, valor)
        session.commit()
        session.refresh(metrica)
        _sync_backup()
        return metrica

def borrar_metrica(id_metrica):
    with SessionLocal() as session:
        metrica = session.query(Metrica).filter_by(id_metrica=id_metrica).first()
        if metrica:
            session.delete(metrica)
            session.commit()
            _sync_backup()

# ─────────────────────────────────────────────
# HELPERS: MÉTRICAS RÁPIDAS
# ─────────────────────────────────────────────
def obtener_metricas_rapidas(id_atleta):
    """
    Devuelve las métricas rápidas únicas por día (HRV, Wellness, RPE, Peso, FC reposo).
    Si hubo varias inserciones en el mismo día, se conserva solo la última.
    """
    tipos = ["hrv", "wellness", "rpe", "peso", "fc_reposo"]
    with SessionLocal() as session:
        metricas = session.query(Metrica)\
            .filter(Metrica.id_atleta == id_atleta, Metrica.tipo_metrica.in_(tipos))\
            .order_by(Metrica.fecha).all()

        # Agrupar por fecha y tipo, quedándose con la última
        unicas = {}
        for m in metricas:
            clave = (m.tipo_metrica, m.fecha.date())
            unicas[clave] = m

        return list(unicas.values())

# ─────────────────────────────────────────────
# HELPERS: VÍNCULO USUARIO ↔ ATLETA
# ─────────────────────────────────────────────
def obtener_id_atleta_por_usuario(usuario_id: int) -> int | None:
    with SessionLocal() as session:
        u = session.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
        return u.id_atleta if u and u.id_atleta else None

def obtener_usuario_por_atleta(id_atleta: int) -> int | None:
    with SessionLocal() as session:
        a = session.query(Atleta).filter(Atleta.id_atleta == id_atleta).first()
        return a.usuario_id if a and a.usuario_id else None

# ─────────────────────────────────────────────
# CRUD: COMENTARIOS
# ─────────────────────────────────────────────
def crear_comentario(id_atleta, texto, visible_para="staff", id_autor=None):
    with SessionLocal() as session:
        comentario = Comentario(
            id_atleta=id_atleta,
            id_autor=id_autor,
            texto=texto,
            visible_para=visible_para,
        )
        session.add(comentario)
        session.commit()
        session.refresh(comentario)
        _sync_backup()
        return comentario

def obtener_comentarios_por_atleta(id_atleta, rol_actual="admin"):
    with SessionLocal() as session:
        query = session.query(Comentario).filter_by(id_atleta=id_atleta)
        if rol_actual == "admin":
            return query.order_by(Comentario.fecha.desc()).all()
        elif rol_actual == "entrenadora":
            return query.filter(Comentario.visible_para.in_(["entrenadora", "staff", "todos"])).order_by(Comentario.fecha.desc()).all()
        elif rol_actual == "atleta":
            return query.filter(Comentario.visible_para.in_(["atleta", "todos"])).order_by(Comentario.fecha.desc()).all()
        else:
            return []

def actualizar_comentario(id_comentario, **kwargs):
    with SessionLocal() as session:
        comentario = session.query(Comentario).filter_by(id_comentario=id_comentario).first()
        if not comentario:
            return None
        for campo, valor in kwargs.items():
            if hasattr(comentario, campo):
                setattr(comentario, campo, valor)
        session.commit()
        session.refresh(comentario)
        _sync_backup()
        return comentario

def borrar_comentario(id_comentario):
    with SessionLocal() as session:
        comentario = session.query(Comentario).filter_by(id_comentario=id_comentario).first()
        if comentario:
            session.delete(comentario)
            session.commit()
            _sync_backup()

# ─────────────────────────────────────────────
# Inicialización del esquema si no había backups
# ─────────────────────────────────────────────
try:
    if 'NEED_INIT_SCHEMA' in globals() and NEED_INIT_SCHEMA:
        print("🛠️ Creando esquema inicial en base vacía...")
        Base.metadata.create_all(bind=engine)
        _sync_backup()  # subimos primer backup vacío
        print("✅ Esquema creado y primer backup generado")
except Exception as e:
    print(f"⚠️ Error al crear esquema inicial: {e}")

# Prueba
def reset_metricas_rapidas(id_atleta: int):
    """
    Borra todas las métricas rápidas y sus eventos de calendario para un atleta.
    Uso puntual de reset.
    """
    tipos = ["hrv", "wellness", "rpe", "peso", "fc_reposo"]
    with SessionLocal() as session:
        # 1. Borrar métricas rápidas del histórico
        session.query(Metrica).filter(
            Metrica.id_atleta == id_atleta,
            Metrica.tipo_metrica.in_(tipos)
        ).delete(synchronize_session=False)

        # 2. Borrar eventos de calendario de métricas rápidas
        session.query(CalendarioEvento).filter(
            CalendarioEvento.id_atleta == id_atleta,
            CalendarioEvento.tipo_evento == "metricas_rapidas"
        ).delete(synchronize_session=False)

        session.commit()
        _sync_backup()
# -----