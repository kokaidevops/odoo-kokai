from odoo import _, api, fields, models

class ResSubdistrict(models.Model):
    _name = 'res.subdistrict'
    _description = 'Res Subdistrict'

    name = fields.Char('Name', required=True)
    city_id = fields.Many2one('res.city', string='City')