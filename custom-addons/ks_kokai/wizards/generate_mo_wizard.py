from odoo import models, fields, api

class GenerateMOWizard(models.TransientModel):
    _name = 'generate.mo.wizard'
    _description = 'Generate Manufacturing Orders'
    
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        required=True
    )
    
    line_ids = fields.One2many(
        'generate.mo.wizard.line',
        'wizard_id',
        string='Products to Manufacture'
    )
    
    generation_method = fields.Selection([
        ('all', 'All Products'),
        ('selected', 'Selected Products Only')
    ], string='Generation Method', default='all')
    
    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        """Populate lines from SO"""
        if self.sale_order_id:
            lines = []
            for so_line in self.sale_order_id.order_line:
                if so_line.product_id.bom_ids:
                    lines.append((0, 0, {
                        'product_id': so_line.product_id.id,
                        'quantity': so_line.product_uom_qty,
                        'so_line_id': so_line.id,
                        'has_template': bool(so_line.product_id.category_template_id)
                    }))
            self.line_ids = lines
    
    def action_generate_mos(self):
        """Generate MOs based on selection"""
        self.ensure_one()
        
        if self.generation_method == 'all':
            self.sale_order_id.action_generate_manufacturing_orders()
        else:
            # Generate only for selected lines
            for line in self.line_ids.filtered('is_selected'):
                self.sale_order_id._generate_mo_by_levels(line.so_line_id)
        
        return self.sale_order_id.action_view_manufacturing_orders()

class GenerateMOWizardLine(models.TransientModel):
    _name = 'generate.mo.wizard.line'
    _description = 'Generate MO Wizard Line'
    
    wizard_id = fields.Many2one('generate.mo.wizard', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity')
    so_line_id = fields.Many2one('sale.order.line', string='SO Line')
    has_template = fields.Boolean(string='Has Template')
    is_selected = fields.Boolean(string='Select', default=True)