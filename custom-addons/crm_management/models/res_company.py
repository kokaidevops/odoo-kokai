from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    issue_approval_id = fields.Many2one('approval.category', string='Issue Approval Type')
    contract_approval_id = fields.Many2one('approval.category', string='Contract Approval Type')