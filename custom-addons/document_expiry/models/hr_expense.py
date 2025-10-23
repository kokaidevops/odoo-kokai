from odoo import _, api, fields, models


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    document_id = fields.Many2one('base.document', string='Document')