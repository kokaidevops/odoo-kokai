from odoo import _, api, fields, models

class ResWard(models.Model):
    _name = 'res.ward'
    _description = 'Res Ward'

    name = fields.Char('Name', required=True)
    subdistrict_id = fields.Many2one('res.subdistrict', string='Subdistrict')