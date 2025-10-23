from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockLot(models.Model):
    _inherit = 'stock.lot'
    
    # Weight tracking fields
    initial_weight = fields.Float(
        string='Initial Weight (kg)',
        digits='Product Unit of Measure',
        required=False,
        tracking=True,
        help='Initial weight when serial number was created'
    )
    
    current_weight = fields.Float(
        string='Current Weight (kg)',
        digits='Product Unit of Measure',
        tracking=True,
        help='Current weight after processing'
    )
    
    weight_loss_total = fields.Float(
        string='Total Weight Loss (kg)',
        compute='_compute_weight_loss',
        store=True,
        digits='Product Unit of Measure'
    )
    
    weight_loss_percentage = fields.Float(
        string='Weight Loss %',
        compute='_compute_weight_loss',
        store=True,
        digits=(5, 2)
    )
    
    weight_history_ids = fields.One2many(
        'stock.lot.weight.history',
        'lot_id',
        string='Weight History'
    )
    
    production_ids = fields.One2many(
        'mrp.production',
        'lot_producing_id',
        string='Productions'
    )
    
    @api.depends('initial_weight', 'current_weight')
    def _compute_weight_loss(self):
        for lot in self:
            if lot.initial_weight > 0:
                lot.weight_loss_total = lot.initial_weight - lot.current_weight
                lot.weight_loss_percentage = (lot.weight_loss_total / lot.initial_weight) * 100
            else:
                lot.weight_loss_total = 0
                lot.weight_loss_percentage = 0
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'current_weight' not in vals and 'initial_weight' in vals:
                vals['current_weight'] = vals['initial_weight']
        return super().create(vals_list)
    
    def update_weight(self, new_weight, reference=None, production_id=None):
        """Update weight and create history record"""
        self.ensure_one()
        
        if new_weight < 0:
            raise ValidationError(_('Weight cannot be negative!'))
        
        old_weight = self.current_weight
        weight_change = old_weight - new_weight
        
        # Create history record
        self.env['stock.lot.weight.history'].create({
            'lot_id': self.id,
            'date': fields.Datetime.now(),
            'old_weight': old_weight,
            'new_weight': new_weight,
            'weight_change': weight_change,
            'reference': reference or '',
            'production_id': production_id,
            'user_id': self.env.user.id,
        })
        
        self.current_weight = new_weight
        
        return True


class StockLotWeightHistory(models.Model):
    _name = 'stock.lot.weight.history'
    _description = 'Stock Lot Weight History'
    _order = 'date desc'
    
    lot_id = fields.Many2one(
        'stock.lot',
        string='Serial Number',
        required=True,
        ondelete='cascade'
    )
    
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now
    )
    
    old_weight = fields.Float(
        string='Previous Weight (kg)',
        digits='Product Unit of Measure'
    )
    
    new_weight = fields.Float(
        string='New Weight (kg)',
        digits='Product Unit of Measure'
    )
    
    weight_change = fields.Float(
        string='Weight Change (kg)',
        digits='Product Unit of Measure'
    )
    
    reference = fields.Char(
        string='Reference'
    )
    
    production_id = fields.Many2one(
        'mrp.production',
        string='Production Order'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User'
    )