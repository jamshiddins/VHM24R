# Type stubs for python-docx
from typing import Any, List, Optional, Union, BinaryIO
from pathlib import Path

class Document:
    def __init__(self, docx: Optional[Union[str, Path, BinaryIO]] = ...) -> None: ...
    
    @property
    def paragraphs(self) -> List[Paragraph]: ...
    
    @property
    def tables(self) -> List[Table]: ...
    
    @property
    def sections(self) -> List[Section]: ...
    
    def add_paragraph(self, text: str = ..., style: Optional[str] = ...) -> Paragraph: ...
    def add_table(self, rows: int, cols: int, style: Optional[str] = ...) -> Table: ...
    def save(self, path_or_stream: Union[str, Path, BinaryIO]) -> None: ...

class Paragraph:
    @property
    def text(self) -> str: ...
    
    @text.setter
    def text(self, value: str) -> None: ...
    
    @property
    def runs(self) -> List[Run]: ...

class Run:
    @property
    def text(self) -> str: ...
    
    @text.setter
    def text(self, value: str) -> None: ...

class Table:
    @property
    def rows(self) -> List[Row]: ...
    
    @property
    def columns(self) -> List[Column]: ...

class Row:
    @property
    def cells(self) -> List[Cell]: ...

class Cell:
    @property
    def text(self) -> str: ...
    
    @text.setter
    def text(self, value: str) -> None: ...
    
    @property
    def paragraphs(self) -> List[Paragraph]: ...

class Column:
    pass

class Section:
    pass
