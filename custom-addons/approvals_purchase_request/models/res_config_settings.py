from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    approval_pr_id = fields.Many2one('approval.category', string='Approval PR')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_pr_id = fields.Many2one('approval.category', string='Approval PR', related='company_id.approval_pr_id', readonly=False)