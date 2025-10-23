from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'
    
    weight_qty = fields.Float(
        string='Weight Quantity (kg)',
        digits='Product Unit of Measure',
        help='Actual weight for this transaction'
    )
    
    price_per_kg = fields.Float(
        string='Price per kg',
        compute='_compute_price_per_kg',
        digits='Product Price'
    )
    
    @api.depends('value', 'weight_qty')
    def _compute_price_per_kg(self):
        for layer in self:
            if layer.weight_qty > 0:
                layer.price_per_kg = abs(layer.value) / layer.weight_qty
            else:
                layer.price_per_kg = 0
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'stock_move_id' in vals:
                move = self.env['stock.move'].browse(vals['stock_move_id'])
                if move.product_id.track_weight_by_serial:
                    vals['weight_qty'] = move.weight_total
        
        return super().create(vals_list)