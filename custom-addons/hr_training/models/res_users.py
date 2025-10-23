from odoo import _, api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def action_show_training(self):
        self.ensure_one()
        action = self.env.ref('hr_training.hr_training_action').read()[0]
        action['domain'] = [
            '|', '|',
            ('user_id', '=', self.env.user.id),
            ('responsible_id', '=', self.env.user.id),
            ('participant_ids', 'in', [self.env.user.id]),
        ]
        return action