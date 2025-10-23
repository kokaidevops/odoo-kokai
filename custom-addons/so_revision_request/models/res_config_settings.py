from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    so_revision_approval_id = fields.Many2one('approval.category', string='Revision Approval Type', related='company_id.so_revision_approval_id', readonly=False)