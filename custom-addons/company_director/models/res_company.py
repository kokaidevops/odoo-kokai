from odoo import _, api, fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    director_id = fields.Many2one('res.users', string='Director')