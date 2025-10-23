from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    approval_maintenance_id = fields.Many2one('approval.category', string='Approval Maintenance')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_maintenance_id = fields.Many2one('approval.category', string='Approval Maintenance', related='company_id.approval_maintenance_id', readonly=False)