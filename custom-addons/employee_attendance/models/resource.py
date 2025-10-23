from odoo import _, api, fields, models


class ResourceCalendarLeaves(models.Model):
    _inherit = 'resource.calendar.leaves'

    holiday = fields.Boolean('Holiday', help="If enabled, this leave will be considered as holiday")
    is_working_day = fields.Boolean(string='Working Period?', copy=False, default=False, help="If marked, this period will still be counted as a working day according to" " the Working Schedule, without reducing the number of working days in the month.")


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    # TODO: Fix this value through the employees._get_work_days_data_batch function
    duration_days = fields.Float(help="Due to technical limitations, this field value should only be entered as 0.5 day or 1 day. Other values may produce unexpected results.")


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def get_total_work_duration_data(self, from_datetime, to_datetime, compute_leaves=True, domain=None):
        """
        Customize the `get_work_duration_data` function.
        Accordingly, this function will add the duration of
            the public holiday (resource.calendar.leaves) if it is marked `is_working_day`
        """
        if compute_leaves:
            if domain is None:
                domain = [('time_type', '=', 'leave'), ('is_working_day', '=', False)]
            else:
                domain += [('time_type', '=', 'leave'), ('is_working_day', '=', False)]
        return self.get_work_duration_data(from_datetime, to_datetime, compute_leaves=compute_leaves, domain=domain)