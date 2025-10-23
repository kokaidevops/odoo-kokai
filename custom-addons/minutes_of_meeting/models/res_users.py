from odoo import _, api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def action_show_meetings(self):
        self.ensure_one()
        action = self.env.ref('calendar.action_calendar_event').read()[0]
        action['domain'] = [
            '|',
            #  '|', '|',
            # ('participant_type', '=', 'all'),
            ('user_id', '=', self.env.user.id),
            ('partner_ids', 'in', [self.env.user.partner_id.id]),
            # '&',
            # ('department_ids', 'in', [self.env.user.department_id.id]),
            # ('employee_type_ids', 'in', [self.env.user.employee_id.employee_type_id.id])
        ]
        return action