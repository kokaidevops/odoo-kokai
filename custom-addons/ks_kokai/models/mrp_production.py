from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    # Weight tracking fields
    total_input_weight = fields.Float(
        string='Total Input Weight (kg)',
        compute='_compute_weights',
        store=True,
        digits='Product Unit of Measure'
    )
    
    total_output_weight = fields.Float(
        string='Total Output Weight (kg)',
        compute='_compute_weights',
        store=True,
        digits='Product Unit of Measure'
    )
    
    actual_weight_loss = fields.Float(
        string='Actual Weight Loss (kg)',
        compute='_compute_weights',
        store=True,
        digits='Product Unit of Measure'
    )
    
    actual_weight_loss_percentage = fields.Float(
        string='Actual Weight Loss (%)',
        compute='_compute_weights',
        store=True,
        digits=(5, 2)
    )
    
    expected_weight_loss = fields.Float(
        related='bom_id.expected_weight_loss',
        string='Expected Weight Loss (%)',
        readonly=True
    )
    
    weight_variance = fields.Float(
        string='Weight Variance (%)',
        compute='_compute_weights',
        store=True,
        digits=(5, 2)
    )
    
    is_weight_variance_high = fields.Boolean(
        string='High Weight Variance',
        compute='_compute_weights',
        store=True
    )
    
    weight_tracking_line_ids = fields.One2many(
        'mrp.production.weight.line',
        'production_id',
        string='Weight Tracking'
    )
    
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        readonly=True
    )
    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Sales Order Line',
        readonly=True
    )
    level = fields.Integer(
        string='Manufacturing Level',
        help='Manufacturing level from template'
    )
    template_line_id = fields.Many2one(
        'product.category.template.line',
        string='Template Line Reference'
    )
    parent_mo_ids = fields.Many2many(
        'mrp.production',
        'mrp_production_parent_rel',
        'child_id',
        'parent_id',
        string='Parent MOs',
        help='Manufacturing orders that must be completed before this one'
    )
    child_mo_ids = fields.Many2many(
        'mrp.production',
        'mrp_production_parent_rel',
        'parent_id',
        'child_id',
        string='Child MOs',
        help='Manufacturing orders that depend on this one'
    )
    operation_name = fields.Char(string='Operation Name')
    operation_type = fields.Selection([
        ('machining', 'Machining'),
        ('assembly', 'Assembly'),
        ('welding', 'Welding'),
        ('testing', 'Testing'),
        ('finishing', 'Finishing'),
        ('other', 'Other')
    ], string='Operation Type')

    bom_series_id = fields.Many2one(
        'product.bom.series',
        string='BOM Series',
        help='Related BOM series entry for production planning'
    )
    production_level = fields.Integer(
        string='Production Level',
        help='Level in the BOM hierarchy (1=final product, 2=sub-assembly, etc.)'
    )
    production_sequence = fields.Integer(
        string='Production Sequence',
        help='Sequence number for manufacturing order execution'
    )
    
    # Related fields for easier access
    bom_series_level = fields.Integer(
        related='bom_series_id.level',
        string='Series Level',
        store=True
    )
    parent_bom_series_id = fields.Many2one(
        related='bom_series_id.parent_series_id',
        string='Parent BOM Series',
        store=True
    )
    
    # Sale order tracking
    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order Line',
        help='Sale order line that triggered this production'
    )
    sale_order_id = fields.Many2one(
        related='sale_line_id.order_id',
        string='Sale Order',
        store=True
    )
    
    @api.depends('bom_series_id', 'production_level')
    def _compute_display_name(self):
        """Enhance display name with level information"""
        for record in self:
            name = record.name or 'New'
            if record.production_level:
                name = f"[L{record.production_level}] {name}"
            record.display_name = name
    
    def action_view_bom_series(self):
        """View related BOM series"""
        self.ensure_one()
        if not self.bom_series_id:
            return
            
        return {
            'name': 'BOM Series',
            'type': 'ir.actions.act_window',
            'res_model': 'product.bom.series',
            'res_id': self.bom_series_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def action_view_related_productions(self):
        """View all productions from same BOM series"""
        self.ensure_one()
        if not self.bom_series_id:
            return
            
        # Find all productions from same product template BOM series
        related_series = self.bom_series_id.product_tmpl_id.bom_series_ids
        related_productions = self.search([
            ('bom_series_id', 'in', related_series.ids)
        ])
        
        return {
            'name': 'Related Productions',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', related_productions.ids)],
            'context': {'group_by': 'production_level'}
        }

    
    @api.constrains('state', 'parent_mo_ids')
    def _check_parent_mo_state(self):
        """Ensure parent MOs are done before confirming this MO"""
        for mo in self:
            if mo.state == 'confirmed':
                incomplete_parents = mo.parent_mo_ids.filtered(
                    lambda p: p.state not in ['done', 'cancel']
                )
                if incomplete_parents:
                    raise ValidationError(
                        _('Cannot confirm MO. Parent MOs must be completed first: %s') 
                        % ', '.join(incomplete_parents.mapped('name'))
                    )
    
    def action_confirm(self):
        """Override to check dependencies"""
        self._check_parent_mo_state()
        return super(MrpProduction, self).action_confirm()
    
    def action_view_parent_mos(self):
        """View parent manufacturing orders"""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_production_action")
        action['domain'] = [('id', 'in', self.parent_mo_ids.ids)]
        return action
    
    def action_view_child_mos(self):
        """View dependent manufacturing orders"""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_production_action")
        action['domain'] = [('id', 'in', self.child_mo_ids.ids)]
        return action

    @api.depends('move_raw_ids.quantity_done', 'move_raw_ids.lot_ids',
                 'qty_produced', 'lot_producing_id')
    def _compute_weights(self):
        for production in self:
            # Calculate input weight
            total_input = 0
            for move in production.move_raw_ids.filtered(lambda m: m.state == 'done'):
                if move.product_id.track_weight_by_serial and move.lot_ids:
                    for lot in move.lot_ids:
                        total_input += lot.current_weight
                else:
                    total_input += move.quantity_done * move.product_id.standard_weight_per_unit
            
            production.total_input_weight = total_input
            
            # Calculate output weight
            if production.lot_producing_id and production.product_id.track_weight_by_serial:
                production.total_output_weight = production.lot_producing_id.current_weight
            else:
                production.total_output_weight = production.qty_produced * production.product_id.standard_weight_per_unit
            
            # Calculate loss
            production.actual_weight_loss = total_input - production.total_output_weight
            
            if total_input > 0:
                production.actual_weight_loss_percentage = (production.actual_weight_loss / total_input) * 100
                production.weight_variance = production.actual_weight_loss_percentage - production.expected_weight_loss
                
                # Check if variance is high
                tolerance = production.product_id.weight_tolerance if production.product_id else 5.0
                production.is_weight_variance_high = (
                    production.weight_variance > tolerance or 
                    production.weight_variance < -tolerance
                )
            else:
                production.actual_weight_loss_percentage = 0
                production.weight_variance = 0
                production.is_weight_variance_high = False
    
    def button_mark_done(self):
        res = super().button_mark_done()
        
        for production in self:
            if production.product_id.track_weight_by_serial and production.lot_producing_id:
                # Update finished product weight
                expected_output_weight = production.total_input_weight * (1 - production.expected_weight_loss / 100)
                
                # Record weight tracking
                for move in production.move_raw_ids.filtered(lambda m: m.lot_ids):
                    for lot in move.lot_ids:
                        self.env['mrp.production.weight.line'].create({
                            'production_id': production.id,
                            'lot_id': lot.id,
                            'product_id': move.product_id.id,
                            'input_weight': lot.current_weight,
                            'move_id': move.id,
                        })
                
                # Update lot weight
                production.lot_producing_id.update_weight(
                    expected_output_weight,
                    reference=f'Production: {production.name}',
                    production_id=production.id
                )
                
                # Create valuation adjustment if needed
                if production.is_weight_variance_high:
                    production._create_weight_variance_entry()
        
        return res
    
    def _create_weight_variance_entry(self):
        """Create accounting entry for weight variance"""
        self.ensure_one()
        
        if not self.bom_id.weight_loss_account_id:
            return
        
        # Calculate variance value
        variance_weight = self.actual_weight_loss - (self.total_input_weight * self.expected_weight_loss / 100)
        variance_value = variance_weight * self.product_id.standard_price
        
        # Check if variance is significant
        if -0.01 < variance_value < 0.01:
            return
        
        # Create journal entry
        move_vals = {
            'journal_id': self.env.ref('stock_account.stock_journal').id,
            'date': fields.Date.today(),
            'ref': f'Weight Variance: {self.name}',
            'line_ids': [
                (0, 0, {
                    'name': f'Weight Variance: {self.name}',
                    'account_id': self.product_id.categ_id.property_stock_valuation_account_id.id,
                    'debit': variance_value if variance_value > 0 else 0,
                    'credit': -variance_value if variance_value < 0 else 0,
                }),
                (0, 0, {
                    'name': f'Weight Variance: {self.name}',
                    'account_id': self.bom_id.weight_loss_account_id.id,
                    'debit': -variance_value if variance_value < 0 else 0,
                    'credit': variance_value if variance_value > 0 else 0,
                }),
            ],
        }
        
        move = self.env['account.move'].create(move_vals)
        move.action_post()


class MrpProductionWeightLine(models.Model):
    _name = 'mrp.production.weight.line'
    _description = 'Production Weight Tracking Line'
    
    production_id = fields.Many2one(
        'mrp.production',
        string='Production',
        required=True,
        ondelete='cascade'
    )
    
    lot_id = fields.Many2one(
        'stock.lot',
        string='Serial Number',
        required=True
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    
    move_id = fields.Many2one(
        'stock.move',
        string='Stock Move'
    )
    
    input_weight = fields.Float(
        string='Input Weight (kg)',
        digits='Product Unit of Measure'
    )
    
    weight_contribution = fields.Float(
        string='Weight Contribution (%)',
        compute='_compute_contribution',
        digits=(5, 2)
    )
    
    @api.depends('input_weight', 'production_id.total_input_weight')
    def _compute_contribution(self):
        for line in self:
            if line.production_id.total_input_weight > 0:
                line.weight_contribution = (line.input_weight / line.production_id.total_input_weight) * 100
            else:
                line.weight_contribution = 0