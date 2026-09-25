# Copyright (C) 2018 Thomas Hess <thomas.hess@udo.edu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import typing

import pytest
from hamcrest import *

import autokey.iomediator.constants as iomediator_constants
import autokey.model.key
from unittest.mock import MagicMock

from autokey.iomediator.iomediator import IoMediator
from autokey.model.key import Key


def generate_tests_for_key_split_re():
    """Yields test_input_str, expected_split_list"""
    # Values taken from original test code
    yield "<ctrl>+y", ["", "<ctrl>+", "y"]
    yield "asdf <ctrl>+y asdf ", ["asdf ", "<ctrl>+", "y asdf "]
    yield "<table><ctrl>+y</table>", ["", "<table>", "", "<ctrl>+", "y", "</table>", ""]
    yield "<!<alt_gr>+8CDATA<alt_gr>+8", ["<!", "<alt_gr>+", "8CDATA", "<alt_gr>+", "8"]
    yield "<ctrl>y", ["", "<ctrl>", "y"]
    yield "Test<tab>More text", ["Test", "<tab>", "More text"]


@pytest.mark.parametrize("input_string, expected_split", generate_tests_for_key_split_re())
def test_key_split_re(input_string: str, expected_split: typing.List[str]):
    assert_that(
        autokey.model.key.KEY_SPLIT_RE.split(input_string),
        has_items(*expected_split)
    )


def test_clear_modifiers_uses_xtest_not_xsendevent():
    """
    Held modifiers must be released via IoMediator.release_key(), which routes to
    interface.fake_keyup() and XTEST. interface.release_key() sends an XSendEvent,
    which is delivered to a client but never enters the server's input pipeline, so
    the modifier stays held and every character of an expansion arrives modified.
    """
    mediator = MagicMock()
    mediator.releasedModifiers = []
    mediator.modifiers = {Key.CONTROL: True, Key.HYPER: True, Key.SHIFT: False}

    IoMediator._clear_modifiers(mediator)

    assert_that(mediator.releasedModifiers, contains_inanyorder(Key.CONTROL, Key.HYPER))
    assert_that(mediator.release_key.call_count, is_(2))
    mediator.interface.release_key.assert_not_called()


def test_reapply_modifiers_does_not_resurrect_a_released_modifier():
    """
    _reapply_modifiers() must not press anything.

    While the release went out as an XSendEvent it was in effect a no-op, so
    re-pressing was harmless. Once the release actually works (XTEST), a re-press
    is a real key press: if the user let go of the modifier while the expansion was
    typing, it goes down with no physical release coming and sticks, leaving the
    keyboard in shift or control until the user clears it by hand.

    Observed in the wild with a script bound to <alt>+<ctrl>+<hyper>+<shift>+,
    which slept 100ms before typing -- easily long enough to let go.
    """
    mediator = MagicMock()
    mediator.releasedModifiers = [Key.CONTROL, Key.HYPER]

    IoMediator._reapply_modifiers(mediator)

    mediator.press_key.assert_not_called()
    mediator.interface.press_key.assert_not_called()
    assert_that(mediator.releasedModifiers, is_([]))


def test_modifier_keysyms_resolve_to_the_left_hand_variant():
    """
    XK_TO_AK_MAP maps both variants of each modifier onto one Key, so inverting it
    silently keeps the right-hand one. Releasing Hyper_R does not clear a Hyper_L
    the user is physically holding.
    """
    from Xlib import XK
    from autokey.interface import AK_TO_XK_MAP

    assert_that(AK_TO_XK_MAP[Key.HYPER], is_(XK.XK_Hyper_L))
    assert_that(AK_TO_XK_MAP[Key.CONTROL], is_(XK.XK_Control_L))
    assert_that(AK_TO_XK_MAP[Key.SHIFT], is_(XK.XK_Shift_L))


@pytest.mark.parametrize("string, types_chars", [
    # Explicit key combinations and special keys type nothing.
    ["<ctrl>+<np_page_up>", False],
    ["<ctrl>+<shift>+<f5>", False],
    ["<ctrl>+v", False],
    ["<enter>", False],
    # Anything with literal text does.
    ["2026-09-18", True],
    ["hello <ctrl>+a there", True],
])
def test_types_characters(string, types_chars):
    """
    Held modifiers are cleared so they cannot corrupt typed text. A string that
    only sends a key combination types nothing, so there is nothing to protect --
    and releasing a modifier the user is holding disturbs the receiving
    application: Chrome drops or delays the synthetic key that follows.
    """
    assert_that(IoMediator._types_characters(MagicMock(), string), is_(types_chars))
