from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone, UTC
from sqlalchemy import JSON  # si usas SQLAlchemy 1.4+ puedes definir JSON
import json
import os
import shutil
import backup_storage

 # ─────────────────────────────────────────────
 # CONFIGURACIÓN BÁSICA
 # ─────────────────────────────────────────────

DB_PATH = os.path.join("/tmp", "base.db")

# Si no existe en /tmp, intentamos restaurar desde Drive o copiar semilla
if not os.path.exists(DB_PATH):
    try:
        backups = backup_storage.listar_backups()
        if backups:
            ultimo = sorted(backups, key=lambda b: b["createdTime"], reverse=True)[0]
            backup_storage.descargar_backup(ultimo["id"], DB_PATH)
            print(f"Restaurado backup inicial desde Drive: {ultimo['name']}")
        else:
            shutil.copy("base.db", DB_PATH)
            print("Copiado base.db inicial al /tmp")
    except Exception as e:
        print(f"⚠️ No se pudo restaurar backup inicial: {e}")

DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

# Helper para sincronizar backup tras cada commit
def _sync_backup():
    try:
        file_id = backup_storage.subir_backup(DB_PATH)
        backup_storage.rotar_backups(max_backups=5)
        print(f"Backup actualizado en Drive: {file_id}")
    except Exception as e:
        print(f"⚠️ Error al subir backup: {e}")

# ─────────────────────────────────────────────
# MODELOS
# ─────────────────────────────────────────────

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    rol = Column(String, nullable=False)  # admin, entrenadora, atleta
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    atletas = relationship("Atleta", back_populates="usuario")


class Atleta(Base):
    __tablename__ = "atletas"

    id_atleta = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

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

    usuario = relationship("Usuario", back_populates="atletas")

  # Relación con Evento
    eventos = relationship("Evento", back_populates="atleta", cascade="all, delete-orphan")

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

def crear_usuario(nombre, email, rol):
    with SessionLocal() as session:
        usuario = Usuario(nombre=nombre, email=email, rol=rol)
        session.add(usuario)
        session.flush()
        session.refresh(usuario)
        session.commit()
        _sync_backup()
        return usuario

def obtener_usuarios():
    with SessionLocal() as session:
        return session.query(Usuario).all()

def actualizar_usuario(id_usuario, **kwargs):
    with SessionLocal() as session:
        usuario = session.query(Usuario).filter_by(id_usuario=id_usuario).first()
        if not usuario:
            return None
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
        if usuario:
            session.delete(usuario)
            session.commit()
            _sync_backup()

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
        return session.query(Atleta).all()

def obtener_atleta_por_id(id_atleta):
    with SessionLocal() as session:
        return session.query(Atleta).filter_by(id_atleta=id_atleta).first()

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
    fecha = Column(DateTime(timezone=True), nullable=False)
    tipo_evento = Column(String, nullable=False)
    valor = Column(Text)  # guardamos JSON serializado
    notas = Column(Text)
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

class Comentario(Base):
    __tablename__ = "comentarios"

    id_comentario = Column(Integer, primary_key=True, autoincrement=True)
    id_atleta = Column(Integer, ForeignKey("atletas.id_atleta"), nullable=False)
    id_autor = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    texto = Column(Text, nullable=False)
    visible_para = Column(String, default="staff")
    fecha = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

# ─────────────────────────────────────────────
# CRUD: CALENDARIO
# ─────────────────────────────────────────────
def crear_evento_calendario(id_atleta, fecha, tipo_evento, valor, notas=None):
    with SessionLocal() as session:
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

def actualizar_evento_calendario(id_atleta, fecha, valores_actualizados, notas=None):
    """
    Actualiza un evento de calendario existente para un atleta en una fecha concreta.
    Si no existe, devuelve None.
    """
    with SessionLocal() as session:
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
            # Admin ve todo
            return query.order_by(CalendarioEvento.fecha.desc()).all()
        elif rol_actual == "entrenadora":
            # Entrenadora ve todo excepto eventos privados de atleta
            return query.filter(CalendarioEvento.tipo_evento.notin_(["PrivadoAtleta"])).order_by(CalendarioEvento.fecha.desc()).all()
        elif rol_actual == "atleta":
            # Atleta ve todo excepto eventos privados de staff
            return query.filter(CalendarioEvento.tipo_evento.notin_(["PrivadoStaff"])).order_by(CalendarioEvento.fecha.desc()).all()
        else:
            # Rol desconocido → no mostrar nada
            return []

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
def crear_metrica(id_atleta, tipo_metrica, valor, unidad):
    with SessionLocal() as session:
        metrica = Metrica(
            id_atleta=id_atleta,
            fecha=datetime.now(timezone.utc),
            tipo_metrica=tipo_metrica,
            valor=str(valor),
            unidad=unidad
        )
        session.add(metrica)
        session.commit()
        session.refresh(metrica)
        _sync_backup()
        return metrica

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

