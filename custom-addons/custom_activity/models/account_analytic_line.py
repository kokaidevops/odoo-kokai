from odoo import _, api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    start_date = fields.Datetime('Start Time')
    end_date = fields.Datetime('End Time')
    unit_amount = fields.Float('Hours Spent', compute='_compute_hours_spent', store=True)
    running = fields.Boolean('Running', default=False)
    is_end = fields.Boolean('Is End', default=False)

    def action_start_timer(self):
        self.ensure_one()
        self.sudo().write({ 'running': True, 'start_date': fields.Datetime.now() })

    def action_end_timer(self):
        self.ensure_one()
        self.sudo().write({ 'running': False, 'end_date': fields.Datetime.now() })

    @api.depends('start_date', 'end_date')
    def _compute_hours_spent(self):
        for record in self:
            if record.start_date and record.end_date:
                timer = record.end_date - record.start_date
                secs=timer.seconds
                hours_spent = secs/3600

                record.is_end = True
                record.unit_amount = hours_spent