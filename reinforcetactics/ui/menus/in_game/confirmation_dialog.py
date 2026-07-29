"""Confirmation dialog for critical actions."""

import pygame

from reinforcetactics.ui import widgets
from reinforcetactics.ui.widgets.dialog import Dialog
from reinforcetactics.utils.language import get_language


class ConfirmationDialog(Dialog):
    """A modal confirmation dialog for critical actions like resign."""

    def __init__(
        self, screen: pygame.Surface, title: str, message: str, confirm_text: str = "Confirm", cancel_text: str = "Cancel"
    ) -> None:
        """
        Initialize confirmation dialog.

        Args:
            screen: Pygame surface to draw on
            title: Dialog title
            message: Message to display
            confirm_text: Text for confirm button
            cancel_text: Text for cancel button
        """
        lang = get_language()
        if confirm_text == "Confirm":
            confirm_text = lang.get("common.confirm", "Confirm")
        if cancel_text == "Cancel":
            cancel_text = lang.get("common.cancel", "Cancel")
        super().__init__(
            screen,
            title,
            message,
            buttons=[
                (cancel_text, False, widgets.CANCEL),
                (confirm_text, True, widgets.CONFIRM),
            ],
            hint=lang.get("dialog.confirm_hint", "Press Y to confirm, N or ESC to cancel"),
            keymap={pygame.K_RETURN: True, pygame.K_y: True, pygame.K_n: False},
            cancel_value=False,
            quit_value=False,
        )

    def run(self) -> bool:
        """
        Run the confirmation dialog loop.

        Returns:
            True if confirmed, False if cancelled
        """
        return bool(super().run())
