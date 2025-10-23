from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    approval_business_trip_id = fields.Many2one('approval.category', string='Approval Business Trip')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_business_trip_id = fields.Many2one('approval.category', string='Approval Business Trip', related='company_id.approval_business_trip_id', readonly=False)