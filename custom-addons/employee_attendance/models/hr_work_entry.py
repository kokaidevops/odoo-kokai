from odoo import _, api, fields, models


class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    date = fields.Date('Date', compute='_compute_date', store=True)

    @api.depends('date_start')
    def _compute_date(self):
        for record in self:
            record.date = record.date_start.date()

    # employee_id = fields.Many2one(group_expand='_read_group_employee_id', tracking=True)
    # work_entry_type_id = fields.Many2one(tracking=True)
    # date_start = fields.Datetime(tracking=True)
    # date_stop = fields.Datetime(tracking=True)
    # duration = fields.Float(tracking=True)
    # state = fields.Selection(tracking=True)
    # name = fields.Char(tracking=True)

    # def action_cancel_work_entry(self):
    #     self.filtered(lambda r: r.state != 'cancelled').write({'state': 'cancelled'})

    # def action_draft_work_entry(self):
    #     self.filtered(lambda r: r.state != 'draft').write({'state': 'draft'})

    # def action_validate_work_entry(self):
    #     self.action_validate()

    # @api.model
    # def _read_group_employee_id(self, employees, domain, order):
    #     """Read group customization in order to display all the employees in views, even if they are empty.
    #     """
    #     return self.env['hr.employee'].sudo().search([], order=order)