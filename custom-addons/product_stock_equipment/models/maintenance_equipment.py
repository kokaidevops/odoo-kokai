from odoo import _, api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    product_id = fields.Many2one('product.product', string='Product')
    location_id = fields.Many2one('stock.location', string='Stock Location')
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial Number')
    serial_no = fields.Char(related='lot_id.name')
    is_pack = fields.Boolean('Is Product Pack?', related='product_id.is_pack')

    def action_show_bundle(self):
        self.ensure_one()
        equipment_ids = []
        action = self.env.ref('maintenance.hr_equipment_action').read()[0]
        equipment_ids.append(self.equipment_id.id)
        for pack in self.equipment_id.lot_id.pack_ids:
            for lot in pack.lot_ids:
                equipment_ids.append(lot.equipment_id.id)
        action['domain'] = [('id', 'in', equipment_ids)]
        return action
        # action = self.env.ref('product_bundle_pack.product_pack_action').read()[0]
        # action['domain'] = [('id', '=', self.lot_id.pack_ids.ids)]
        # return action