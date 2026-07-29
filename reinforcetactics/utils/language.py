"""
Language and translation system
"""

TRANSLATIONS = {
    "english": {
        # Main Menu
        "main_title": "REINFORCE TACTICS",
        "main_subtitle": "Turn-Based Strategy with RL",
        "menu_1v1_human": "1v1 (Human vs Human)",
        "menu_1v1_computer": "1v1 (Human vs Computer)",
        "menu_replay": "Watch Replay",
        "menu_load": "Load Game",
        "menu_settings": "Settings",
        "menu_exit": "Exit",
        "press_esc": "Press ESC to exit",
        # Main Menu (alternative keys used in menus.py)
        "main_menu.title": "Reinforce Tactics",
        "main_menu.new_game": "New Game",
        "main_menu.load_game": "Load Game",
        "main_menu.watch_replay": "Watch Replay",
        "main_menu.credits": "Credits",
        "main_menu.settings": "Settings",
        "main_menu.quit": "Quit",
        "main_menu.menu_hint": "Arrows: Move   Enter: Select   Esc: Quit",
        "main_menu.quit_confirm_title": "Quit Reinforce Tactics",
        "main_menu.quit_confirm_msg": "Close the game?",
        # Settings Menu
        "settings_title": "SETTINGS",
        "settings_language": "Language",
        "settings_paths": "File Paths",
        "settings_video": "Video Settings",
        "settings_maps_path": "Maps Directory",
        "settings_videos_path": "Videos Directory",
        "settings_replays_path": "Replays Directory",
        "settings_saves_path": "Saves Directory",
        "settings_reset": "Reset to Defaults",
        "settings_back": "Back",
        "settings_save": "Save",
        "settings_saved": "Settings saved!",
        "settings_reset_confirm": "Reset all settings to defaults?",
        # Settings Menu (alternative keys)
        "settings.title": "Settings",
        "settings.language": "Language",
        "settings.sound": "Sound",
        "settings.fullscreen": "Fullscreen",
        # Map Selection
        "map_select_title": "Select Map",
        "map_select": "Select",
        "map_random": "Random Map",
        "map_back": "Back",
        # New Game Menu
        "new_game.title": "Select Map",
        "new_game.select_mode": "Select Game Mode",
        # Player Configuration Menu
        "player_config.title": "Configure Players",
        "player_config.player": "Player {number}",
        "player_config.type_human": "Human",
        "player_config.type_computer": "Computer",
        "player_config.difficulty": "Difficulty",
        "player_config.difficulty_simple": "SimpleBot",
        "player_config.difficulty_normal": "NormalBot (Coming Soon)",
        "player_config.difficulty_hard": "HardBot (Coming Soon)",
        "player_config.start_game": "Start Game",
        # Save/Load Game
        "save_game.title": "Save Game",
        "save_game.enter_name": "Enter save name:",
        "save_game.instructions": "Press ENTER to save, ESC to cancel",
        "load_game.title": "Load Game",
        "load_game.status_in_progress": "In Progress",
        "load_game.status_completed": "Completed",
        "load_game.winner_label": "Winner: Player {player}",
        "load_game.completed_title": "Completed Game",
        "load_game.completed_confirm": "This game is already over. Load anyway?",
        # Quit Confirmation
        "quit_confirm.title": "Quit Game",
        "quit_confirm.message": "Save before quitting?",
        "quit_confirm.save_quit": "Save & Quit",
        "quit_confirm.quit": "Quit",
        "quit_confirm.cancel": "Cancel",
        # Language Menu
        "language.title": "Select Language",
        # Pause Menu
        "pause.title": "Paused",
        "pause.resume": "Resume",
        "pause.save": "Save Game",
        "pause.load": "Load Game",
        "pause.settings": "Settings",
        "pause.main_menu": "Main Menu",
        "pause.quit": "Quit",
        # Game Over
        "game_over.title": "Game Over",
        "game_over.winner": "Player {player} Wins!",
        "game_over.save_replay": "Save Replay",
        "game_over.new_game": "New Game",
        "game_over.main_menu": "Main Menu",
        "game_over.quit": "Quit",
        # Common
        "common.menu_hint": "Arrows: Move   Enter: Select   Esc: Back",
        "common.back": "Back",
        "common.confirm": "Confirm",
        "common.cancel": "Cancel",
        # Credits
        "credits.title": "Credits",
        "credits.game_title": "REINFORCE TACTICS",
        "credits.developer": "Developer:",
        "credits.developer_name": "Michael Kudlaty",
        "credits.description": "Turn-Based Strategy Game with Reinforcement Learning",
        # Game
        "player": "Player",
        "gold": "Gold",
        "turn": "Turn",
        "end_turn": "End Turn",
        "resign": "Resign",
        "game_over": "Game Over!",
        "winner": "wins!",
        "controls_title": "Controls",
        "controls_select": "Click units to select",
        "controls_move": "Click tiles to move",
        "controls_end_turn": "Press SPACE to end turn",
        "controls_quit": "Press ESC to quit",
        # Units
        "warrior": "Warrior",
        "mage": "Mage",
        "cleric": "Cleric",
        "barbarian": "Barbarian",
        "health": "Health",
        "attack": "Attack",
        "movement": "Movement",
        "cost": "Cost",
        "status": "Status",
        "abilities": "Abilities",
        # Messages
        "loading": "Loading...",
        "saving": "Saving...",
        "not_implemented": "Not yet implemented",
        "error": "Error",
        "success": "Success",
        "confirm": "Confirm",
        "cancel": "Cancel",
        # Map Editor
        "map_editor.title": "Map Editor",
        "map_editor.new_map": "New Map",
        "map_editor.edit_map": "Edit Existing Map",
        "map_editor.save": "Save Map",
        "map_editor.load": "Load Map",
        "map_editor.new_map_dialog.title": "Create New Map",
        "map_editor.new_map_dialog.width": "Width:",
        "map_editor.new_map_dialog.height": "Height:",
        "map_editor.new_map_dialog.players": "Players:",
        "map_editor.new_map_dialog.create": "Create",
        "map_editor.new_map_dialog.min_size": "Minimum size: {size}x{size}",
        "map_editor.tile_palette.title": "Tile Palette",
        "map_editor.tile_palette.terrain": "Terrain",
        "map_editor.tile_palette.structures": "Structures",
        "map_editor.tile_palette.neutral": "Neutral",
        "map_editor.tile_palette.player": "Player {number}",
        "map_editor.canvas.grid": "Grid: On",
        "map_editor.canvas.grid_off": "Grid: Off",
        "map_editor.canvas.coordinates": "X: {x}, Y: {y}",
        "map_editor.tools.paint": "Paint",
        "map_editor.tools.erase": "Erase",
        "map_editor.tools.fill": "Fill",
        "map_editor.save_dialog.title": "Save Map",
        "map_editor.save_dialog.filename": "Filename:",
        "map_editor.save_dialog.overwrite": "File exists. Overwrite?",
        "map_editor.validation.no_hq": "Each player must have exactly one Headquarters",
        "map_editor.validation.min_size": "Map must be at least {size}x{size}",
        "map_editor.validation.invalid_hq": "Player {player} needs exactly one Headquarters",
        "map_editor.shortcuts.title": "Keyboard Shortcuts",
        "map_editor.shortcuts.save": "Ctrl+S: Save",
        "map_editor.shortcuts.new": "Ctrl+N: New Map",
        "map_editor.shortcuts.open": "Ctrl+O: Open Map",
        "map_editor.shortcuts.grid": "G: Toggle Grid",
        "map_editor.shortcuts.esc": "Esc: Exit",
        # Settings extras
        "settings.graphics": "Graphics",
        "settings.units": "Unit Settings",
        "settings.api_keys": "LLM API Keys",
        "settings.sound_nyi": "Sound (not implemented)",
        # Graphics menu
        "graphics.title": "Graphics Settings",
        "graphics.not_set": "(not set)",
        "graphics.not_set_auto": "(auto)",
        "graphics.animation_path": "Animation Sheets Path",
        "graphics.unit_path": "Static Sprites Path",
        "graphics.tile_path": "Tile Sprites Path",
        "graphics.edit_unit_path": "Edit Unit Sprites Path",
        "graphics.edit_animation_path": "Edit Animation Sprites Path",
        "graphics.edit_tile_path": "Edit Tile Sprites Path",
        "graphics.path_hint": "Enter the path to your sprites folder",
        "graphics.path_example": "Example: images/sprites/units",
        "graphics.press_enter": "Press ENTER to save, ESC to cancel",
        "graphics.paste_hint": "Ctrl+V to paste from clipboard",
        # Units settings
        "units.title": "Unit Settings",
        "units.enable_all": "Enable All Units",
        "units.disable_all": "Disable All Units",
        "units.basic_only": "Basic Units Only (W,M,C,A)",
        "units.advanced_only": "Advanced Units Only (K,R,S,B)",
        # API keys
        "api_keys.title": "LLM API Keys Configuration",
        "api_keys.instructions": "Enter your API keys for LLM providers (leave blank to use environment variables)",
        # Player config extras
        "player_config.fog_of_war": "Fog of War",
        "player_config.game_options": "Game Options",
        "player_config.bot_simple": "Simple Bot",
        "player_config.bot_medium": "Medium Bot",
        "player_config.bot_advanced": "Advanced Bot",
        "player_config.bot_openai": "OpenAI (GPT)",
        "player_config.bot_claude": "Claude",
        "player_config.bot_gemini": "Gemini",
        "player_config.bot_model": "Custom Model",
        "player_config.no_api_key": "(No API Key)",
        "player_config.browse": "Browse...",
        # In-game unit action menu
        "unit_action.title": "Unit Actions",
        "unit_action.attack": "Attack (A)",
        "unit_action.paralyze": "Paralyze (P)",
        "unit_action.heal": "Heal (H)",
        "unit_action.cure": "Cure (C)",
        "unit_action.haste": "Haste (T)",
        "unit_action.defence_buff": "Defence Buff (D)",
        "unit_action.attack_buff": "Attack Buff (B)",
        "unit_action.capture": "Capture (S)",
        "unit_action.cancel_move": "Cancel Move (M)",
        "unit_action.wait": "Wait / End (W)",
        # Unit purchase
        "unit_purchase.title": "Purchase Unit",
        "unit_purchase.cost_suffix": "g",
        # Extra unit names
        "archer": "Archer",
        "knight": "Knight",
        "rogue": "Rogue",
        "sorcerer": "Sorcerer",
        # Tooltips / HUD status
        "tooltip.can_move": "Can Move",
        "tooltip.can_act": "Can Act",
        "tooltip.paralyzed": "Paralyzed ({turns})",
        "tooltip.hp": "HP: {current}/{max}",
        "tooltip.atk_def": "ATK: {atk}  DEF: {defence}",
        "tooltip.mov": "MOV: {mov}",
        "tooltip.player_unit": "{name} (P{player})",
        # Misc menus
        "game_over.turns": "Turns: {turns}",
        "pause.main_menu_confirm_title": "Return to Main Menu",
        "pause.main_menu_confirm_msg": "Unsaved progress will be lost. Continue?",
        "load_game.no_saves": "No saved games found",
        "replay.title": "Select Replay",
        "replay.no_replays": "No replays found",
        "common.disabled": "OFF",
        "common.enabled": "ON",
        "common.save": "Save",
        "dialog.confirm_hint": "Press Y to confirm, N or ESC to cancel",
        "new_game.random_map": "Random Map",
    },
    "french": {
        # Main Menu
        "main_title": "REINFORCE TACTICS",
        "main_subtitle": "Stratégie au tour par tour avec IA",
        "menu_1v1_human": "1v1 (Humain vs Humain)",
        "menu_1v1_computer": "1v1 (Humain vs Ordinateur)",
        "menu_replay": "Regarder Replay",
        "menu_load": "Charger Partie",
        "menu_settings": "Paramètres",
        "menu_exit": "Quitter",
        "press_esc": "Appuyez sur ESC pour quitter",
        # Main Menu (alternative keys)
        "main_menu.title": "Reinforce Tactics",
        "main_menu.new_game": "Nouvelle Partie",
        "main_menu.load_game": "Charger Partie",
        "main_menu.watch_replay": "Regarder Replay",
        "main_menu.credits": "Crédits",
        "main_menu.settings": "Paramètres",
        "main_menu.quit": "Quitter",
        "main_menu.menu_hint": "Flèches : Naviguer   Entrée : Sélectionner   Échap : Quitter",
        "main_menu.quit_confirm_title": "Quitter Reinforce Tactics",
        "main_menu.quit_confirm_msg": "Fermer le jeu ?",
        # Settings Menu
        "settings_title": "PARAMÈTRES",
        "settings_language": "Langue",
        "settings_paths": "Chemins des Fichiers",
        "settings_video": "Paramètres Vidéo",
        "settings_maps_path": "Répertoire des Cartes",
        "settings_videos_path": "Répertoire des Vidéos",
        "settings_replays_path": "Répertoire des Replays",
        "settings_saves_path": "Répertoire des Sauvegardes",
        "settings_reset": "Réinitialiser",
        "settings_back": "Retour",
        "settings_save": "Enregistrer",
        "settings_saved": "Paramètres enregistrés!",
        "settings_reset_confirm": "Réinitialiser tous les paramètres?",
        # Settings Menu (alternative keys)
        "settings.title": "Paramètres",
        "settings.language": "Langue",
        "settings.sound": "Son",
        "settings.fullscreen": "Plein Écran",
        # Map Selection
        "map_select_title": "Sélectionner la Carte",
        "map_select": "Sélectionner",
        "map_random": "Carte Aléatoire",
        "map_back": "Retour",
        # New Game Menu
        "new_game.title": "Sélectionner la Carte",
        "new_game.select_mode": "Choisir le Mode de Jeu",
        # Player Configuration Menu
        "player_config.title": "Configurer les Joueurs",
        "player_config.player": "Joueur {number}",
        "player_config.type_human": "Humain",
        "player_config.type_computer": "Ordinateur",
        "player_config.difficulty": "Difficulté",
        "player_config.difficulty_simple": "SimpleBot",
        "player_config.difficulty_normal": "NormalBot (Bientôt)",
        "player_config.difficulty_hard": "HardBot (Bientôt)",
        "player_config.start_game": "Commencer",
        # Save/Load Game
        "save_game.title": "Sauvegarder",
        "save_game.enter_name": "Nom de la sauvegarde:",
        "save_game.instructions": "Appuyez sur ENTRÉE pour sauvegarder, ESC pour annuler",
        "load_game.title": "Charger Partie",
        "load_game.status_in_progress": "En Cours",
        "load_game.status_completed": "Terminée",
        "load_game.winner_label": "Gagnant: Joueur {player}",
        "load_game.completed_title": "Partie Terminée",
        "load_game.completed_confirm": "Cette partie est déjà terminée. Charger quand même?",
        # Quit Confirmation
        "quit_confirm.title": "Quitter",
        "quit_confirm.message": "Sauvegarder avant de quitter?",
        "quit_confirm.save_quit": "Sauver & Quitter",
        "quit_confirm.quit": "Quitter",
        "quit_confirm.cancel": "Annuler",
        # Language Menu
        "language.title": "Choisir la Langue",
        # Pause Menu
        "pause.title": "Pause",
        "pause.resume": "Reprendre",
        "pause.save": "Sauvegarder",
        "pause.load": "Charger",
        "pause.settings": "Paramètres",
        "pause.main_menu": "Menu Principal",
        "pause.quit": "Quitter",
        # Game Over
        "game_over.title": "Partie Terminée",
        "game_over.winner": "Joueur {player} Gagne!",
        "game_over.save_replay": "Sauvegarder Replay",
        "game_over.new_game": "Nouvelle Partie",
        "game_over.main_menu": "Menu Principal",
        "game_over.quit": "Quitter",
        # Common
        "common.menu_hint": "Flèches : Naviguer   Entrée : Sélectionner   Échap : Retour",
        "common.back": "Retour",
        "common.confirm": "Confirmer",
        "common.cancel": "Annuler",
        # Credits
        "credits.title": "Crédits",
        "credits.game_title": "REINFORCE TACTICS",
        "credits.developer": "Développeur:",
        "credits.developer_name": "Michael Kudlaty",
        "credits.description": "Jeu de Stratégie au Tour par Tour avec Apprentissage par Renforcement",
        # Game
        "player": "Joueur",
        "gold": "Or",
        "turn": "Tour",
        "end_turn": "Fin du Tour",
        "resign": "Abandonner",
        "game_over": "Partie Terminée!",
        "winner": "gagne!",
        "controls_title": "Contrôles",
        "controls_select": "Cliquez pour sélectionner",
        "controls_move": "Cliquez pour déplacer",
        "controls_end_turn": "ESPACE pour finir le tour",
        "controls_quit": "ESC pour quitter",
        # Units
        "warrior": "Guerrier",
        "mage": "Mage",
        "cleric": "Clerc",
        "barbarian": "Barbare",
        "health": "Santé",
        "attack": "Attaque",
        "movement": "Mouvement",
        "cost": "Coût",
        "status": "Statut",
        "abilities": "Capacités",
        # Messages
        "loading": "Chargement...",
        "saving": "Sauvegarde...",
        "not_implemented": "Pas encore implémenté",
        "error": "Erreur",
        "success": "Succès",
        "confirm": "Confirmer",
        "cancel": "Annuler",
        # Map Editor
        "map_editor.title": "Éditeur de Carte",
        "map_editor.new_map": "Nouvelle Carte",
        "map_editor.edit_map": "Modifier une Carte",
        "map_editor.save": "Enregistrer Carte",
        "map_editor.load": "Charger Carte",
        "map_editor.new_map_dialog.title": "Créer une Nouvelle Carte",
        "map_editor.new_map_dialog.width": "Largeur:",
        "map_editor.new_map_dialog.height": "Hauteur:",
        "map_editor.new_map_dialog.players": "Joueurs:",
        "map_editor.new_map_dialog.create": "Créer",
        "map_editor.new_map_dialog.min_size": "Taille minimum: {size}x{size}",
        "map_editor.tile_palette.title": "Palette de Tuiles",
        "map_editor.tile_palette.terrain": "Terrain",
        "map_editor.tile_palette.structures": "Structures",
        "map_editor.tile_palette.neutral": "Neutre",
        "map_editor.tile_palette.player": "Joueur {number}",
        "map_editor.canvas.grid": "Grille: Activée",
        "map_editor.canvas.grid_off": "Grille: Désactivée",
        "map_editor.canvas.coordinates": "X: {x}, Y: {y}",
        "map_editor.tools.paint": "Pinceau",
        "map_editor.tools.erase": "Effacer",
        "map_editor.tools.fill": "Remplir",
        "map_editor.save_dialog.title": "Enregistrer Carte",
        "map_editor.save_dialog.filename": "Nom de fichier:",
        "map_editor.save_dialog.overwrite": "Le fichier existe. Écraser?",
        "map_editor.validation.no_hq": "Chaque joueur doit avoir exactement un Quartier Général",
        "map_editor.validation.min_size": "La carte doit faire au moins {size}x{size}",
        "map_editor.validation.invalid_hq": "Le joueur {player} a besoin d'un Quartier Général",
        "map_editor.shortcuts.title": "Raccourcis Clavier",
        "map_editor.shortcuts.save": "Ctrl+S: Enregistrer",
        "map_editor.shortcuts.new": "Ctrl+N: Nouvelle Carte",
        "map_editor.shortcuts.open": "Ctrl+O: Ouvrir Carte",
        "map_editor.shortcuts.grid": "G: Activer/Désactiver Grille",
        "map_editor.shortcuts.esc": "Esc: Quitter",
    },
    "korean": {
        # Main Menu
        "main_title": "REINFORCE TACTICS",
        "main_subtitle": "턴제 전략 게임 with RL",
        "menu_1v1_human": "1v1 (인간 vs 인간)",
        "menu_1v1_computer": "1v1 (인간 vs 컴퓨터)",
        "menu_replay": "리플레이 보기",
        "menu_load": "게임 불러오기",
        "menu_settings": "설정",
        "menu_exit": "종료",
        "press_esc": "ESC를 눌러 종료",
        # Main Menu (alternative keys)
        "main_menu.title": "Reinforce Tactics",
        "main_menu.new_game": "새 게임",
        "main_menu.load_game": "불러오기",
        "main_menu.watch_replay": "리플레이 보기",
        "main_menu.credits": "크레딧",
        "main_menu.settings": "설정",
        "main_menu.quit": "종료",
        "main_menu.menu_hint": "방향키: 이동   Enter: 선택   Esc: 종료",
        "main_menu.quit_confirm_title": "Reinforce Tactics 종료",
        "main_menu.quit_confirm_msg": "게임을 종료할까요?",
        # Settings Menu
        "settings_title": "설정",
        "settings_language": "언어",
        "settings_paths": "파일 경로",
        "settings_video": "비디오 설정",
        "settings_maps_path": "맵 디렉토리",
        "settings_videos_path": "비디오 디렉토리",
        "settings_replays_path": "리플레이 디렉토리",
        "settings_saves_path": "저장 디렉토리",
        "settings_reset": "기본값으로 재설정",
        "settings_back": "뒤로",
        "settings_save": "저장",
        "settings_saved": "설정이 저장되었습니다!",
        "settings_reset_confirm": "모든 설정을 기본값으로 재설정하시겠습니까?",
        # Settings Menu (alternative keys)
        "settings.title": "설정",
        "settings.language": "언어",
        "settings.sound": "소리",
        "settings.fullscreen": "전체 화면",
        # Map Selection
        "map_select_title": "맵 선택",
        "map_select": "선택",
        "map_random": "무작위 맵",
        "map_back": "뒤로",
        # New Game Menu
        "new_game.title": "맵 선택",
        "new_game.select_mode": "게임 모드 선택",
        # Player Configuration Menu
        "player_config.title": "플레이어 설정",
        "player_config.player": "플레이어 {number}",
        "player_config.type_human": "인간",
        "player_config.type_computer": "컴퓨터",
        "player_config.difficulty": "난이도",
        "player_config.difficulty_simple": "SimpleBot",
        "player_config.difficulty_normal": "NormalBot (곧 출시)",
        "player_config.difficulty_hard": "HardBot (곧 출시)",
        "player_config.start_game": "게임 시작",
        # Save/Load Game
        "save_game.title": "게임 저장",
        "save_game.enter_name": "저장 이름 입력:",
        "save_game.instructions": "ENTER로 저장, ESC로 취소",
        "load_game.title": "게임 불러오기",
        "load_game.status_in_progress": "진행 중",
        "load_game.status_completed": "완료",
        "load_game.winner_label": "승자: 플레이어 {player}",
        "load_game.completed_title": "완료된 게임",
        "load_game.completed_confirm": "이 게임은 이미 종료되었습니다. 그래도 불러오시겠습니까?",
        # Quit Confirmation
        "quit_confirm.title": "게임 종료",
        "quit_confirm.message": "종료 전에 저장하시겠습니까?",
        "quit_confirm.save_quit": "저장 후 종료",
        "quit_confirm.quit": "종료",
        "quit_confirm.cancel": "취소",
        # Language Menu
        "language.title": "언어 선택",
        # Pause Menu
        "pause.title": "일시 정지",
        "pause.resume": "계속",
        "pause.save": "저장",
        "pause.load": "불러오기",
        "pause.settings": "설정",
        "pause.main_menu": "메인 메뉴",
        "pause.quit": "종료",
        # Game Over
        "game_over.title": "게임 종료",
        "game_over.winner": "플레이어 {player} 승리!",
        "game_over.save_replay": "리플레이 저장",
        "game_over.new_game": "새 게임",
        "game_over.main_menu": "메인 메뉴",
        "game_over.quit": "종료",
        # Common
        "common.menu_hint": "방향키: 이동   Enter: 선택   Esc: 뒤로",
        "common.back": "뒤로",
        "common.confirm": "확인",
        "common.cancel": "취소",
        # Credits
        "credits.title": "크레딧",
        "credits.game_title": "REINFORCE TACTICS",
        "credits.developer": "개발자:",
        "credits.developer_name": "Michael Kudlaty",
        "credits.description": "강화 학습 기반 턴제 전략 게임",
        # Game
        "player": "플레이어",
        "gold": "골드",
        "turn": "턴",
        "end_turn": "턴 종료",
        "resign": "포기",
        "game_over": "게임 종료!",
        "winner": "승리!",
        "controls_title": "조작법",
        "controls_select": "유닛을 클릭하여 선택",
        "controls_move": "타일을 클릭하여 이동",
        "controls_end_turn": "SPACE로 턴 종료",
        "controls_quit": "ESC로 종료",
        # Units
        "warrior": "전사",
        "mage": "마법사",
        "cleric": "성직자",
        "barbarian": "야만인",
        "health": "체력",
        "attack": "공격력",
        "movement": "이동력",
        "cost": "비용",
        "status": "상태",
        "abilities": "능력",
        # Messages
        "loading": "로딩 중...",
        "saving": "저장 중...",
        "not_implemented": "아직 구현되지 않음",
        "error": "오류",
        "success": "성공",
        "confirm": "확인",
        "cancel": "취소",
        # Map Editor
        "map_editor.title": "맵 에디터",
        "map_editor.new_map": "새 맵",
        "map_editor.edit_map": "기존 맵 수정",
        "map_editor.save": "맵 저장",
        "map_editor.load": "맵 불러오기",
        "map_editor.new_map_dialog.title": "새 맵 만들기",
        "map_editor.new_map_dialog.width": "가로:",
        "map_editor.new_map_dialog.height": "세로:",
        "map_editor.new_map_dialog.players": "플레이어:",
        "map_editor.new_map_dialog.create": "생성",
        "map_editor.new_map_dialog.min_size": "최소 크기: {size}x{size}",
        "map_editor.tile_palette.title": "타일 팔레트",
        "map_editor.tile_palette.terrain": "지형",
        "map_editor.tile_palette.structures": "구조물",
        "map_editor.tile_palette.neutral": "중립",
        "map_editor.tile_palette.player": "플레이어 {number}",
        "map_editor.canvas.grid": "그리드: 켜짐",
        "map_editor.canvas.grid_off": "그리드: 꺼짐",
        "map_editor.canvas.coordinates": "X: {x}, Y: {y}",
        "map_editor.tools.paint": "그리기",
        "map_editor.tools.erase": "지우기",
        "map_editor.tools.fill": "채우기",
        "map_editor.save_dialog.title": "맵 저장",
        "map_editor.save_dialog.filename": "파일 이름:",
        "map_editor.save_dialog.overwrite": "파일이 존재합니다. 덮어쓰시겠습니까?",
        "map_editor.validation.no_hq": "각 플레이어는 정확히 하나의 본부가 있어야 합니다",
        "map_editor.validation.min_size": "맵은 최소 {size}x{size}여야 합니다",
        "map_editor.validation.invalid_hq": "플레이어 {player}에게 정확히 하나의 본부가 필요합니다",
        "map_editor.shortcuts.title": "단축키",
        "map_editor.shortcuts.save": "Ctrl+S: 저장",
        "map_editor.shortcuts.new": "Ctrl+N: 새 맵",
        "map_editor.shortcuts.open": "Ctrl+O: 맵 열기",
        "map_editor.shortcuts.grid": "G: 그리드 토글",
        "map_editor.shortcuts.esc": "Esc: 나가기",
    },
    "spanish": {
        # Main Menu
        "main_title": "REINFORCE TACTICS",
        "main_subtitle": "Estrategia por Turnos con IA",
        "menu_1v1_human": "1v1 (Humano vs Humano)",
        "menu_1v1_computer": "1v1 (Humano vs Computadora)",
        "menu_replay": "Ver Repetición",
        "menu_load": "Cargar Juego",
        "menu_settings": "Configuración",
        "menu_exit": "Salir",
        "press_esc": "Presiona ESC para salir",
        # Main Menu (alternative keys)
        "main_menu.title": "Reinforce Tactics",
        "main_menu.new_game": "Nuevo Juego",
        "main_menu.load_game": "Cargar Juego",
        "main_menu.watch_replay": "Ver Repetición",
        "main_menu.credits": "Créditos",
        "main_menu.settings": "Configuración",
        "main_menu.quit": "Salir",
        "main_menu.menu_hint": "Flechas: Mover   Enter: Seleccionar   Esc: Salir",
        "main_menu.quit_confirm_title": "Salir de Reinforce Tactics",
        "main_menu.quit_confirm_msg": "¿Cerrar el juego?",
        # Settings Menu
        "settings_title": "CONFIGURACIÓN",
        "settings_language": "Idioma",
        "settings_paths": "Rutas de Archivos",
        "settings_video": "Configuración de Video",
        "settings_maps_path": "Directorio de Mapas",
        "settings_videos_path": "Directorio de Videos",
        "settings_replays_path": "Directorio de Repeticiones",
        "settings_saves_path": "Directorio de Guardados",
        "settings_reset": "Restablecer Valores",
        "settings_back": "Atrás",
        "settings_save": "Guardar",
        "settings_saved": "¡Configuración guardada!",
        "settings_reset_confirm": "¿Restablecer toda la configuración?",
        # Settings Menu (alternative keys)
        "settings.title": "Configuración",
        "settings.language": "Idioma",
        "settings.sound": "Sonido",
        "settings.fullscreen": "Pantalla Completa",
        # Map Selection
        "map_select_title": "Seleccionar Mapa",
        "map_select": "Seleccionar",
        "map_random": "Mapa Aleatorio",
        "map_back": "Atrás",
        # New Game Menu
        "new_game.title": "Seleccionar Mapa",
        "new_game.select_mode": "Seleccionar Modo de Juego",
        # Player Configuration Menu
        "player_config.title": "Configurar Jugadores",
        "player_config.player": "Jugador {number}",
        "player_config.type_human": "Humano",
        "player_config.type_computer": "Computadora",
        "player_config.difficulty": "Dificultad",
        "player_config.difficulty_simple": "SimpleBot",
        "player_config.difficulty_normal": "NormalBot (Próximamente)",
        "player_config.difficulty_hard": "HardBot (Próximamente)",
        "player_config.start_game": "Comenzar Juego",
        # Save/Load Game
        "save_game.title": "Guardar Juego",
        "save_game.enter_name": "Nombre del guardado:",
        "save_game.instructions": "Presiona ENTER para guardar, ESC para cancelar",
        "load_game.title": "Cargar Juego",
        "load_game.status_in_progress": "En Progreso",
        "load_game.status_completed": "Completado",
        "load_game.winner_label": "Ganador: Jugador {player}",
        "load_game.completed_title": "Juego Completado",
        "load_game.completed_confirm": "Este juego ya terminó. ¿Cargar de todos modos?",
        # Quit Confirmation
        "quit_confirm.title": "Salir del Juego",
        "quit_confirm.message": "¿Guardar antes de salir?",
        "quit_confirm.save_quit": "Guardar y Salir",
        "quit_confirm.quit": "Salir",
        "quit_confirm.cancel": "Cancelar",
        # Language Menu
        "language.title": "Seleccionar Idioma",
        # Pause Menu
        "pause.title": "Pausa",
        "pause.resume": "Continuar",
        "pause.save": "Guardar",
        "pause.load": "Cargar",
        "pause.settings": "Configuración",
        "pause.main_menu": "Menú Principal",
        "pause.quit": "Salir",
        # Game Over
        "game_over.title": "Fin del Juego",
        "game_over.winner": "¡Jugador {player} Gana!",
        "game_over.save_replay": "Guardar Repetición",
        "game_over.new_game": "Nuevo Juego",
        "game_over.main_menu": "Menú Principal",
        "game_over.quit": "Salir",
        # Common
        "common.menu_hint": "Flechas: Mover   Enter: Seleccionar   Esc: Atrás",
        "common.back": "Atrás",
        "common.confirm": "Confirmar",
        "common.cancel": "Cancelar",
        # Credits
        "credits.title": "Créditos",
        "credits.game_title": "REINFORCE TACTICS",
        "credits.developer": "Desarrollador:",
        "credits.developer_name": "Michael Kudlaty",
        "credits.description": "Juego de Estrategia por Turnos con Aprendizaje por Refuerzo",
        # Game
        "player": "Jugador",
        "gold": "Oro",
        "turn": "Turno",
        "end_turn": "Fin de Turno",
        "resign": "Rendirse",
        "game_over": "¡Juego Terminado!",
        "winner": "¡gana!",
        "controls_title": "Controles",
        "controls_select": "Clic para seleccionar unidades",
        "controls_move": "Clic para mover",
        "controls_end_turn": "ESPACIO para terminar turno",
        "controls_quit": "ESC para salir",
        # Units
        "warrior": "Guerrero",
        "mage": "Mago",
        "cleric": "Clérigo",
        "barbarian": "Bárbaro",
        "health": "Salud",
        "attack": "Ataque",
        "movement": "Movimiento",
        "cost": "Costo",
        "status": "Estado",
        "abilities": "Habilidades",
        # Messages
        "loading": "Cargando...",
        "saving": "Guardando...",
        "not_implemented": "No implementado aún",
        "error": "Error",
        "success": "Éxito",
        "confirm": "Confirmar",
        "cancel": "Cancelar",
    },
    "chinese": {
        # Main Menu
        "main_title": "REINFORCE TACTICS",
        "main_subtitle": "基于强化学习的回合制策略游戏",
        "menu_1v1_human": "1v1 (人类 vs 人类)",
        "menu_1v1_computer": "1v1 (人类 vs 电脑)",
        "menu_replay": "观看回放",
        "menu_load": "加载游戏",
        "menu_settings": "设置",
        "menu_exit": "退出",
        "press_esc": "按ESC退出",
        # Main Menu (alternative keys)
        "main_menu.title": "Reinforce Tactics",
        "main_menu.new_game": "新游戏",
        "main_menu.load_game": "加载游戏",
        "main_menu.watch_replay": "观看回放",
        "main_menu.credits": "制作人员",
        "main_menu.settings": "设置",
        "main_menu.quit": "退出",
        "main_menu.menu_hint": "方向键: 移动   Enter: 选择   Esc: 退出",
        "main_menu.quit_confirm_title": "退出 Reinforce Tactics",
        "main_menu.quit_confirm_msg": "确定要关闭游戏吗？",
        # Settings Menu
        "settings_title": "设置",
        "settings_language": "语言",
        "settings_paths": "文件路径",
        "settings_video": "视频设置",
        "settings_maps_path": "地图目录",
        "settings_videos_path": "视频目录",
        "settings_replays_path": "回放目录",
        "settings_saves_path": "存档目录",
        "settings_reset": "恢复默认",
        "settings_back": "返回",
        "settings_save": "保存",
        "settings_saved": "设置已保存！",
        "settings_reset_confirm": "确定要恢复默认设置吗？",
        # Settings Menu (alternative keys)
        "settings.title": "设置",
        "settings.language": "语言",
        "settings.sound": "声音",
        "settings.fullscreen": "全屏",
        # Map Selection
        "map_select_title": "选择地图",
        "map_select": "选择",
        "map_random": "随机地图",
        "map_back": "返回",
        # New Game Menu
        "new_game.title": "选择地图",
        "new_game.select_mode": "选择游戏模式",
        # Player Configuration Menu
        "player_config.title": "配置玩家",
        "player_config.player": "玩家 {number}",
        "player_config.type_human": "人类",
        "player_config.type_computer": "电脑",
        "player_config.difficulty": "难度",
        "player_config.difficulty_simple": "简单机器人",
        "player_config.difficulty_normal": "普通机器人（即将推出）",
        "player_config.difficulty_hard": "困难机器人（即将推出）",
        "player_config.start_game": "开始游戏",
        "player_config.fog_of_war": "战争迷雾",
        "player_config.game_options": "游戏选项",
        "player_config.bot_simple": "简单机器人",
        "player_config.bot_medium": "中等机器人",
        "player_config.bot_advanced": "高级机器人",
        "player_config.bot_openai": "OpenAI (GPT)",
        "player_config.bot_claude": "Claude",
        "player_config.bot_gemini": "Gemini",
        "player_config.bot_model": "自定义模型",
        "player_config.no_api_key": "（无 API Key）",
        "player_config.browse": "浏览…",
        # Settings extras
        "settings.graphics": "图形",
        "settings.units": "单位设置",
        "settings.api_keys": "LLM API 密钥",
        "settings.sound_nyi": "声音（未实现）",
        # Graphics
        "graphics.title": "图形设置",
        "graphics.not_set": "（未设置）",
        "graphics.not_set_auto": "（自动）",
        "graphics.animation_path": "动画精灵表路径",
        "graphics.unit_path": "静态精灵路径",
        "graphics.tile_path": "地形精灵路径",
        "graphics.edit_unit_path": "编辑单位精灵路径",
        "graphics.edit_animation_path": "编辑动画精灵路径",
        "graphics.edit_tile_path": "编辑地形精灵路径",
        "graphics.path_hint": "输入精灵文件夹路径",
        "graphics.path_example": "示例: images/sprites/units",
        "graphics.press_enter": "回车保存，ESC 取消",
        "graphics.paste_hint": "Ctrl+V 从剪贴板粘贴",
        # Units settings
        "units.title": "单位设置",
        "units.enable_all": "启用全部单位",
        "units.disable_all": "禁用全部单位",
        "units.basic_only": "仅基础单位 (W,M,C,A)",
        "units.advanced_only": "仅高级单位 (K,R,S,B)",
        # API keys
        "api_keys.title": "LLM API 密钥配置",
        "api_keys.instructions": "输入各 LLM 提供商的 API 密钥（留空则使用环境变量）",
        # In-game unit action menu
        "unit_action.title": "单位行动",
        "unit_action.attack": "攻击 (A)",
        "unit_action.paralyze": "麻痹 (P)",
        "unit_action.heal": "治疗 (H)",
        "unit_action.cure": "驱散 (C)",
        "unit_action.haste": "加速 (T)",
        "unit_action.defence_buff": "防御强化 (D)",
        "unit_action.attack_buff": "攻击强化 (B)",
        "unit_action.capture": "占领 (S)",
        "unit_action.cancel_move": "取消移动 (M)",
        "unit_action.wait": "待命 / 结束 (W)",
        # Unit purchase
        "unit_purchase.title": "购买单位",
        "unit_purchase.cost_suffix": "金",
        # Extra unit names
        "archer": "弓箭手",
        "knight": "骑士",
        "rogue": "刺客",
        "sorcerer": "术士",
        # Tooltips
        "tooltip.can_move": "可移动",
        "tooltip.can_act": "可行动",
        "tooltip.paralyzed": "麻痹（{turns}）",
        "tooltip.hp": "生命: {current}/{max}",
        "tooltip.atk_def": "攻击: {atk}  防御: {defence}",
        "tooltip.mov": "移动: {mov}",
        "tooltip.player_unit": "{name}（玩家{player}）",
        # Misc
        "game_over.turns": "回合数: {turns}",
        "pause.main_menu_confirm_title": "返回主菜单",
        "pause.main_menu_confirm_msg": "未保存的进度将丢失。是否继续？",
        "load_game.no_saves": "未找到存档",
        "replay.title": "选择回放",
        "replay.no_replays": "未找到回放",
        "common.disabled": "关",
        "common.enabled": "开",
        "common.save": "保存",
        "dialog.confirm_hint": "按 Y 确认，按 N 或 ESC 取消",
        "new_game.random_map": "随机地图",
        # Map Editor
        "map_editor.title": "地图编辑器",
        "map_editor.new_map": "新建地图",
        "map_editor.edit_map": "编辑已有地图",
        "map_editor.save": "保存地图",
        "map_editor.load": "加载地图",
        "map_editor.new_map_dialog.title": "创建新地图",
        "map_editor.new_map_dialog.width": "宽度:",
        "map_editor.new_map_dialog.height": "高度:",
        "map_editor.new_map_dialog.players": "玩家数:",
        "map_editor.new_map_dialog.create": "创建",
        "map_editor.new_map_dialog.min_size": "最小尺寸: {size}x{size}",
        "map_editor.tile_palette.title": "图块面板",
        "map_editor.tile_palette.terrain": "地形",
        "map_editor.tile_palette.structures": "建筑",
        "map_editor.tile_palette.neutral": "中立",
        "map_editor.tile_palette.player": "玩家 {number}",
        "map_editor.canvas.grid": "网格: 开",
        "map_editor.canvas.grid_off": "网格: 关",
        "map_editor.canvas.coordinates": "X: {x}, Y: {y}",
        "map_editor.tools.paint": "绘制",
        "map_editor.tools.erase": "擦除",
        "map_editor.tools.fill": "填充",
        "map_editor.save_dialog.title": "保存地图",
        "map_editor.save_dialog.filename": "文件名:",
        "map_editor.save_dialog.overwrite": "文件已存在。是否覆盖？",
        "map_editor.validation.no_hq": "每个玩家必须恰好有一个总部",
        "map_editor.validation.min_size": "地图至少为 {size}x{size}",
        "map_editor.validation.invalid_hq": "玩家 {player} 需要恰好一个总部",
        "map_editor.shortcuts.title": "快捷键",
        "map_editor.shortcuts.save": "Ctrl+S: 保存",
        "map_editor.shortcuts.new": "Ctrl+N: 新建地图",
        "map_editor.shortcuts.open": "Ctrl+O: 打开地图",
        "map_editor.shortcuts.grid": "G: 切换网格",
        "map_editor.shortcuts.esc": "Esc: 退出",
        # Save/Load Game
        "save_game.title": "保存游戏",
        "save_game.enter_name": "输入存档名称：",
        "save_game.instructions": "按回车保存，按ESC取消",
        "load_game.title": "加载游戏",
        "load_game.status_in_progress": "进行中",
        "load_game.status_completed": "已完成",
        "load_game.winner_label": "获胜者: 玩家 {player}",
        "load_game.completed_title": "已完成的游戏",
        "load_game.completed_confirm": "该游戏已经结束。是否仍要加载？",
        # Quit Confirmation
        "quit_confirm.title": "退出游戏",
        "quit_confirm.message": "退出前是否保存？",
        "quit_confirm.save_quit": "保存并退出",
        "quit_confirm.quit": "退出",
        "quit_confirm.cancel": "取消",
        # Language Menu
        "language.title": "选择语言",
        # Pause Menu
        "pause.title": "暂停",
        "pause.resume": "继续",
        "pause.save": "保存",
        "pause.load": "加载",
        "pause.settings": "设置",
        "pause.main_menu": "主菜单",
        "pause.quit": "退出",
        # Game Over
        "game_over.title": "游戏结束",
        "game_over.winner": "玩家 {player} 获胜！",
        "game_over.save_replay": "保存回放",
        "game_over.new_game": "新游戏",
        "game_over.main_menu": "主菜单",
        "game_over.quit": "退出",
        # Common
        "common.menu_hint": "方向键: 移动   Enter: 选择   Esc: 返回",
        "common.back": "返回",
        "common.confirm": "确认",
        "common.cancel": "取消",
        # Credits
        "credits.title": "制作人员",
        "credits.game_title": "REINFORCE TACTICS",
        "credits.developer": "开发者:",
        "credits.developer_name": "Michael Kudlaty",
        "credits.description": "基于强化学习的回合制策略游戏",
        # Game
        "player": "玩家",
        "gold": "金币",
        "turn": "回合",
        "end_turn": "结束回合",
        "resign": "投降",
        "game_over": "游戏结束！",
        "winner": "获胜！",
        "controls_title": "操作说明",
        "controls_select": "点击选择单位",
        "controls_move": "点击移动",
        "controls_end_turn": "空格键结束回合",
        "controls_quit": "ESC退出",
        # Units
        "warrior": "战士",
        "mage": "法师",
        "cleric": "牧师",
        "barbarian": "野蛮人",
        "health": "生命值",
        "attack": "攻击力",
        "movement": "移动力",
        "cost": "费用",
        "status": "状态",
        "abilities": "技能",
        # Messages
        "loading": "加载中...",
        "saving": "保存中...",
        "not_implemented": "尚未实现",
        "error": "错误",
        "success": "成功",
        "confirm": "确认",
        "cancel": "取消",
    },
}

LANGUAGE_NAMES = {"english": "English", "french": "Français", "korean": "한국어", "spanish": "Español", "chinese": "中文"}

# Language code mappings (for flexibility)
LANGUAGE_CODES = {
    "en": "english",
    "fr": "french",
    "ko": "korean",
    "es": "spanish",
    "zh": "chinese",
    "english": "english",
    "french": "french",
    "korean": "korean",
    "spanish": "spanish",
    "chinese": "chinese",
}


class Language:
    """Language manager for translations."""

    def __init__(self, language: str = "english"):
        """
        Initialize language manager.

        Args:
            language: Language name or code (e.g., 'english', 'en', 'french', 'fr')
        """
        self.set_language(language)

    def set_language(self, language: str) -> bool:
        """
        Set current language.

        Args:
            language: Language name or code

        Returns:
            True if language was set successfully
        """
        # Normalize language code
        lang_key = language.lower()
        normalized = LANGUAGE_CODES.get(lang_key, lang_key)

        if normalized in TRANSLATIONS:
            self.current_language = normalized
            # Fonts are cached without language in the key; CJK vs Latin must
            # re-resolve after a language switch (see utils.fonts).
            try:
                from reinforcetactics.utils.fonts import clear_font_cache

                clear_font_cache()
            except Exception:  # pylint: disable=broad-except
                pass
            print(f"✅ Language set to: {LANGUAGE_NAMES.get(normalized, normalized)}")
            return True
        print(f"❌ Language '{language}' not available, using English")
        self.current_language = "english"
        try:
            from reinforcetactics.utils.fonts import clear_font_cache

            clear_font_cache()
        except Exception:  # pylint: disable=broad-except
            pass
        return False

    def get(self, key: str, default: str | None = None) -> str:
        """
        Get translation for key.

        Args:
            key: Translation key (e.g., 'main_menu.title')
            default: Default value if key not found

        Returns:
            Translated string
        """
        translations = TRANSLATIONS.get(self.current_language, TRANSLATIONS["english"])
        result = translations.get(key)

        # If not found in current language, try English as fallback
        if result is None and self.current_language != "english":
            result = TRANSLATIONS["english"].get(key)

        return result if result is not None else (default or key)

    def get_all_languages(self) -> list:
        """Get list of all available languages."""
        return list(TRANSLATIONS.keys())

    def get_language_display_name(self, language: str | None = None) -> str:
        """
        Get display name for language.

        Args:
            language: Language code (uses current if None)

        Returns:
            Display name (e.g., 'English', 'Français')
        """
        if language is None:
            language = self.current_language

        # Normalize
        normalized = LANGUAGE_CODES.get(language.lower(), language.lower())
        return LANGUAGE_NAMES.get(normalized, language.capitalize())

    def get_current_language(self) -> str:
        """Get current language code."""
        return self.current_language


# Global language instance
_language_instance: Language | None = None  # pylint: disable=invalid-name


def get_language() -> Language:
    """
    Get global language instance.

    Creates instance on first call using settings if available.

    Returns:
        Language instance
    """
    global _language_instance
    if _language_instance is None:
        # Try to get language from settings
        try:
            from reinforcetactics.utils.settings import get_settings

            settings = get_settings()
            _language_instance = Language(settings.get_language())
        except (ImportError, Exception):
            # Fallback to English if settings not available
            _language_instance = Language("english")
    return _language_instance


def reset_language(lang_code: str = "english") -> Language:
    """
    Reset global language instance to a new language.

    This function was missing and is needed by menus.py LanguageMenu._set_language()

    Args:
        lang_code: Language code or name (e.g., 'en', 'english', 'fr', 'french')

    Returns:
        The new Language instance
    """
    global _language_instance
    _language_instance = Language(lang_code)

    # Also try to persist to settings
    try:
        from reinforcetactics.utils.settings import get_settings

        settings = get_settings()
        # Normalize the language code
        normalized = LANGUAGE_CODES.get(lang_code.lower(), lang_code.lower())
        settings.set_language(normalized)
    except (ImportError, Exception):
        pass  # Settings not available, just update in-memory

    return _language_instance


def t(key: str, default: str | None = None) -> str:
    """
    Shorthand for translation.

    Args:
        key: Translation key
        default: Default value if not found

    Returns:
        Translated string
    """
    return get_language().get(key, default)
