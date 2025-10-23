from odoo import _, api, fields, models

class ResCity(models.Model):
    _name = 'res.city'
    _description = 'Res City'

    name = fields.Char('Name', required=True)
    state_id = fields.Many2one('res.country.state', string='State', ondelete='cascade')