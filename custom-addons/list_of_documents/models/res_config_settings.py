from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    approval_amendment_id = fields.Many2one('approval.category', string='Approval Amendment')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_amendment_id = fields.Many2one('approval.category', string='Approval Amendment', related='company_id.approval_amendment_id', readonly=False)