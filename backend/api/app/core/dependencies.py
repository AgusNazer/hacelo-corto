from typing import Annotated, Union
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload

# Para login tradicional con username/password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Para tokens JWT de Google OAuth (aparece en Swagger como segundo botón Authorize)
http_bearer_scheme = HTTPBearer(auto_error=False)


async def get_token_from_request(
    oauth2_token: Annotated[str, Depends(oauth2_scheme)] = None,
    bearer_token: Annotated[Union[HTTPAuthorizationCredentials, None], Depends(http_bearer_scheme)] = None,
) -> str:
    """
    Obtiene el token JWT de cualquiera de los dos esquemas de autenticación:
    - OAuth2PasswordBearer (login tradicional)
    - HTTPBearer (Google OAuth JWT)
    
    Esto permite que Swagger UI funcione con ambos métodos.
    """
    # Prioridad 1: HTTPBearer (Google OAuth)
    if bearer_token and bearer_token.credentials:
        return bearer_token.credentials
    
    # Prioridad 2: OAuth2PasswordBearer (login tradicional)
    if oauth2_token:
        return oauth2_token
    
    # Si ninguno está presente, lanzar error
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: Annotated[str, Depends(get_token_from_request)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = None

    # Intentar buscar por UUID (caso normal: sub = user.id)
    try:
        subject_as_uuid = UUID(token_data.sub)
        user = db.query(User).filter(User.id == subject_as_uuid).first()
    except (ValueError, TypeError):
        user = db.query(User).filter(User.email == token_data.sub).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
