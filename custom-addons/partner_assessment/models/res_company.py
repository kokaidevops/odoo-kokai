from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    partner_assessment_approval_id = fields.Many2one('approval.category', string='Partner Assessment Approval Type')