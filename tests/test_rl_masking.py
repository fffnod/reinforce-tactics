"""Tests for reinforcetactics.rl.masking targeting previously uncovered paths."""

import numpy as np
import pytest

from reinforcetactics.core.unit import Unit
from reinforcetactics.rl.gym_env import StrategyGameEnv
from reinforcetactics.rl.masking import (
    ActionMaskedEnv,
    make_maskable_env,
    make_maskable_vec_env,
    validate_action_mask,
)


class TestActionMaskedEnvBasics:
    def test_delegates_attribute_access(self):
        base = StrategyGameEnv(opponent="random", render_mode=None)
        wrapped = ActionMaskedEnv(base)
        # grid_width is on the base env; wrapper should pass through
        assert wrapped.grid_width == base.grid_width
        assert wrapped.grid_height == base.grid_height
        wrapped.close()

    def test_stats_disabled_returns_empty_dict(self):
        base = StrategyGameEnv(opponent="random", render_mode=None)
        wrapped = ActionMaskedEnv(base, track_stats=False)
        wrapped.reset()
        assert wrapped.get_masking_stats() == {}
        wrapped.close()

    def test_stats_track_percentages(self):
        base = StrategyGameEnv(opponent="random", render_mode=None)
        wrapped = ActionMaskedEnv(base, track_stats=True)
        wrapped.reset()
        # Send two end_turn actions (action_type=5)
        for _ in range(2):
            wrapped.step(np.array([5, 0, 0, 0, 0, 0]))
        stats = wrapped.get_masking_stats()
        assert stats["total_actions"] == 2
        assert "action_type_percentages" in stats
        # index 5 = end_turn => 100%
        assert stats["action_type_percentages"][5] == pytest.approx(100.0)
        wrapped.close()


class TestMakeMaskableEnv:
    def test_default_construction(self):
        env = make_maskable_env(opponent="random")
        env.reset()
        masks = env.action_masks()
        assert isinstance(masks, np.ndarray)
        assert masks.dtype == np.bool_
        env.close()

    def test_flat_discrete_mode(self):
        env = make_maskable_env(
            opponent="random",
            action_space_type="flat_discrete",
            max_flat_actions=128,
        )
        env.reset()
        # In flat mode, action_masks() still returns a 1D bool array
        masks = env.action_masks()
        assert masks.ndim == 1
        env.close()

    def test_max_turns_threaded_to_underlying_env(self):
        """make_maskable_env should forward max_turns to StrategyGameEnv
        and onto the underlying GameState."""
        wrapped = make_maskable_env(opponent="random", max_turns=11)
        # ActionMaskedEnv delegates attr access to the wrapped StrategyGameEnv
        assert wrapped.max_turns == 11
        assert wrapped.game_state.max_turns == 11
        wrapped.close()

    def test_max_turns_default_none(self):
        wrapped = make_maskable_env(opponent="random")
        assert wrapped.max_turns is None
        assert wrapped.game_state.max_turns is None
        wrapped.close()


class TestMakeMaskableVecEnv:
    def test_dummy_vec_env_single(self):
        vec = make_maskable_vec_env(n_envs=1, opponent="random", use_subprocess=False)
        obs = vec.reset()
        assert obs is not None
        vec.close()

    def test_dummy_vec_env_multiple(self):
        vec = make_maskable_vec_env(n_envs=2, opponent="random", use_subprocess=False)
        obs = vec.reset()
        assert obs is not None
        vec.close()

    def test_max_turns_threaded_to_each_subenv(self):
        """make_maskable_vec_env should forward max_turns to every sub-env."""
        vec = make_maskable_vec_env(
            n_envs=2,
            opponent="random",
            use_subprocess=False,
            max_turns=9,
        )
        # Sub-envs are Monitor(ActionMaskedEnv(StrategyGameEnv)); gymnasium
        # 1.x wrappers don't implicitly forward attributes, so go through
        # the VecEnv API (get_attr uses get_wrapper_attr, which walks the
        # wrapper stack) and .unwrapped for the base env.
        assert vec.get_attr("max_turns") == [9, 9]
        for sub in vec.envs:
            assert sub.unwrapped.game_state.max_turns == 9
        vec.close()


class TestValidateActionMask:
    def test_fresh_game_is_valid(self):
        env = StrategyGameEnv(opponent="random", render_mode=None)
        env.reset()
        result = validate_action_mask(env)
        assert result["valid"] is True
        assert result["errors"] == []
        assert "mask_summary" in result
        # All named action types should appear
        expected = {
            "create",
            "move",
            "attack",
            "seize",
            "heal",
            "end_turn",
            "paralyze",
            "haste",
            "defence_buff",
            "attack_buff",
        }
        assert set(result["mask_summary"].keys()) == expected
        env.close()

    def test_end_turn_always_has_legal_actions(self):
        env = StrategyGameEnv(opponent="random", render_mode=None)
        env.reset()
        result = validate_action_mask(env)
        assert result["mask_summary"]["end_turn"]["has_legal_actions"] is True
        env.close()


class TestMaskCacheAndCure:
    """Mask correctness against direct game-state mutation.

    Ported from tests/verify_mask.py, which pytest never collected because
    the filename did not match the ``test_*.py`` pattern.
    """

    @pytest.fixture
    def env(self):
        env = StrategyGameEnv(map_file=None, opponent="bot", render_mode=None)
        yield env
        env.close()

    def test_cache_invalidation(self, env):
        """Executing an action invalidates the cached action mask."""
        env.reset()
        env.game_state.units = []
        env.game_state._invalidate_cache()

        # Unit at 0,0
        unit = Unit("W", 0, 0, player=1)
        unit.can_move = True
        env.game_state.units.append(unit)
        env.game_state.grid.get_tile(0, 0).type = "p"
        env.game_state.grid.get_tile(1, 0).type = "p"
        env.game_state.current_player = 1

        # 1. Check initial mask (Move to 1,0 is valid)
        mask1 = env._get_action_mask()
        area = env.grid_width * env.grid_height
        idx_move_1_0 = (1 * area) + (0 * env.grid_width + 1)
        assert mask1[idx_move_1_0] == 1.0

        # 2. Execute move to 1,0 (directly via game state to simulate action)
        env.game_state.move_unit(unit, 1, 0)

        # 3. The mask must change: the unit exhausted its movement, and it is
        # the only unit, so the entire move layer should now be invalid.
        mask2 = env._get_action_mask()
        assert not np.array_equal(mask1, mask2), "Mask should change after action"

        move_layer_start = 1 * area
        move_layer_end = 2 * area
        assert np.all(mask2[move_layer_start:move_layer_end] == 0.0), "No moves should be valid after unit moves"

    def test_cure_masking_and_execution(self, env):
        """Cure action is correctly masked and executed."""
        env.reset()
        env.game_state.units = []
        env.game_state._invalidate_cache()

        # Setup: Cleric (Player 1) and Paralyzed Ally (Player 1)
        cleric = Unit("C", 5, 5, player=1)
        cleric.can_attack = True  # Enable unit to act
        ally = Unit("W", 5, 6, player=1)
        ally.paralyzed_turns = 2  # Paralyzed

        env.game_state.units.append(cleric)
        env.game_state.units.append(ally)
        env.game_state._invalidate_cache()

        # 1. Check mask: index for Heal/Cure action (type 4) at ally position (5,6)
        mask = env._get_action_mask()
        area = env.grid_width * env.grid_height
        heal_idx = (4 * area) + (6 * env.grid_width + 5)
        assert mask[heal_idx] == 1.0, "Cure action should be masked as valid"

        # 2. Execute Cure: Type 4 (Heal/Cure), Cleric, From(5,5), To(5,6)
        action_dict = {"action_type": 4, "unit_type": "C", "from_pos": (5, 5), "to_pos": (5, 6)}
        reward, is_valid = env._execute_action(action_dict)

        assert is_valid, "Cure action should be valid"
        assert not ally.is_paralyzed(), "Ally should be cured (paralyzed_turns=0)"
        assert reward > 0, "Should receive reward for curing"
