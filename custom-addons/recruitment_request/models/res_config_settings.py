from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    recruitment_request_approval_id = fields.Many2one('approval.category', string='Recruitment Request Approval', related='company_id.recruitment_request_approval_id', readonly=False)