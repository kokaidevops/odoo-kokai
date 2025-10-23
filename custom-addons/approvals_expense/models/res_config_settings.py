from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    approval_expense_id = fields.Many2one('approval.category', string='Approval Expense')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_expense_id = fields.Many2one('approval.category', string='Approval Expense', related='company_id.approval_expense_id', readonly=False)