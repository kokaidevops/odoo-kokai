from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    approval_time_off_id = fields.Many2one('approval.category', string='Approval Time Off')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_time_off_id = fields.Many2one('approval.category', string='Approval Time Off', related='company_id.approval_time_off_id', readonly=False)