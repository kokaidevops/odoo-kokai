from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    recruitment_request_approval_id = fields.Many2one('approval.category', string='Recruitment Request Approval')