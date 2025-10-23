from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    approval_shift_change_id = fields.Many2one('approval.category', string='Approval Shift Change')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_shift_change_id = fields.Many2one('approval.category', string='Approval Shift Change', related='company_id.approval_shift_change_id', readonly=False)