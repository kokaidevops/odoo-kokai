from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # is_coa_installed = fields.Boolean('Is COa Installed')
    quadrant = fields.Selection([
        ('i', 'I'),
        ('ii', 'II'),
        ('iii', 'III'),
        ('iv', 'IV'),
    ], string='Quadrant')