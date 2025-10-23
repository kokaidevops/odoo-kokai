from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    approval_budget_plan_id = fields.Many2one('approval.category', string='Approval Budget Plan')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_budget_plan_id = fields.Many2one('approval.category', string='Approval Budget Plan', related='company_id.approval_budget_plan_id', readonly=False)