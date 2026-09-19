# Copyright (C) 2026 AutoKey contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import pytest
from hamcrest import *

import autokey.interface


@pytest.mark.parametrize("alt_list, expected, description", [
    # A stock layout: AltGr is keycode 108, its own symbol.
    [[(108, 0)], (0, 1, 4, 5), "stock AltGr on 108"],
    # AltGr elsewhere. This is the case the old code missed: it required keycode
    # 108 specifically, so a keyboard with Control_R on 108 and AltGr on 92 lost
    # the AltGr levels entirely.
    [[(49, 0), (92, 0), (92, 2), (108, 2)], (0, 1, 4, 5), "AltGr on 92, Control_R on 108"],
    [[(92, 0)], (0, 1, 4, 5), "AltGr on 92 only"],
    # ISO_Level3_Shift present only as a secondary symbol is not an AltGr key.
    [[(108, 2)], (0, 1), "only as a shifted symbol"],
    [[(49, 1), (92, 3)], (0, 1), "only at non-zero offsets"],
    # No AltGr at all.
    [[], (0, 1), "absent"],
])
def test_usable_offsets(alt_list, expected, description):
    """
    Offsets 4 and 5 are the AltGr levels. Whether AutoKey can reach them decides
    whether a character living there is considered typeable -- or whether AutoKey
    rewrites the keyboard mapping to borrow a spare keycode for it, which it then
    never restores.
    """
    assert_that(autokey.interface.XInterfaceBase._usable_offsets(alt_list),
                is_(expected), description)
