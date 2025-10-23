from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    approval_po_id = fields.Many2one('approval.category', string='Approval PO')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_po_id = fields.Many2one('approval.category', string='Approval PO', related='company_id.approval_po_id', readonly=False)