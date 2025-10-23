from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    partner_assessment_approval_id = fields.Many2one('approval.category', string='Partner Assessment Approval Type', related='company_id.partner_assessment_approval_id', readonly=False)