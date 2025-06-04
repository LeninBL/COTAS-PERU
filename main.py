from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, func
from typing import List
from fastapi.responses import HTMLResponse
from fastapi import Query


# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de seguridad
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
DATABASE_URL = os.getenv("DATABASE_URL")


app = FastAPI()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de la base de datos
engine = create_engine(
    DATABASE_URL,
    pool_size=200,       # Aumenta el tamaño del pool
    max_overflow=20,    # Permite más conexiones adicionales
    pool_timeout=1800,    # Tiempo de espera antes de lanzar TimeoutError
    pool_recycle=1800   # Recicla conexiones cada 30 minutos para evitar problemas
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelo de usuario en la base de datos
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default='normal')  # Añadir este campo
    # Relación uno a uno con user_details
    user_details = relationship("UserDetailsDB", back_populates="user", uselist=False)

class ProductoDB(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(50))
    marca = Column(String(50))
    modelo = Column(String(50))
    ubicacion = Column(String(50), nullable=False)
    cantidad_total = Column(Integer, nullable=False, default=0)
    cantidad_nuevos = Column(Integer, nullable=False, default=0)
    cantidad_usados = Column(Integer, nullable=False, default=0)
    cantidad_danados = Column(Integer, nullable=False, default=0)
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())


# Crear todas las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear la clase para la tabla `user_details`
class UserDetailsDB(Base):
    __tablename__ = "user_details"
    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    dob = Column(String)
    location = Column(String)
    bio = Column(String)

    # Relacionado con el usuario (clave foránea)
    user = relationship("UserDB", back_populates="user_details")

    # Establecer la clave foránea explícita
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

# Relación en UserDB
UserDB.user_details = relationship("UserDetailsDB", uselist=False, back_populates="user")

class User(BaseModel):
    username: str
    hashed_password: str
    role: Optional[str] = 'normal'

class UserDetails(BaseModel):
    first_name: str
    last_name: str
    dob: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None

class UserUpdate(BaseModel):
    username: str  
    first_name: str
    last_name: str
    dob: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    current_password: str
    new_password: Optional[str] = None
    confirm_password: Optional[str] = None

class Producto(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    categoria: str | None = None
    marca: str | None = None
    modelo: str | None = None
    ubicacion: str
    cantidad_total: int
    cantidad_nuevos: int
    cantidad_usados: int
    cantidad_danados: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
            from_attributes = True 

class ProductoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    ubicacion: Optional[str] = None
    cantidad_total: Optional[int] = None
    cantidad_nuevos: Optional[int] = None
    cantidad_usados: Optional[int] = None
    cantidad_danados: Optional[int] = None


class ProductoCreate(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None = None
    categoria: str | None = None
    marca: str | None = None
    modelo: str | None = None
    ubicacion: str
    cantidad_total: int
    cantidad_nuevos: int
    cantidad_usados: int
    cantidad_danados: int


class Producto(Producto):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True



class MovimientoDB(Base):
    __tablename__ = "movimientos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, server_default=func.now())
    codigo_producto = Column(String(50), nullable=False)
    tipo = Column(String(10), nullable=False)  # 'entrada' o 'salida'
    cantidad = Column(Integer, nullable=False)
    estado = Column(String(10), nullable=False)  # 'nuevo', 'usado', 'dañado'
    responsable = Column(String(100), nullable=False)
    registrado_por = Column(String(100), nullable=False)
    observaciones = Column(Text)
    producto_id = Column(Integer, ForeignKey('productos.id'))

    producto = relationship("ProductoDB")

class MovimientoBase(BaseModel):
    codigo_producto: str
    tipo: str
    cantidad: int
    estado: str
    responsable: str
    observaciones: Optional[str] = None

class MovimientoCreate(MovimientoBase):
    pass

class Movimiento(MovimientoBase):
    id: int
    fecha: datetime
    registrado_por: str
    producto_id: int

    class Config:
        from_attributes = True











class Token(BaseModel):
    access_token: str
    token_type: str

# Función para verificar la contraseña
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Función para obtener un usuario desde la base de datos
def get_user(db, username: str):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user:
        return User(username=user.username, hashed_password=user.hashed_password)
    return None

# Función para obtener los detalles del usuario
def get_user_details(db, user_id: int):
    return db.query(UserDetailsDB).filter(UserDetailsDB.user_id == user_id).first()

# Función para autenticar al usuario
def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Función para crear el token de acceso
def create_access_token(data: dict):
    to_encode = data.copy()
    # Incluir timestamp de la última actividad
    to_encode['last_activity'] = datetime.now(timezone.utc).isoformat()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Verificar si la sesión está expirada por inactividad
def is_session_expired(last_activity: str, inactivity_limit_minutes: int = 30):
    last_activity_time = datetime.fromisoformat(last_activity)
    now = datetime.now(timezone.utc)
    inactivity_duration = now - last_activity_time
    return inactivity_duration > timedelta(minutes=inactivity_limit_minutes)

















# Ruta para login
@app.post("/token", response_model=Token)
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    response.set_cookie(
        key="access_token",
        value=access_token,  
        httponly=True,
        secure=True,  
        samesite="Lax"
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Ruta de inicio

# Rutas protegidas
@app.get("/users/me")
async def read_users_me(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse("/", status_code=302)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        last_activity = payload.get("last_activity")


        if not last_activity or is_session_expired(last_activity):
            response = RedirectResponse("/", status_code=302)
            response.delete_cookie(key="access_token")  
            

            expires_in=datetime.now(timezone.utc) + timedelta(seconds=3) 

            response.set_cookie(
                key="session_expired",
                value="true",
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=3, 
                expires=expires_in  
            )
            return response
        db = SessionLocal()
        user = db.query(UserDB).filter(UserDB.username == username).first()
        user_details = get_user_details(db, user.id)

        # Actualizar el timestamp de la última actividad
        payload['last_activity'] = datetime.now(timezone.utc).isoformat()
        new_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        response = templates.TemplateResponse("welcome.html", {"request": request, "username": f'{user_details.first_name} {user_details.last_name}',  "is_admin": user.role == 'admin' })
        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except JWTError:
        return RedirectResponse("/", status_code=302)

@app.get("/users/me/profile")
async def read_users_me_profile(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse("/", status_code=302)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        last_activity = payload.get("last_activity")


        if not last_activity or is_session_expired(last_activity):
            response = RedirectResponse("/", status_code=302)
            response.delete_cookie(key="access_token")  

            expires_in = datetime.now(timezone.utc) + timedelta(seconds=3)

            response.set_cookie(
                key="session_expired",
                value="true",
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=3,
                expires=expires_in
            )
            return response

 
        db = SessionLocal()
        user = db.query(UserDB).filter(UserDB.username == username).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")


        user_details = get_user_details(db, user.id)

        if not user_details:
            raise HTTPException(status_code=404, detail="User details not found")


        payload['last_activity'] = datetime.now(timezone.utc).isoformat()
        new_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


        response = templates.TemplateResponse(
            "profile.html", {
                "request": request,
                "username": f'{user_details.first_name} {user_details.last_name}',
                "userFullName": user_details.first_name,
                "userLastName": user_details.last_name,
                "userEmail": user.username, 
                "userDOB": user_details.dob,
                "userLocation": user_details.location,
                "userBio": user_details.bio,
                "is_admin": user.role == 'admin'
            }
        )

        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except JWTError:
        return RedirectResponse("/", status_code=302)
    
@app.put("/users/me/update_profile", response_model=UserDetails)
async def update_user_profile(
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    request: Request = None
):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user = db.query(UserDB).filter(UserDB.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        

        if not verify_password(user_update.current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect current password")
        
 
        if user_update.new_password:
            if user_update.new_password != user_update.confirm_password:
                raise HTTPException(status_code=400, detail="Passwords do not match")
            user.hashed_password = pwd_context.hash(user_update.new_password)
        

        user_details = get_user_details(db, user.id)
        if not user_details:
            raise HTTPException(status_code=404, detail="User details not found")
        
        user_details.first_name = user_update.first_name
        user_details.last_name = user_update.last_name
        user_details.dob = user_update.dob
        user_details.location = user_update.location
        user_details.bio = user_update.bio

        db.commit()
        

        payload['last_activity'] = datetime.now(timezone.utc).isoformat()
        new_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        

        response = {"message": "Perfil actualizado con éxito."}  
        return JSONResponse(content=response, status_code=200)  
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")












@app.get("/")
async def read_root(request: Request):
    session_expired = request.cookies.get("session_expired", "false") == "true"
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "session_expired": session_expired
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/index")
async def index(request: Request):
    session_expired = request.cookies.get("session_expired", "false") == "true"
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "session_expired": session_expired
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/about")
async def about(request: Request):
    session_expired = request.cookies.get("session_expired", "false") == "true"
    response = templates.TemplateResponse("about.html", {
        "request": request,
        "session_expired": session_expired
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/services")
async def services(request: Request):
    session_expired = request.cookies.get("session_expired", "false") == "true"
    response = templates.TemplateResponse("services.html", {
        "request": request,
        "session_expired": session_expired
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/support")
async def support(request: Request):
    session_expired = request.cookies.get("session_expired", "false") == "true"
    response = templates.TemplateResponse("support.html", {
        "request": request,
        "session_expired": session_expired
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/contact")
async def contact(request: Request):
    session_expired = request.cookies.get("session_expired", "false") == "true"
    response = templates.TemplateResponse("contact.html", {
        "request": request,
        "session_expired": session_expired
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/libro-reclamaciones")
async def contact(request: Request):
    session_expired = request.cookies.get("session_expired", "false") == "true"
    response = templates.TemplateResponse("libro-reclamaciones.html", {
        "request": request,
        "session_expired": session_expired
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/politica-privacidad")
async def contact(request: Request):
    session_expired = request.cookies.get("session_expired", "false") == "true"
    response = templates.TemplateResponse("politica-privacidad.html", {
        "request": request,
        "session_expired": session_expired
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/terminos-condiciones")
async def contact(request: Request):
    session_expired = request.cookies.get("session_expired", "false") == "true"
    response = templates.TemplateResponse("terminos-condiciones.html", {
        "request": request,
        "session_expired": session_expired
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response




























@app.get("/access")
async def access(request: Request):
    token = request.cookies.get("access_token")
    session_expired = request.cookies.get("session_expired", "false") == "true"

    if token:
        return RedirectResponse("/users/me")
    
    response = templates.TemplateResponse("access.html", {
        "request": request,
        "session_expired": session_expired
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


























@app.get("/users/me/check_admin")
def check_admin(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(UserDB).filter(UserDB.username == payload.get("sub")).first()
        
        if user.role != 'admin':
            raise HTTPException(status_code=403, detail="No autorizado")
            
        return {"message": "Autorizado"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

@app.get("/users/me/show")
async def read_users_me(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse("/", status_code=302)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        last_activity = payload.get("last_activity")


        if not last_activity or is_session_expired(last_activity):
            response = RedirectResponse("/", status_code=302)
            response.delete_cookie(key="access_token") 

            expires_in = datetime.now(timezone.utc) + timedelta(seconds=3)

            response.set_cookie(
                key="session_expired",
                value="true",
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=3,
                expires=expires_in
            )
            return response
        
        db = SessionLocal()
        user = db.query(UserDB).filter(UserDB.username == username).first()
        user_details = get_user_details(db, user.id)
        user_name=user_details.first_name
        user_last_name=user_details.last_name
        all_users = db.query(UserDB).all() 

        all_users_with_details = []
        for user in all_users:
            user_details = get_user_details(db, user.id)
            all_users_with_details.append({"user": user, "details": user_details})


        payload['last_activity'] = datetime.now(timezone.utc).isoformat()
        new_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


        response = templates.TemplateResponse("show.html", {
            "request": request, 
            "username": f'{user_name} {user_last_name}', 
            "all_users_with_details": all_users_with_details,
            "is_admin": user.role == 'admin'
            
        })

        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except JWTError:
        return RedirectResponse("/", status_code=302)

@app.get("/users/me/register_show")
async def read_users_me(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse("/", status_code=302)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        last_activity = payload.get("last_activity")

        if not last_activity or is_session_expired(last_activity):
            response = RedirectResponse("/", status_code=302)
            response.delete_cookie(key="access_token") 

            expires_in = datetime.now(timezone.utc) + timedelta(seconds=3)

            response.set_cookie(
                key="session_expired",
                value="true",
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=3,
                expires=expires_in
            )
            return response

        db = SessionLocal()
        user = db.query(UserDB).filter(UserDB.username == username).first()
        if user.role != 'admin':
            return RedirectResponse("/users/me/show", status_code=302)
        
        user_details = get_user_details(db, user.id)
        user_name=user_details.first_name
        user_last_name=user_details.last_name
        all_users = db.query(UserDB).all()  

        all_users_with_details = []
        for user in all_users:
            user_details = get_user_details(db, user.id)
            all_users_with_details.append({"user": user, "details": user_details})


        payload['last_activity'] = datetime.now(timezone.utc).isoformat()
        new_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


        response = templates.TemplateResponse("register_show.html", {
            "request": request, 
            "username": f'{user_name} {user_last_name}', 
            "all_users_with_details": all_users_with_details,
            "is_admin": user.role == 'admin'
        })

        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except JWTError:
        return RedirectResponse("/", status_code=302)

@app.post("/users/me/create")
def create_user(user: User, user_details: UserDetails, db: Session = Depends(get_db), request: Request = None):
    # Verificar si el usuario actual es admin
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user = db.query(UserDB).filter(UserDB.username == payload.get("sub")).first()
        
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Solo los administradores pueden crear usuarios")
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Resto de la lógica de creación de usuario...
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Usuario ya existe")

    hashed_password = pwd_context.hash(user.hashed_password)

    new_user = UserDB(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_user_details = UserDetailsDB(
        user_id=new_user.id,
        first_name=user_details.first_name,
        last_name=user_details.last_name,
        dob=user_details.dob,
        location=user_details.location,
        bio=user_details.bio
    )
    db.add(new_user_details)
    db.commit()
    db.refresh(new_user_details)

    return {"message": "Usuario creado exitosamente"}

@app.get("/users/me/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    user_details = db.query(UserDetailsDB).filter(UserDetailsDB.user_id == user_id).first()
    if user_details is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    return user_details

@app.put("/users/me/{user_id}")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")


    if not verify_password(user_update.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña incorrecta")


    if user_update.new_password:
        user.hashed_password = pwd_context.hash(user_update.new_password)

    user_details = db.query(UserDetailsDB).filter(UserDetailsDB.user_id == user_id).first()
    if user_details:
        user_details.first_name = user_update.first_name
        user_details.last_name = user_update.last_name
        user_details.dob = user_update.dob
        user_details.location = user_update.location
        user_details.bio = user_update.bio
        db.commit()
        db.refresh(user_details)

    db.commit()
    db.refresh(user)
    return {"message": "Usuario actualizado exitosamente"}

@app.delete("/users/me/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    db.query(UserDetailsDB).filter(UserDetailsDB.user_id == user_id).delete()
    db.query(UserDB).filter(UserDB.id == user_id).delete()
    db.commit()
    return {"message": "Usuario eliminado exitosamente"}



# Rutas para productos
@app.get("/productos-ui")
async def get_productos(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse("/", status_code=302)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        last_activity = payload.get("last_activity")

        if not last_activity or is_session_expired(last_activity):
            response = RedirectResponse("/", status_code=302)
            response.delete_cookie(key="access_token")

            expires_in = datetime.now(timezone.utc) + timedelta(seconds=3)
            response.set_cookie(
                key="session_expired",
                value="true",
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=3,
                expires=expires_in
            )
            return response

        db = SessionLocal()
        user = db.query(UserDB).filter(UserDB.username == username).first()
        user_details = get_user_details(db, user.id)
        user_name = user_details.first_name
        user_last_name = user_details.last_name

 
        productos = db.query(ProductoDB).all()

        # Actualizar la actividad en el token
        payload['last_activity'] = datetime.now(timezone.utc).isoformat()
        new_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        response = templates.TemplateResponse("products.html", {
            "request": request,
            "username": f'{user_name} {user_last_name}',
            "is_admin": user.role == 'admin',
            "productos": productos  
        })

        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except JWTError:
        return RedirectResponse("/", status_code=302)    

@app.get("/productos-carga", response_model=List[Producto])
async def listar_productos(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse("/", status_code=302)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        last_activity = payload.get("last_activity")

        if not last_activity or is_session_expired(last_activity):
            response = RedirectResponse("/", status_code=302)
            response.delete_cookie(key="access_token")

            expires_in = datetime.now(timezone.utc) + timedelta(seconds=3)
            response.set_cookie(
                key="session_expired",
                value="true",
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=3,
                expires=expires_in
            )
            return response

        user = db.query(UserDB).filter(UserDB.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        productos = db.query(ProductoDB).all()

        # Actualizar actividad y renovar token
        payload["last_activity"] = datetime.now(timezone.utc).isoformat()
        new_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        response = JSONResponse(content=[Producto.model_validate(p).model_dump(mode="json") for p in productos])
        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        return response

    except JWTError:
        return RedirectResponse("/", status_code=302)

@app.post("/productos")
async def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    # Validar ubicación
    ubicaciones_validas = ["ALMACÉN 1", "ALMACÉN 2", "SÓTANO"]
    if producto.ubicacion not in ubicaciones_validas:
        raise HTTPException(
            status_code=400,
            detail=f"Ubicación no válida. Las opciones son: {', '.join(ubicaciones_validas)}"
        )
    
    # Validar que el código no exista
    db_producto = db.query(ProductoDB).filter(ProductoDB.codigo == producto.codigo).first()
    if db_producto:
        raise HTTPException(status_code=400, detail="El código ya existe")
    
    # Validar que las cantidades sumen correctamente
    if producto.cantidad_total != (producto.cantidad_nuevos + producto.cantidad_usados + producto.cantidad_danados):
        raise HTTPException(status_code=400, detail="La suma de cantidades por estado no coincide con la cantidad total")
    
    nuevo_producto = ProductoDB(**producto.model_dump())
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

@app.get("/productos/{producto_id}")
async def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(ProductoDB).filter(ProductoDB.id == producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto




@app.get("/productos")
async def buscar_producto_por_codigo(codigo: str = Query(None), db: Session = Depends(get_db)):
    if codigo:
        producto = db.query(ProductoDB).filter(ProductoDB.codigo == codigo).first()
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return [producto]  # Devuelvo lista para mantener el mismo formato frontend
    else:
        productos = db.query(ProductoDB).all()
        return productos


@app.put("/productos/{producto_id}")
async def actualizar_producto(
    producto_id: int,
    producto: ProductoUpdate,
    db: Session = Depends(get_db)
):
    db_producto = db.query(ProductoDB).filter(ProductoDB.id == producto_id).first()
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    update_data = producto.dict(exclude_unset=True)

    # Validar ubicación si se proporciona
    ubicaciones_validas = ["ALMACÉN 1", "ALMACÉN 2", "SÓTANO"]
    if "ubicacion" in update_data and update_data["ubicacion"] not in ubicaciones_validas:
        raise HTTPException(
            status_code=400,
            detail=f"Ubicación no válida. Las opciones son: {', '.join(ubicaciones_validas)}"
        )

    # Validar código único si se proporciona y ha cambiado
    if "codigo" in update_data and update_data["codigo"] != db_producto.codigo:
        existing = db.query(ProductoDB).filter(ProductoDB.codigo == update_data["codigo"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="El código ya existe")

    # Validar cantidades si se proporciona cantidad_total y al menos uno de los otros
    cantidad_keys = {"cantidad_total", "cantidad_nuevos", "cantidad_usados", "cantidad_danados"}
    if cantidad_keys.intersection(update_data.keys()):
        cantidad_total = update_data.get("cantidad_total", db_producto.cantidad_total)
        cantidad_nuevos = update_data.get("cantidad_nuevos", db_producto.cantidad_nuevos)
        cantidad_usados = update_data.get("cantidad_usados", db_producto.cantidad_usados)
        cantidad_danados = update_data.get("cantidad_danados", db_producto.cantidad_danados)

        if cantidad_total != (cantidad_nuevos + cantidad_usados + cantidad_danados):
            raise HTTPException(status_code=400, detail="La suma de cantidades por estado no coincide con la cantidad total")

    # Aplicar la actualización
    for key, value in update_data.items():
        setattr(db_producto, key, value)
    
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto


@app.delete("/productos/{producto_id}")
async def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(ProductoDB).filter(ProductoDB.id == producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(producto)
    db.commit()
    return {"message": "Producto eliminado correctamente"}


# Ruta para obtener categorías dinámicas
@app.get("/categorias-dinamicas")
async def obtener_categorias_dinamicas(db: Session = Depends(get_db)):
    # Obtener todas las categorías distintas de los productos
    categorias = db.query(ProductoDB.categoria).distinct().all()
    # Filtrar y aplanar resultados
    return [c[0] for c in categorias if c[0]]  # Excluye valores None

# Ruta para obtener ubicaciones válidas
@app.get("/ubicaciones-validas")
async def obtener_ubicaciones_validas():
    # Devuelve las ubicaciones predefinidas
    return ["ALMACÉN 1", "ALMACÉN 2", "SÓTANO"]




@app.get("/entradas-ui")
async def get_entradas(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/", status_code=302)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        last_activity = payload.get("last_activity")

        if not last_activity or is_session_expired(last_activity):
            response = RedirectResponse("/", status_code=302)
            response.delete_cookie(key="access_token")
            expires_in = datetime.now(timezone.utc) + timedelta(seconds=3)
            response.set_cookie(
                key="session_expired",
                value="true",
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=3,
                expires=expires_in
            )
            return response

        db = SessionLocal()
        user = db.query(UserDB).filter(UserDB.username == username).first()
        user_details = get_user_details(db, user.id)
        user_name = user_details.first_name
        user_last_name = user_details.last_name

        # Obtener movimientos de entrada para pre-cargar el historial
        movimientos = db.query(MovimientoDB).filter(MovimientoDB.tipo == 'entrada').order_by(MovimientoDB.fecha.desc()).limit(50).all()

        # Renovar token
        payload["last_activity"] = datetime.now(timezone.utc).isoformat()
        new_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        response = templates.TemplateResponse("entradas.html", {
            "request": request,
            "username": f"{user_name} {user_last_name}",
            "is_admin": user.role == 'admin',
            "now": datetime.now(timezone.utc),
            "movimientos": movimientos
        })

        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except JWTError:
        return RedirectResponse("/", status_code=302)

@app.get("/salidas-ui")
async def get_salidas(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/", status_code=302)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        last_activity = payload.get("last_activity")

        if not last_activity or is_session_expired(last_activity):
            response = RedirectResponse("/", status_code=302)
            response.delete_cookie(key="access_token")
            expires_in = datetime.now(timezone.utc) + timedelta(seconds=3)
            response.set_cookie(
                key="session_expired",
                value="true",
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=3,
                expires=expires_in
            )
            return response

        db = SessionLocal()
        user = db.query(UserDB).filter(UserDB.username == username).first()
        user_details = get_user_details(db, user.id)
        user_name = user_details.first_name
        user_last_name = user_details.last_name

        # Obtener movimientos de salida para pre-cargar el historial
        movimientos = db.query(MovimientoDB).filter(MovimientoDB.tipo == 'salida').order_by(MovimientoDB.fecha.desc()).limit(50).all()

        payload["last_activity"] = datetime.now(timezone.utc).isoformat()
        new_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        response = templates.TemplateResponse("salidas.html", {
            "request": request,
            "username": f"{user_name} {user_last_name}",
            "is_admin": user.role == 'admin',
            "now": datetime.now(timezone.utc),
            "movimientos": movimientos
        })

        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except JWTError:
        return RedirectResponse("/", status_code=302)

@app.post("/movimientos")
async def crear_movimiento(movimiento: MovimientoCreate, request: Request, db: Session = Depends(get_db)):
    # Verificar autenticación
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Buscar producto
    producto = db.query(ProductoDB).filter(ProductoDB.codigo == movimiento.codigo_producto).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Validar cantidades si es salida
    if movimiento.tipo == 'salida':
        if movimiento.estado == 'nuevo' and producto.cantidad_nuevos < movimiento.cantidad:
            raise HTTPException(status_code=400, detail="No hay suficiente stock nuevo")
        if movimiento.estado == 'usado' and producto.cantidad_usados < movimiento.cantidad:
            raise HTTPException(status_code=400, detail="No hay suficiente stock usado")
        if movimiento.estado == 'dañado' and producto.cantidad_danados < movimiento.cantidad:
            raise HTTPException(status_code=400, detail="No hay suficiente stock dañado")

    # Actualizar stock del producto
    if movimiento.tipo == 'entrada':
        if movimiento.estado == 'nuevo':
            producto.cantidad_nuevos += movimiento.cantidad
        elif movimiento.estado == 'usado':
            producto.cantidad_usados += movimiento.cantidad
        elif movimiento.estado == 'dañado':
            producto.cantidad_danados += movimiento.cantidad
    else:  # salida
        if movimiento.estado == 'nuevo':
            producto.cantidad_nuevos -= movimiento.cantidad
        elif movimiento.estado == 'usado':
            producto.cantidad_usados -= movimiento.cantidad
        elif movimiento.estado == 'dañado':
            producto.cantidad_danados -= movimiento.cantidad

    producto.cantidad_total = producto.cantidad_nuevos + producto.cantidad_usados + producto.cantidad_danados

    # Crear movimiento
    db_movimiento = MovimientoDB(
        **movimiento.model_dump(),
        producto_id=producto.id,
        registrado_por=username
    )
    db.add(db_movimiento)
    db.commit()
    db.refresh(db_movimiento)
    
    return db_movimiento

@app.get("/movimientos")
async def listar_movimientos(
    request: Request,
    codigo: Optional[str] = None,
    tipo: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    responsable: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Verificar autenticación
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Convertir fechas
    fecha_inicio_dt = parse_fecha(fecha_inicio)
    fecha_fin_dt = parse_fecha(fecha_fin)

    query = db.query(MovimientoDB)

    if codigo:
        query = query.filter(MovimientoDB.codigo_producto.contains(codigo))
    if tipo:
        query = query.filter(MovimientoDB.tipo == tipo)
    if responsable:
        query = query.filter(MovimientoDB.responsable.contains(responsable))
    if fecha_inicio_dt:
        query = query.filter(MovimientoDB.fecha >= fecha_inicio_dt)
    if fecha_fin_dt:
        query = query.filter(MovimientoDB.fecha <= fecha_fin_dt)

    return query.order_by(MovimientoDB.fecha.desc()).all()

def parse_fecha(fecha_str: Optional[str]) -> Optional[datetime]:
    if fecha_str:
        try:
            return datetime.fromisoformat(fecha_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Fecha inválida: {fecha_str}")
    return None













# Ruta para logout
@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return RedirectResponse("/access", status_code=302, headers={
        "Set-Cookie": "access_token=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Lax"
        
    })

app.mount("/static", StaticFiles(directory="static"), name="static")