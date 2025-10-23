from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    activity_revision_id = fields.Many2one('mail.activity.type', string='Activity Type')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    activity_revision_id = fields.Many2one('mail.activity.type', string='Activity Type', related='company_id.activity_revision_id', readonly=False)