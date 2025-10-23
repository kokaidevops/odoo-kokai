from odoo import _, api, fields, models


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    name = fields.Char('Expense Report Summary', required=True, tracking=True, default='New')

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('hr.expense.sheet')
        return super(HrExpenseSheet, self).create(vals)