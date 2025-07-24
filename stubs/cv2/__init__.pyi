"""
OpenCV (cv2) stub file for type checking
"""

import numpy as np
from typing import Any, Optional, Tuple

# Constants
COLOR_BGR2GRAY: int
INTER_CUBIC: int
THRESH_BINARY: int
THRESH_OTSU: int
MORPH_CLOSE: int
MORPH_OPEN: int

# Font constants
FONT_HERSHEY_SIMPLEX: int
FONT_HERSHEY_PLAIN: int
FONT_HERSHEY_DUPLEX: int
FONT_HERSHEY_COMPLEX: int
FONT_HERSHEY_TRIPLEX: int
FONT_HERSHEY_COMPLEX_SMALL: int
FONT_HERSHEY_SCRIPT_SIMPLEX: int
FONT_HERSHEY_SCRIPT_COMPLEX: int

def imread(filename: str, flags: int = ...) -> Optional[np.ndarray]: ...
def cvtColor(src: np.ndarray, code: int) -> np.ndarray: ...
def resize(src: np.ndarray, dsize: Optional[Tuple[int, int]], fx: float = ..., fy: float = ..., interpolation: int = ...) -> np.ndarray: ...
def GaussianBlur(src: np.ndarray, ksize: Tuple[int, int], sigmaX: float, sigmaY: float = ..., borderType: int = ...) -> np.ndarray: ...
def threshold(src: np.ndarray, thresh: float, maxval: float, type: int) -> Tuple[float, np.ndarray]: ...
def morphologyEx(src: np.ndarray, op: int, kernel: np.ndarray, anchor: Tuple[int, int] = ..., iterations: int = ..., borderType: int = ..., borderValue: Any = ...) -> np.ndarray: ...
def putText(img: np.ndarray, text: str, org: Tuple[int, int], fontFace: int, fontScale: float, color: Tuple[int, int, int], thickness: int = ..., lineType: int = ..., bottomLeftOrigin: bool = ...) -> None: ...
def getStructuringElement(shape: int, ksize: Tuple[int, int], anchor: Tuple[int, int] = ...) -> np.ndarray: ...

__version__: str
