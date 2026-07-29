"""Capture UI screenshots for documentation (Chinese locale)."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "windib")  # Windows windowed

import pygame

from reinforcetactics.core.game_state import GameState
from reinforcetactics.ui.menus.game_setup.game_mode_menu import GameModeMenu
from reinforcetactics.ui.menus.game_setup.map_selection_menu import MapSelectionMenu
from reinforcetactics.ui.menus.main_menu import MainMenu
from reinforcetactics.ui.menus.save_load.replay_selection_menu import ReplaySelectionMenu
from reinforcetactics.ui.menus.settings.graphics_menu import GraphicsMenu
from reinforcetactics.ui.menus.settings.settings_menu import SettingsMenu
from reinforcetactics.ui.renderer import Renderer
from reinforcetactics.utils.file_io import FileIO
from reinforcetactics.utils.language import get_language
from reinforcetactics.utils.settings import get_settings

OUT = Path("agents/assets/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
SIZE = (900, 700)


def save(surface: pygame.Surface, name: str) -> Path:
    path = OUT / name
    pygame.image.save(surface, str(path))
    print(f"saved {path} ({path.stat().st_size} bytes)")
    return path


def pump():
    pygame.event.pump()


def main() -> None:
    # Chinese UI for doc screenshots
    lang = get_language()
    lang.set_language("chinese")
    get_settings()  # ensure settings.json side effects / defaults load

    pygame.init()
    # Hidden-ish window is fine; we blit then save surface
    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption("RT screenshot")
    pump()

    # 1) Main menu
    menu = MainMenu()
    # MainMenu creates its own screen — use that surface
    menu.draw()
    pump()
    save(menu.screen, "01-main-menu-zh.png")
    # keep a shared screen for submenus
    screen = menu.screen

    # 2) Settings
    sm = SettingsMenu(screen)
    sm.draw()
    pump()
    save(screen, "02-settings-zh.png")

    # 3) Graphics
    gm = GraphicsMenu(screen)
    gm.draw()
    pump()
    save(screen, "03-graphics-zh.png")

    # 4) Replay selection
    rm = ReplaySelectionMenu(screen)
    rm.draw()
    pump()
    save(screen, "04-replay-select-zh.png")

    # 5) Game mode
    mode = GameModeMenu(screen)
    mode.draw()
    pump()
    save(screen, "05-game-mode-zh.png")

    # 6) Map selection 1v1
    mm = MapSelectionMenu(screen, game_mode="1v1")
    mm.draw()
    pump()
    save(screen, "06-map-select-1v1-zh.png")

    # 7) In-game board (beginner) — headless render to surface
    map_data = FileIO.load_map("maps/1v1/beginner.csv")
    game = GameState(map_data, num_players=2)
    # create a couple units for a livelier shot
    game.create_unit("W", 1, 1, player=1)
    game.create_unit("A", 4, 4, player=2)
    renderer = Renderer(game, headless=True, pixel_art=True)
    # force a render
    if hasattr(renderer, "render"):
        renderer.render()
    surf = getattr(renderer, "screen", None) or getattr(renderer, "surface", None)
    if surf is None:
        # try common attrs
        for attr in ("display", "_screen", "window"):
            if hasattr(renderer, attr):
                surf = getattr(renderer, attr)
                break
    if surf is not None:
        save(surf, "07-game-board-beginner.png")
    else:
        print("WARN: could not get renderer surface; attrs=", [a for a in dir(renderer) if not a.startswith("__")])

    pygame.quit()
    print("done. files:", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
