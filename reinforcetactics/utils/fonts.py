"""Font utility for cross-platform Unicode support.

The game bundles its own fonts (in ``assets/fonts/``) so the UI looks the
same on every platform:

- **Noto Sans** (``get_font``) — body/UI text. Full Latin coverage,
  including the accented characters used by the French and Spanish
  translations.
- **Pixelify Sans** (``get_display_font``) — pixel-styled display font for
  titles and headings, matching the game's pixel-art style.

Neither bundled font covers CJK, so when the active language is Korean or
Chinese both helpers fall back to a system font with CJK coverage. The
system-font chain is also the fallback when the bundled files are missing
(e.g. a stripped-down install).

On some Windows + pygame-ce builds, ``pygame.font.get_fonts()`` /
``SysFont()`` crash while scanning the registry (non-string font paths).
CJK loading therefore prefers **direct font file paths** (e.g.
``C:\\Windows\\Fonts\\msyh.ttc``) before any SysFont lookup.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pygame

# Bundled fonts, relative to the assets/fonts directory.
BODY_FONT_FILE = "NotoSans-Regular.ttf"
DISPLAY_FONT_FILE = "PixelifySans-Regular.ttf"

# Languages whose glyphs the bundled fonts cannot render.
CJK_LANGUAGES = ("korean", "chinese")

# Priority list of system font *names* for SysFont (secondary path).
# Used only when direct file loading fails and SysFont works.
CJK_FONT_CANDIDATES = [
    # Windows Chinese / Korean
    "Microsoft YaHei",
    "Microsoft YaHei UI",
    "Malgun Gothic",
    "SimHei",
    "SimSun",
    "DengXian",
    # macOS
    "PingFang SC",
    "PingFang TC",
    "Apple SD Gothic Neo",
    "Hiragino Sans",
    "AppleGothic",
    # Cross-platform
    "Noto Sans CJK SC",
    "Noto Sans CJK KR",
    "Noto Sans CJK",
    "Arial Unicode MS",
    "DejaVu Sans",
]

# Direct font files (preferred on Windows when SysFont is broken).
# Order: Simplified Chinese → Traditional → Korean → generic.
_WINDOWS_CJK_FONT_FILES = (
    "msyh.ttc",  # Microsoft YaHei
    "msyhbd.ttc",  # Microsoft YaHei Bold (still has CJK glyphs)
    "msyh.ttf",
    "msjhl.ttc",  # Microsoft JhengHei Light
    "msjh.ttc",  # Microsoft JhengHei
    "simhei.ttf",
    "simsun.ttc",
    "simsunb.ttf",
    "Deng.ttf",
    "Dengb.ttf",
    "malgun.ttf",  # Malgun Gothic (Korean, also usable for some CJK)
    "malgunbd.ttf",
    "msgothic.ttc",
)

_LINUX_CJK_FONT_FILES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
)

_MAC_CJK_FONT_FILES = (
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
)

# Cache key is (kind, size) where kind is "body", "display", or "system".
_font_cache: dict[tuple[str, int], pygame.font.Font] = {}
_available_fonts_cache: list | None = None
_bundled_fonts_dir: Path | None = None
_bundled_fonts_dir_resolved = False
_quit_hook_registered = False
_cjk_file_path_cache: str | None | bool = False  # False=unset, None=none found, str=path


def clear_font_cache() -> None:
    """Clear all cached font objects.

    Call after language changes so CJK vs Latin font selection is re-evaluated.
    """
    global _available_fonts_cache, _cjk_file_path_cache
    _font_cache.clear()
    _available_fonts_cache = None
    _cjk_file_path_cache = False


def _clear_caches_on_quit() -> None:
    """Drop cached fonts when pygame quits.

    Font objects do not survive a ``pygame.quit()`` / ``pygame.init()``
    cycle — rendering with a stale font can crash the interpreter — so this
    is registered via ``pygame.register_quit`` whenever the cache is in use.
    """
    global _quit_hook_registered
    clear_font_cache()
    _quit_hook_registered = False


def _resolve_bundled_fonts_dir() -> Path | None:
    """Locate the bundled ``assets/fonts`` directory.

    Walks up from this file (the repo ships ``assets/fonts/`` at the root)
    and also checks the current working directory. Returns ``None`` if the
    directory can't be found. Result is cached.
    """
    global _bundled_fonts_dir, _bundled_fonts_dir_resolved
    if _bundled_fonts_dir_resolved:
        return _bundled_fonts_dir

    candidates = [Path.cwd() / "assets" / "fonts"]
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidates.append(parent / "assets" / "fonts")

    _bundled_fonts_dir = next((c for c in candidates if c.is_dir()), None)
    _bundled_fonts_dir_resolved = True
    return _bundled_fonts_dir


def _get_available_fonts() -> list:
    """Get list of available system fonts (cached).

    Returns:
        List of available font names in lowercase without spaces.
        Empty list if the pygame sysfont scanner is broken (seen on some
        Windows + pygame-ce builds).
    """
    global _available_fonts_cache
    if _available_fonts_cache is None:
        try:
            available_fonts = pygame.font.get_fonts()
            _available_fonts_cache = [f.lower().replace(" ", "") for f in available_fonts]
        except (pygame.error, OSError, TypeError, ValueError, AttributeError):
            # pygame-ce on Windows can raise TypeError when a registry font
            # path is not a string. Fall back to file-based CJK loading.
            _available_fonts_cache = []
    return _available_fonts_cache


def _needs_cjk_font() -> bool:
    """Whether the active language needs glyphs the bundled fonts lack."""
    # Imported lazily: language settings load at startup and this avoids any
    # import-order coupling between utils modules.
    from reinforcetactics.utils.language import get_language

    try:
        return get_language().get_current_language() in CJK_LANGUAGES
    except Exception:  # pylint: disable=broad-except
        return False


def _ensure_font_init() -> None:
    """Initialize pygame.font if needed, clearing stale caches."""
    global _available_fonts_cache, _quit_hook_registered
    if not pygame.font.get_init():
        pygame.font.init()
        # Clear caches after reinitialization to avoid stale fonts
        clear_font_cache()
    if not _quit_hook_registered:
        pygame.register_quit(_clear_caches_on_quit)
        _quit_hook_registered = True


def _get_cached(kind: str, size: int) -> pygame.font.Font | None:
    """Return a cached font if present and still valid."""
    font = _font_cache.get((kind, size))
    if font is None:
        return None
    try:
        font.get_height()
        return font
    except pygame.error:
        del _font_cache[(kind, size)]
        return None


def _load_bundled(kind: str, filename: str, size: int) -> pygame.font.Font | None:
    """Load a bundled font file, or return None if unavailable."""
    fonts_dir = _resolve_bundled_fonts_dir()
    if fonts_dir is None:
        return None
    path = fonts_dir / filename
    if not path.is_file():
        return None
    try:
        font = pygame.font.Font(str(path), size)
    except (pygame.error, OSError, FileNotFoundError):
        return None
    _font_cache[(kind, size)] = font
    return font


def _iter_cjk_font_file_candidates() -> list[Path]:
    """Return platform-specific font file paths that likely contain CJK glyphs."""
    paths: list[Path] = []

    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        fonts_dir = Path(windir) / "Fonts"
        for name in _WINDOWS_CJK_FONT_FILES:
            paths.append(fonts_dir / name)
    elif sys.platform == "darwin":
        paths.extend(Path(p) for p in _MAC_CJK_FONT_FILES)
    else:
        paths.extend(Path(p) for p in _LINUX_CJK_FONT_FILES)

    # Optional project-local override for air-gapped / minimal systems.
    bundled = _resolve_bundled_fonts_dir()
    if bundled is not None:
        for name in (
            "NotoSansCJKsc-Regular.otf",
            "NotoSansCJKsc-Regular.ttf",
            "NotoSansCJK-Regular.ttc",
            "NotoSansSC-Regular.otf",
        ):
            paths.append(bundled / name)

    return paths


def _resolve_cjk_font_file() -> str | None:
    """Find a usable CJK font file path (cached)."""
    global _cjk_file_path_cache
    if _cjk_file_path_cache is not False:
        return _cjk_file_path_cache if isinstance(_cjk_file_path_cache, str) else None

    for path in _iter_cjk_font_file_candidates():
        if not path.is_file():
            continue
        try:
            # Probe: can pygame open it and render a CJK character?
            probe = pygame.font.Font(str(path), 16)
            surface = probe.render("中", True, (255, 255, 255))
            if surface.get_width() > 0:
                _cjk_file_path_cache = str(path)
                return _cjk_file_path_cache
        except (pygame.error, OSError, FileNotFoundError, TypeError, ValueError):
            continue

    _cjk_file_path_cache = None
    return None


def _load_font_from_file(path: str, size: int) -> pygame.font.Font | None:
    """Load a font from an absolute path."""
    try:
        return pygame.font.Font(path, size)
    except (pygame.error, OSError, FileNotFoundError, TypeError, ValueError):
        return None


def _get_system_font(size: int) -> pygame.font.Font:
    """Get the best available system font with comprehensive Unicode support.

    Preference order:
    1. Direct CJK font file (robust on Windows when SysFont is broken)
    2. ``SysFont`` by candidate name
    3. pygame default font (may not render CJK)
    """
    cached = _get_cached("system", size)
    if cached is not None:
        return cached

    # 1) Direct file path — preferred
    cjk_path = _resolve_cjk_font_file()
    if cjk_path:
        font = _load_font_from_file(cjk_path, size)
        if font is not None:
            _font_cache[("system", size)] = font
            return font

    # 2) SysFont by name (works on many platforms; may fail on broken pygame-ce)
    try:
        available_fonts_lower = _get_available_fonts()
    except Exception:  # pylint: disable=broad-except
        available_fonts_lower = []

    for candidate in CJK_FONT_CANDIDATES:
        candidate_normalized = candidate.lower().replace(" ", "")
        # If we have a working font list, skip missing names; if the list is
        # empty (scanner broken), still try SysFont for each candidate.
        if available_fonts_lower and candidate_normalized not in available_fonts_lower:
            continue
        try:
            font = pygame.font.SysFont(candidate, size)
        except (pygame.error, OSError, TypeError, ValueError, AttributeError):
            continue
        # Reject fonts that cannot draw a basic CJK glyph (empty/tofu boxes
        # often still produce a surface — width check is a weak filter only).
        try:
            probe = font.render("中", True, (255, 255, 255))
            if probe.get_width() <= 0:
                continue
        except (pygame.error, OSError):
            continue
        _font_cache[("system", size)] = font
        return font

    # 3) Last resort
    font = pygame.font.Font(None, size)
    _font_cache[("system", size)] = font
    return font


def get_font(size: int) -> pygame.font.Font:
    """
    Get the game's body/UI font at the given size.

    Returns the bundled Noto Sans font so text looks identical on every
    platform. Falls back to a system font with comprehensive Unicode
    coverage when the active language is CJK (Korean/Chinese) or the
    bundled font file is missing.

    Args:
        size: Font size in points

    Returns:
        pygame.font.Font instance
    """
    _ensure_font_init()

    if _needs_cjk_font():
        return _get_system_font(size)

    cached = _get_cached("body", size)
    if cached is not None:
        return cached

    font = _load_bundled("body", BODY_FONT_FILE, size)
    if font is not None:
        return font
    return _get_system_font(size)


def get_display_font(size: int) -> pygame.font.Font:
    """
    Get the game's display font (titles/headings) at the given size.

    Returns the bundled Pixelify Sans font, a pixel-styled face matching
    the game's pixel-art look. Falls back to :func:`get_font` when the
    active language is CJK or the bundled font file is missing.

    Args:
        size: Font size in points

    Returns:
        pygame.font.Font instance
    """
    _ensure_font_init()

    if _needs_cjk_font():
        return _get_system_font(size)

    cached = _get_cached("display", size)
    if cached is not None:
        return cached

    font = _load_bundled("display", DISPLAY_FONT_FILE, size)
    if font is not None:
        return font
    return get_font(size)
