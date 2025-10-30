from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

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

def actualizar_atleta(id_atleta, campo, valor):
    with SessionLocal() as session:
        atleta = session.query(Atleta).filter_by(id_atleta=id_atleta).first()
        if atleta:
            setattr(atleta, campo, valor)
            session.commit()
        return atleta

def borrar_atleta(id_atleta):
    with SessionLocal() as session:
        atleta = session.query(Atleta).filter_by(id_atleta=id_atleta).first()
        if atleta:
            session.delete(atleta)
            session.commit()