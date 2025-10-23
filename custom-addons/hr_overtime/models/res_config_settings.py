from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    approval_overtime_id = fields.Many2one('approval.category', string='Approval Overtime')
    approval_overtime_batch_id = fields.Many2one('approval.category', string='Approval Overtime Batch')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_overtime_id = fields.Many2one('approval.category', string='Approval Overtime', related='company_id.approval_overtime_id', readonly=False)
    approval_overtime_batch_id = fields.Many2one('approval.category', string='Approval Overtime Batch', related='company_id.approval_overtime_batch_id', readonly=False)