from odoo import _, api, fields, models


class ResourceCalendarLeaves(models.Model):
    _inherit = 'resource.calendar.leaves'

    date = fields.Date('Date', compute='_compute_date', store=True)

    @api.depends('date_from')
    def _compute_date(self):
        for record in self:
            record.date = record.date_from.date()


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    check_in_init = fields.Datetime('Check In Init')
    check_out_init = fields.Datetime('Check Out Init')

    def _skip_generate_work_entry(self):
        skip = super()._skip_generate_work_entry()
        public_holiday = self.env['resource.calendar.leaves'].search([
            ('date', '=', self.date),
            ('holiday', '=', True),
        ], limit=1)
        return skip or len(public_holiday)

    def _attendance_to_work_entry(self, source):
        res = super()._attendance_to_work_entry(source)
        return res or source == 'time_off'