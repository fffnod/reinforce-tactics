"""Graphics settings menu for configuring sprite paths."""

import pygame

from reinforcetactics.ui import theme
from reinforcetactics.ui.menus.base import Menu
from reinforcetactics.ui.widgets import TextInput
from reinforcetactics.utils.fonts import get_font
from reinforcetactics.utils.language import get_language
from reinforcetactics.utils.settings import get_settings


class GraphicsMenu(Menu):
    """Graphics settings menu for sprite configuration."""

    def __init__(self, screen: pygame.Surface | None = None) -> None:
        """
        Initialize graphics menu.

        Args:
            screen: Optional pygame surface. If None, creates its own.
        """
        super().__init__(screen, get_language().get("graphics.title", "Graphics Settings"))
        self.settings = get_settings()
        self.editing_path: str | None = None  # Which path is being edited ('unit', 'tile', or 'animation')
        self.path_input = TextInput()
        self._setup_options()

    def _setup_options(self) -> None:
        """Setup menu options."""
        lang = get_language()

        # Get current settings
        disable_animations = self.settings.get("graphics.disable_animations", False)
        disable_unit_sprites = self.settings.get("graphics.disable_unit_sprites", False)
        use_tile_sprites = self.settings.get("graphics.use_tile_sprites", False)
        sprites_path = self.settings.get("graphics.sprites_path", "")
        animation_path = self.settings.get("graphics.animation_sprites_path", "")
        unit_path = self.settings.get("graphics.unit_sprites_path", "")
        tile_path = self.settings.get("graphics.tile_sprites_path", "")

        yes = lang.get("common.yes", "YES")
        no = lang.get("common.no", "NO")
        on = lang.get("common.enabled", "ON")
        off = lang.get("common.disabled", "OFF")
        not_set = lang.get("graphics.not_set", "(not set)")
        auto = lang.get("graphics.not_set_auto", "(auto)")

        # Base sprites root: auto-discovers units/ and tiles/ subfolders.
        # Not the same as animation_path (per-category override below).
        base_display = sprites_path if sprites_path else not_set
        self.add_option(
            f"{lang.get('graphics.sprites_path', 'Sprites Base Path')}: {base_display}",
            self._edit_sprites_path,
        )

        # Animation sprite-sheet override (falls back to base + units/)
        anim_path_display = animation_path if animation_path else auto
        self.add_option(
            f"{lang.get('graphics.animation_path', 'Animation Sheets Path')}: {anim_path_display}",
            self._edit_animation_path,
        )

        anim_status = yes if disable_animations else no
        self.add_option(
            f"{lang.get('graphics.disable_animations', 'Disable Animations')}: {anim_status}",
            self._toggle_animations,
        )

        # Static unit sprite override
        unit_path_display = unit_path if unit_path else auto
        self.add_option(
            f"{lang.get('graphics.unit_path', 'Static Sprites Path')}: {unit_path_display}",
            self._edit_unit_path,
        )

        static_status = yes if disable_unit_sprites else no
        self.add_option(
            f"{lang.get('graphics.disable_static_sprites', 'Disable Static Sprites')}: {static_status}",
            self._toggle_unit_sprites,
        )

        tile_status = on if use_tile_sprites else off
        self.add_option(
            f"{lang.get('graphics.use_tile_sprites', 'Use Tile Sprites')}: {tile_status}",
            self._toggle_tile_sprites,
        )

        tile_path_display = tile_path if tile_path else auto
        self.add_option(
            f"{lang.get('graphics.tile_path', 'Tile Sprites Path')}: {tile_path_display}",
            self._edit_tile_path,
        )

        self.add_option(lang.get("common.back", "Back"), lambda: None)

    def _refresh_options(self) -> None:
        """Refresh menu options after settings change."""
        self.clear_options()
        self._setup_options()

    def _toggle_unit_sprites(self) -> str:
        """Toggle disabling static unit sprites."""
        current = self.settings.get("graphics.disable_unit_sprites", False)
        self.settings.set("graphics.disable_unit_sprites", not current)
        self._refresh_options()
        return "toggled"

    def _toggle_tile_sprites(self) -> str:
        """Toggle tile sprites on/off."""
        current = self.settings.get("graphics.use_tile_sprites", False)
        self.settings.set("graphics.use_tile_sprites", not current)
        self._refresh_options()
        return "toggled"

    def _edit_unit_path(self) -> str:
        """Start editing unit sprites path."""
        self.editing_path = "unit"
        self.path_input.text = self.settings.get("graphics.unit_sprites_path", "")
        return "editing"

    def _edit_tile_path(self) -> str:
        """Start editing tile sprites path."""
        self.editing_path = "tile"
        self.path_input.text = self.settings.get("graphics.tile_sprites_path", "")
        return "editing"

    def _toggle_animations(self) -> str:
        """Toggle disabling animations."""
        current = self.settings.get("graphics.disable_animations", False)
        self.settings.set("graphics.disable_animations", not current)
        self._refresh_options()
        return "toggled"

    def _edit_sprites_path(self) -> str:
        """Start editing base sprites path."""
        self.editing_path = "base"
        self.path_input.text = self.settings.get("graphics.sprites_path", "")
        return "editing"

    def _edit_animation_path(self) -> str:
        """Start editing animation sprites path."""
        self.editing_path = "animation"
        self.path_input.text = self.settings.get("graphics.animation_sprites_path", "")
        return "editing"

    def _save_path(self) -> None:
        """Save the currently edited path."""
        if self.editing_path == "base":
            self.settings.set("graphics.sprites_path", self.path_input.text)
        elif self.editing_path == "unit":
            self.settings.set("graphics.unit_sprites_path", self.path_input.text)
        elif self.editing_path == "tile":
            self.settings.set("graphics.tile_sprites_path", self.path_input.text)
        elif self.editing_path == "animation":
            self.settings.set("graphics.animation_sprites_path", self.path_input.text)
        self.editing_path = None
        self.path_input.text = ""
        self._refresh_options()

    def _cancel_edit(self) -> None:
        """Cancel path editing."""
        self.editing_path = None
        self.path_input.text = ""

    def handle_input(self, event: pygame.event.Event) -> str | None:
        """Handle input events, including text input for path editing."""
        if self.editing_path:
            return self._handle_text_input(event)
        return super().handle_input(event)

    def _handle_text_input(self, event: pygame.event.Event) -> str | None:
        """Handle text input for path editing."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._save_path()
                return "saved"
            if event.key == pygame.K_ESCAPE:
                self._cancel_edit()
                return "cancelled"
            self.path_input.handle_key(event)
        return None

    def draw(self) -> None:
        """Draw the menu, with special handling for path editing mode."""
        if self.editing_path:
            self._draw_path_editor()
        else:
            super().draw()

    def _draw_path_editor(self) -> None:
        """Draw the path editing interface."""
        self.screen.fill(self.bg_color)

        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()

        lang = get_language()

        # Draw title
        if self.editing_path == "base":
            title = lang.get("graphics.edit_sprites_path", "Edit Sprites Base Path")
        elif self.editing_path == "unit":
            title = lang.get("graphics.edit_unit_path", "Edit Unit Sprites Path")
        elif self.editing_path == "animation":
            title = lang.get("graphics.edit_animation_path", "Edit Animation Sprites Path")
        else:
            title = lang.get("graphics.edit_tile_path", "Edit Tile Sprites Path")

        title_surface = self.title_font.render(title, True, self.title_color)
        title_rect = title_surface.get_rect(centerx=screen_width // 2, y=50)
        self.screen.blit(title_surface, title_rect)

        # Draw instructions
        instructions_font = get_font(theme.FONT_SIZE_BODY)
        instructions = [
            lang.get("graphics.path_hint", "Enter the path to your sprites folder"),
            lang.get("graphics.path_example", "Example: images/sprites/units"),
            "",
            lang.get("graphics.press_enter", "Press ENTER to save, ESC to cancel"),
            lang.get("graphics.paste_hint", "Ctrl+V to paste from clipboard"),
        ]

        y_offset = 120
        for instruction in instructions:
            inst_surface = instructions_font.render(instruction, True, theme.TEXT_INSTRUCTION)
            inst_rect = inst_surface.get_rect(centerx=screen_width // 2, y=y_offset)
            self.screen.blit(inst_surface, inst_rect)
            y_offset += 30

        # Draw input box
        input_box_width = min(600, screen_width - 100)
        input_box_height = 50
        input_box = pygame.Rect(
            (screen_width - input_box_width) // 2,
            screen_height // 2 - input_box_height // 2,
            input_box_width,
            input_box_height,
        )
        self.path_input.draw(self.screen, input_box, get_font(theme.FONT_SIZE_SUBHEADING))

        pygame.display.flip()

    def _on_result(self, result: str) -> tuple[bool, str | None]:
        """Absorb toggles and path-editing transitions; stay in the menu."""
        if result in ("toggled", "saved", "cancelled", "editing"):
            return False, None
        return True, result
