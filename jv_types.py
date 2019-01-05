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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from . jv_flooring import JVFlooring
from . jv_siding import JVSiding
from . jv_roofing import JVRoofing
from . jv_windows import JVWindows


registered_types = {
    "flooring": JVFlooring,
    "siding": JVSiding,
    "roofing": JVRoofing,
    "windows": JVWindows
}


def get_object_type_handler(object_type: str):
    return registered_types.get(object_type, None)
