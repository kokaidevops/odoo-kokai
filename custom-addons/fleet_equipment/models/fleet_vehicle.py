from odoo import _, api, fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    equipment_ids = fields.One2many('fleet.equipment', 'fleet_id', string='Equipment')


class FleetEquipment(models.Model):
    _name = 'fleet.equipment'
    _description = 'Fleet Equipment'

    fleet_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    equipment_id = fields.Many2one('product.product', string='Equipment')
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial Numbers', domain="[('product_id', '=', equipment_id)]")
    qty = fields.Integer('Qty', default=1)
    uom_id = fields.Many2one('uom.uom', string='UoM', related='equipment_id.uom_id', store=True, readonly=False)
    condition = fields.Selection([
        ('bad', 'Bad'),
        ('good', 'Good'),
        ('maintenance', 'Maintenance'),
    ], string='Condition', default='good')