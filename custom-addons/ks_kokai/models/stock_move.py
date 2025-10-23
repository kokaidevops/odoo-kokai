from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    weight_total = fields.Float(
        string='Total Weight (kg)',
        compute='_compute_weight_total',
        store=True,
        digits='Product Unit of Measure'
    )
    
    unit_weight = fields.Float(
        string='Unit Weight (kg)',
        compute='_compute_weight_total',
        digits='Product Unit of Measure'
    )
    
    @api.depends('product_id', 'lot_ids', 'quantity_done')
    def _compute_weight_total(self):
        for move in self:
            if move.product_id.track_weight_by_serial and move.lot_ids:
                move.weight_total = sum(lot.current_weight for lot in move.lot_ids)
                move.unit_weight = move.weight_total / len(move.lot_ids) if move.lot_ids else 0
            else:
                move.weight_total = move.quantity_done * move.product_id.standard_weight_per_unit
                move.unit_weight = move.product_id.standard_weight_per_unit
    
    def _get_price_unit(self):
        """Override to calculate price based on weight"""
        price_unit = super()._get_price_unit()
        
        if self.product_id.valuation_by_actual_weight and self.lot_ids:
            # Adjust price based on actual weight vs standard weight
            if self.product_id.standard_weight_per_unit > 0:
                actual_weight = sum(lot.current_weight for lot in self.lot_ids)
                standard_weight = len(self.lot_ids) * self.product_id.standard_weight_per_unit
                
                if standard_weight > 0:
                    weight_factor = actual_weight / standard_weight
                    price_unit = price_unit * weight_factor
        
        return price_unit


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    lot_weight = fields.Float(
        string='Weight (kg)',
        related='lot_id.current_weight',
        readonly=True
    )
    
    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id and self.product_id.track_weight_by_serial:
            # Show weight info
            return {
                'warning': {
                    'title': _('Serial Weight Info'),
                    'message': _('Serial %s has weight: %.3f kg') % (
                        self.lot_id.name,
                        self.lot_id.current_weight
                    )
                }
            }