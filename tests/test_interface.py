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
