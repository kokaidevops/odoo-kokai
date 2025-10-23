from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _prepare_equipment_values(self):
        return {
            'name': "%s" % (self.product_id.name),
            'category_id': self.product_id.equipment_category_id.id,
            'equipment_assign_to': self.product_id.equipment_assign_to,
            'maintenance_team_id': self.product_id.maintenance_team_id.id,
            'serial_no': self.lot_id.name,
            'product_id': self.product_id.id,
            'location_id': self.location_id.id,
            'lot_id': self.lot_id.id,
        }

    def action_generate_equipment(self):
        if not self.product_id.is_equipment:
            raise ValidationError("Can't create Equipment for product that aren't equipment!")
        data = self._prepare_equipment_values()
        if self.lot_id.equipment_id:
            raise ValidationError("Equipment has been created!")
        try:
            equipment = self.env['maintenance.equipment'].create(data)
            self.lot_id.write({ 'equipment_id': equipment.id })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Equipment "%s" created successfully') % (equipment.name),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'}
                }
            }
        except Exception as e:
            raise ValidationError("Failed create Equipment: %s" % str(e))


class StockLot(models.Model):
    _inherit = 'stock.lot'

    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')