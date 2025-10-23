from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    qhse_manager_id = fields.Many2one('res.users', string='QHSE Manager')