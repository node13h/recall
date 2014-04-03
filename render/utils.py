# Recall - ics file renderer>
# Copyright (C) 2014  Sergej Alikov <sergej.alikov@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime

# HEIGHT_RATIO is used to convert minutes into ruler units
HEIGHT_RATIO = 0.05

# Unfilled portion at the bottom of the event in
# minutes (to create visual spacer)
SPACER = 1


def to_datetime(dt, tz):
    if isinstance(dt, datetime.datetime):
        if dt.tzinfo:
            result = dt.astimezone(tz)
        else:
            result = tz.localize(dt)
    elif isinstance(dt, datetime.date):
        result = tz.localize(datetime.datetime.combine(
            dt, datetime.time.min))
    else:
        raise ValueError('You must use datetime or date')

    return result


def ruler_units(minutes):
    return minutes * HEIGHT_RATIO


def adjust_duration(minutes):
    if minutes > SPACER:
        m = minutes - SPACER
    else:
        m = minutes

    return m
