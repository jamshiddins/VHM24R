"""Type stubs for psycopg2"""

from typing import Any, Optional, Union, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .extensions import connection, cursor
else:
    connection = Any
    cursor = Any

__version__: str

def connect(
    dsn: Optional[str] = ...,
    connection_factory: Optional[Type[connection]] = ...,
    cursor_factory: Optional[Type[cursor]] = ...,
    host: Optional[str] = ...,
    port: Optional[Union[str, int]] = ...,
    database: Optional[str] = ...,
    user: Optional[str] = ...,
    password: Optional[str] = ...,
    **kwargs: Any
) -> connection: ...

# Submodules are available for import
from . import extras as extras
from . import extensions as extensions

class Error(Exception): ...
class Warning(Exception): ...
class InterfaceError(Error): ...
class DatabaseError(Error): ...
class DataError(DatabaseError): ...
class OperationalError(DatabaseError): ...
class IntegrityError(DatabaseError): ...
class InternalError(DatabaseError): ...
class ProgrammingError(DatabaseError): ...
class NotSupportedError(DatabaseError): ...
