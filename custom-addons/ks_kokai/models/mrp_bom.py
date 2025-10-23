from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    
    
    @api.depends('theoritical_initial_weight','theoritical_loss_weight')
    def _compute_weight_loss(self):
        for record in self:
            if (record.theoritical_loss_weight > 0) and (record.theoritical_initial_weight > 0):
                record.expected_weight_loss = (record.theoritical_loss_weight / record.theoritical_initial_weight) * 100
                record.potential_loss_weight = record.theoritical_initial_weight - record.theoritical_loss_weight

    expected_weight_loss = fields.Float(
        string='Expected Weight Loss (%)',
        default=0.0,
        compute=_compute_weight_loss,
        help='Expected weight loss percentage during production',
        store=True
        
    )
    
    
    potential_loss_weight = fields.Float(
        string='Potential loss weight (kg)',
        default=0.0,
        compute=_compute_weight_loss,
        store = True

    )
    
    
    
    
    weight_loss_account_id = fields.Many2one(
        'account.account',
        string='Weight Loss Account',
        help='Account for booking weight loss variance'
    )

    theoritical_initial_weight = fields.Float(
        string='Theoritical Initial Weight (kg)',
    )
    
    
    theoritical_loss_weight = fields.Float(
        string='Theoritical_loss_weight (kg)',
    )
    
    series_ids = fields.One2many(
        'product.bom.series',
        'bom_id',
        string='BOM Series'
    )
    production_level = fields.Integer(
        string='Production Level',
        compute='_compute_production_level',
        store=True
    )
    
    @api.depends('series_ids.level')
    def _compute_production_level(self):
        for record in self:
            if record.series_ids:
                record.production_level = min(record.series_ids.mapped('level'))
            else:
                record.production_level = 0    


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    
    weight_contribution = fields.Float(
        string='Weight Contribution (%)',
        default=100.0,
        help='Percentage of weight contribution to finished product'
    )
    
    track_serial_weight = fields.Boolean(
        related='product_id.track_weight_by_serial',
        string='Track Weight'
        
    )