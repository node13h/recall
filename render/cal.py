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

from copy import copy
import datetime
from collections import OrderedDict
from contextlib import closing

import pytz
from dateutil.rrule import rrulestr
import requests
import icalendar

from render.utils import to_datetime, ruler_units, adjust_duration


class TooManyLinesException(Exception):
    pass


class Rrule(object):
    def __init__(self, vrecur, dtstart, after, before, tz):
        vrecur = copy(vrecur)

        if vrecur:
            if 'UNTIL' in vrecur:
                vrecur['UNTIL'] = [
                    to_datetime(vrecur['UNTIL'][0], tz).astimezone(pytz.utc)]
            self.dtstart = dtstart
            self.rr = rrulestr(
                vrecur.to_ical(), dtstart=self.dtstart).between(
                after, before, True)

        else:
            self.rr = []

    def occurences(self, date):
        for o in self.rr:
            if o.date() == date:
                yield o


class Event(object):
    start = None
    end = None
    rrule = None

    def __init__(self, vevent, after, before, tz):
        self.summary = vevent.decoded('SUMMARY')
        dtstart = vevent.decoded('DTSTART')
        self.start = to_datetime(dtstart, tz)

        if 'DTEND' in vevent:
            dtend = vevent.decoded('DTEND')
            self.end = to_datetime(dtend, tz)
            self.duration = self.end - self.start

        elif 'DURATION' in vevent:
            self.duration = vevent.decoded('DURATION')
            self.end = self.start + self.duration

        if 'RRULE' in vevent:
            self.rrule = Rrule(vevent['RRULE'], self.start, after, before, tz)

    def occurences(self, date):
        if self.start.date() == date:
            yield self.start
        if self.rrule:
            for o in self.rrule.occurences(date):
                yield o

    @property
    def is_single_day(self):
        if self.duration <= datetime.timedelta(days=1):
            return True
        else:
            return False

    @property
    def is_all_day(self):
        if self.duration >= datetime.timedelta(days=1):
            return True
        else:
            return False


class Week(object):
    def __init__(self, start_date, tz):
        self.tz = tz
        self.days = OrderedDict()
        self.dates = []
        for offset in range(7):
            date = start_date + datetime.timedelta(days=offset)
            self.dates.append(to_datetime(date, tz))
            self.days[date] = []

    @property
    def first_day(self):
        return self.dates[0]

    @property
    def last_day(self):
        return self.dates[-1]

    def add_event(self, vevent):
        e = Event(
            vevent,
            self.first_day,
            self.last_day + datetime.timedelta(days=1),
            self.tz)

        for date, day in self.days.iteritems():
            if not e.is_all_day:

                for o in e.occurences(date):

                    row = {}
                    row['event'] = e
                    row['start'] = o
                    row['end'] = o + e.duration

                    offset_minutes = o.hour * 60 + o.minute
                    row['offset'] = ruler_units(offset_minutes)

                    duration_minutes = e.duration.total_seconds() / 60
                    row['duration'] = ruler_units(
                        adjust_duration(duration_minutes))

                    # TODO: if duration + offset > 86400 => clip and
                    # add extra event to next day

                    day.append(row)

    def _get_start_end(self, e):
        s = e.start.time()
        s_secs = s.hour * 3600 + s.minute * 60 + s.second

        if (s_secs + e.duration.total_seconds()) > 86400:
            e = datetime.time.max
        else:
            e = e.end.time()

        return s, e

    def process_overlapping_events(self):
        for date, day in self.days.iteritems():
            for outer_row in day:
                outer_event = outer_row['event']
                o_start, o_end = self._get_start_end(outer_event)
                overlapping = []

                for inner_row in day:
                    inner_event = inner_row['event']
                    i_start, i_end = self._get_start_end(inner_event)

                    if ((i_end >= o_start >= i_start) or
                            (i_end >= o_end >= i_start)):
                        overlapping.append(inner_event)

                outer_row['overlapping'] = sorted(
                    overlapping, key=lambda x: x.start.time())

                count = len(outer_row['overlapping'])
                idx = outer_row['overlapping'].index(outer_event)
                last = outer_event == outer_row['overlapping'][-1]

                # left and width are in percent
                outer_row['left'] = 100/count * idx
                if last:
                    outer_row['width'] = 100/count
                else:
                    outer_row['width'] = 100/count * 1.7


class CalendarWeekView(object):
    max_lines = 2048
    week = None

    def __init__(self):
        self.ruler = []

        ruler_minutes = 24 * 60
        self.ruler_duration = ruler_units(ruler_minutes)

        for hour in range(24):
            bar = {}

            offset_minutes = hour * 60
            bar['offset'] = ruler_units(offset_minutes)

            duration_minutes = 60
            bar['duration'] = ruler_units(adjust_duration(duration_minutes))

            bar['label'] = '{0}:00'.format(hour)

            self.ruler.append(bar)

    def load_from_url(self, url, start_date, tz=None):
        lines = []
        with closing(requests.get(url, stream=True)) as r:
            for i, line in enumerate(r.iter_lines()):
                lines.append(line)
                if i > self.max_lines:
                    raise TooManyLinesException()

            ics = icalendar.Calendar.from_ical('\n'.join(lines))
            if tz is None:
                try:
                    tz = pytz.timezone(ics.get('X-WR-TIMEZONE', ''))
                except pytz.exceptions.UnknownTimeZoneError:
                    tz = pytz.utc

            self.week = Week(start_date, tz)

            for item in ics.subcomponents:
                if isinstance(item, icalendar.Event):
                    self.week.add_event(item)

            self.week.process_overlapping_events()
