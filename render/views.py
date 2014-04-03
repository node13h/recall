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

from django.views.generic import FormView
import pytz


from render.forms import UploadForm
from render.cal import CalendarWeekView


class RenderFromUrlView(FormView):
    template_name = 'render/from_url.html'
    form_class = UploadForm

    def get_initial(self):
        today = datetime.date.today()
        last_monday = today - datetime.timedelta(days=today.weekday())
        return {'start_date': last_monday}

    def form_valid(self, form):
        try:
            tz = pytz.timezone(form.cleaned_data['timezone'])
        except pytz.exceptions.UnknownTimeZoneError:
            tz = None

        weekview = CalendarWeekView()
        weekview.load_from_url(
            form.cleaned_data['url'], form.cleaned_data['start_date'], tz)

        return self.render_to_response(self.get_context_data(
            weekview=weekview))
