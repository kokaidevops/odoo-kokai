from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    so_revision_approval_id = fields.Many2one('approval.category', string='Revision Approval Type')