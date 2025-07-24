# Type stubs for pytesseract
from typing import Any, Union, Optional, Dict, List, overload
from PIL.Image import Image
import numpy as np
import pandas as pd

# Main OCR functions
def image_to_string(
    image: Union[Image, np.ndarray, str],
    lang: Optional[str] = None,
    config: str = "",
    nice: int = 0,
    output_type: Any = None,
    timeout: int = 0
) -> str: ...

def image_to_data(
    image: Union[Image, np.ndarray, str],
    lang: Optional[str] = None,
    config: str = "",
    nice: int = 0,
    output_type: Any = None,
    timeout: int = 0
) -> Union[Dict[str, Any], pd.DataFrame, str, bytes]: ...

def image_to_boxes(
    image: Union[Image, np.ndarray, str],
    lang: Optional[str] = None,
    config: str = "",
    nice: int = 0,
    output_type: Any = None,
    timeout: int = 0
) -> str: ...

def image_to_osd(
    image: Union[Image, np.ndarray, str],
    lang: Optional[str] = None,
    config: str = "",
    nice: int = 0,
    output_type: Any = None,
    timeout: int = 0
) -> str: ...

def image_to_alto_xml(
    image: Union[Image, np.ndarray, str],
    lang: Optional[str] = None,
    config: str = "",
    nice: int = 0,
    timeout: int = 0
) -> str: ...

def image_to_hocr(
    image: Union[Image, np.ndarray, str],
    lang: Optional[str] = None,
    config: str = "",
    nice: int = 0,
    timeout: int = 0
) -> str: ...

def image_to_pdf_or_hocr(
    image: Union[Image, np.ndarray, str],
    lang: Optional[str] = None,
    config: str = "",
    nice: int = 0,
    extension: str = "pdf",
    timeout: int = 0
) -> bytes: ...

def run_and_get_output(
    image: Union[Image, np.ndarray, str],
    extension: str = "txt",
    lang: Optional[str] = None,
    config: str = "",
    nice: int = 0,
    timeout: int = 0,
    return_bytes: bool = False
) -> Union[str, bytes]: ...

# Utility functions
def get_languages(config: str = "") -> List[str]: ...
def get_tesseract_version() -> str: ...

# Output types
class Output:
    BYTES: int = 0
    DICT: int = 1
    STRING: int = 2
    DATAFRAME: int = 3

# Page Segmentation Mode constants
PSM_OEM_TESSERACT_ONLY: int = 0
PSM_OEM_LSTM_ONLY: int = 1
PSM_OEM_TESSERACT_LSTM_COMBINED: int = 2
PSM_OEM_DEFAULT: int = 3

PSM_ORIENTATION_AND_SCRIPT_DETECTION_ONLY: int = 0
PSM_AUTO_PAGE_SEGMENTATION_WITH_OSD: int = 1
PSM_AUTO_PAGE_SEGMENTATION_BUT_NO_OSD: int = 2
PSM_FULLY_AUTO_PAGE_SEGMENTATION_BUT_NO_OSD: int = 3
PSM_ASSUME_SINGLE_COLUMN_OF_TEXT_OF_VARIABLE_SIZES: int = 4
PSM_ASSUME_SINGLE_UNIFORM_BLOCK_OF_VERTICALLY_ALIGNED_TEXT: int = 5
PSM_ASSUME_SINGLE_UNIFORM_BLOCK_OF_TEXT: int = 6
PSM_TREAT_IMAGE_AS_SINGLE_TEXT_LINE: int = 7
PSM_TREAT_IMAGE_AS_SINGLE_WORD: int = 8
PSM_TREAT_IMAGE_AS_SINGLE_WORD_IN_CIRCLE: int = 9
PSM_TREAT_IMAGE_AS_SINGLE_CHARACTER: int = 10
PSM_SPARSE_TEXT: int = 11
PSM_SPARSE_TEXT_OSD: int = 12
PSM_RAW_LINE: int = 13

# Legacy constants for backward compatibility
PSM_OEM_AUTO: int = PSM_OEM_DEFAULT
PSM_SINGLE_BLOCK: int = PSM_ASSUME_SINGLE_UNIFORM_BLOCK_OF_TEXT
PSM_SINGLE_COLUMN: int = PSM_ASSUME_SINGLE_COLUMN_OF_TEXT_OF_VARIABLE_SIZES
PSM_SINGLE_BLOCK_VERT_TEXT: int = PSM_ASSUME_SINGLE_UNIFORM_BLOCK_OF_VERTICALLY_ALIGNED_TEXT
PSM_SINGLE_LINE: int = PSM_TREAT_IMAGE_AS_SINGLE_TEXT_LINE
PSM_SINGLE_WORD: int = PSM_TREAT_IMAGE_AS_SINGLE_WORD
PSM_SINGLE_CHAR: int = PSM_TREAT_IMAGE_AS_SINGLE_CHARACTER

# Exceptions
class TesseractError(Exception): ...
class TesseractNotFoundError(TesseractError): ...

# Module level attributes
__version__: str
