from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_equipment = fields.Boolean('Is Equipment?')
    equipment_category_id = fields.Many2one('maintenance.equipment.category', string='Equipment Category')
    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance Team')
    equipment_assign_to = fields.Selection([
        ('department', 'Department'),
        ('employee', 'Employee'),
        ('other', 'Other'),
    ], string='Used By', default='employee', required=True)