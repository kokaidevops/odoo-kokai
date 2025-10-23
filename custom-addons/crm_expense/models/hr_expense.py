from odoo import _, api, fields, models


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    opportunity_id = fields.Many2one('crm.lead', string='Opportunity', related='sheet_id.opportunity_id')


class HRExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    expense_ids = fields.One2many('hr.expense.sheet', 'opportunity_id', string='Expense')