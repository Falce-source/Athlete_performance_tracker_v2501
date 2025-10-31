from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone
from sqlalchemy import JSON  # si usas SQLAlchemy 1.4+ puedes definir JSON
import json

# ─────────────────────────────────────────────
# CONFIGURACIÓN BÁSICA
# ─────────────────────────────────────────────

DATABASE_URL = "sqlite:///base.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)  # <- clave
Base = declarative_base()

# ─────────────────────────────────────────────
# MODELOS
# ─────────────────────────────────────────────

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    rol = Column(String, nullable=False)  # admin, entrenadora, atleta
    creado_en = Column(DateTime, default=datetime.utcnow)

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
    creado_en = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="atletas")

  # Relación con Evento
    eventos = relationship("Evento", back_populates="atleta", cascade="all, delete-orphan")

class Evento(Base):
    __tablename__ = "eventos"

    id_evento = Column(Integer, primary_key=True, autoincrement=True)
    id_atleta = Column(Integer, ForeignKey("atletas.id_atleta"), nullable=False)

    titulo = Column(String, nullable=False)          # Ej: "Entrenamiento fuerza"
    descripcion = Column(Text)                       # Detalles opcionales
    fecha = Column(DateTime, nullable=False)         # Cuándo ocurre
    lugar = Column(String)                           # Ej: "Gimnasio municipal"
    tipo = Column(String)                            # Ej: "Entrenamiento", "Competición", "Revisión médica"

    creado_en = Column(DateTime, default=datetime.utcnow)

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
        return usuario

def obtener_usuarios():
    with SessionLocal() as session:
        return session.query(Usuario).all()

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
        return atleta

def borrar_atleta(id_atleta):
    with SessionLocal() as session:
        atleta = session.query(Atleta).filter_by(id_atleta=id_atleta).first()
        if atleta:
            session.delete(atleta)
            session.commit()

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
        return evento

def obtener_eventos():
    with SessionLocal() as session:
        return session.query(Evento).all()

def obtener_eventos_por_atleta(id_atleta):
    with SessionLocal() as session:
        return session.query(Evento).filter_by(id_atleta=id_atleta).all()

def borrar_evento(id_evento):
    with SessionLocal() as session:
        evento = session.query(Evento).filter_by(id_evento=id_evento).first()
        if evento:
            session.delete(evento)
            session.commit()

# ─────────────────────────────────────────────
# MODELOS EXTRA: CALENDARIO, SESIONES, MÉTRICAS, COMENTARIOS
# ─────────────────────────────────────────────

class CalendarioEvento(Base):
    __tablename__ = "calendario_eventos"

    id_evento = Column(Integer, primary_key=True, autoincrement=True)
    id_atleta = Column(Integer, ForeignKey("atletas.id_atleta"), nullable=False)
    fecha = Column(DateTime, nullable=False)
    tipo_evento = Column(String, nullable=False)
    valor = Column(Text)  # guardamos JSON serializado
    notas = Column(Text)
    creado_en = Column(DateTime, default=datetime.utcnow)

class Sesion(Base):
    __tablename__ = "sesiones"

    id_sesion = Column(Integer, primary_key=True, autoincrement=True)
    id_atleta = Column(Integer, ForeignKey("atletas.id_atleta"), nullable=False)
    fecha = Column(DateTime, nullable=False)
    tipo_sesion = Column(String, nullable=False)
    planificado_json = Column(Text)
    realizado_json = Column(Text)

class Metrica(Base):
    __tablename__ = "metricas"

    id_metrica = Column(Integer, primary_key=True, autoincrement=True)
    id_atleta = Column(Integer, ForeignKey("atletas.id_atleta"), nullable=False)
    fecha = Column(DateTime, nullable=False)
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
    fecha = Column(DateTime, default=datetime.utcnow)

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
        return evento

def obtener_eventos_por_atleta(id_atleta):
    with SessionLocal() as session:
        return session.query(CalendarioEvento).filter_by(id_atleta=id_atleta).all()

# ─────────────────────────────────────────────
# CRUD: SESIONES
# ─────────────────────────────────────────────
def obtener_sesiones_por_atleta(id_atleta):
    with SessionLocal() as session:
        return session.query(Sesion).filter_by(id_atleta=id_atleta).order_by(Sesion.fecha.desc()).all()

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
        return metrica

def obtener_metricas_por_tipo(id_atleta, tipo_metrica):
    with SessionLocal() as session:
        return session.query(Metrica).filter_by(id_atleta=id_atleta, tipo_metrica=tipo_metrica).order_by(Metrica.fecha).all()

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
        return comentario

def obtener_comentarios_por_atleta(id_atleta):
    with SessionLocal() as session:
        return session.query(Comentario).filter_by(id_atleta=id_atleta).order_by(Comentario.fecha.desc()).all()
