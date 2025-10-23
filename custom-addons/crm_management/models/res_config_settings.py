from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    issue_approval_id = fields.Many2one('approval.category', string='Issue Approval Type', related='company_id.issue_approval_id', readonly=False)
    contract_approval_id = fields.Many2one('approval.category', string='Contract Approval Type', related='company_id.contract_approval_id', readonly=False)