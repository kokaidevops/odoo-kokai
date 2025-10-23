from odoo import models, fields, api
class BOMGenerationWizard(models.TransientModel):
    _name = 'bom.generation.wizard'
    _description = 'BOM Generation Wizard'
    
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
        readonly=True
    )
    
    category_template_id = fields.Many2one(
        'product.category.template',
        string='Category Template',
        required=True
    )
    
    specification_ids = fields.One2many(
        'bom.generation.wizard.spec',
        'wizard_id',
        string='Specifications'
    )
    
    preview_line_ids = fields.One2many(
        'bom.generation.wizard.preview',
        'wizard_id',
        string='BOM Preview'
    )
    
    @api.onchange('category_template_id')
    def _onchange_category_template_id(self):
        """Load specifications from product"""
        if self.category_template_id and self.product_tmpl_id:
            # Create specification lines
            specs = []
            for attr_line in self.product_tmpl_id.attribute_line_ids:
                specs.append((0, 0, {
                    'attribute_id': attr_line.attribute_id.id,
                    'value_ids': [(6, 0, attr_line.value_ids.ids)],
                }))
            self.specification_ids = specs
            
            # Generate preview
            self._generate_preview()
    
    def _generate_preview(self):
        """Generate BOM preview"""
        if not self.category_template_id:
            return
        
        preview_lines = []
        for template_line in self.category_template_id.template_line_ids:
            preview_lines.append((0, 0, {
                'sequence': template_line.sequence,
                'level': template_line.level,
                'name': template_line.name,
                'category': template_line.category,
                'quantity_formula': template_line.quantity_formula,
                'calculated_qty': 1.0,  # Default
            }))
        
        self.preview_line_ids = preview_lines
    
    def action_generate_bom(self):
        """Generate actual BOM"""
        self.ensure_one()
        
        # Set category template on product
        self.product_tmpl_id.category_template_id = self.category_template_id
        
        # Generate BOM
        bom = self.product_tmpl_id._generate_bom_structure(
            self.product_tmpl_id._get_product_specifications()
        )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'res_id': bom.id,
            'view_mode': 'form',
            'target': 'current',
        }


class BOMGenerationWizardSpec(models.TransientModel):
    _name = 'bom.generation.wizard.spec'
    _description = 'BOM Generation Wizard Specification'
    
    # Inverse field untuk One2many relationship
    wizard_id = fields.Many2one(
        'bom.generation.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    attribute_id = fields.Many2one(
        'product.attribute',
        string='Attribute',
        required=True
    )
    
    value_ids = fields.Many2many(
        'product.attribute.value',
        string='Values',
        domain="[('attribute_id', '=', attribute_id)]"
    )
    
    selected_value_id = fields.Many2one(
        'product.attribute.value',
        string='Selected Value',
        domain="[('attribute_id', '=', attribute_id)]"
    )

class BOMGenerationWizardPreview(models.TransientModel):
    _name = 'bom.generation.wizard.preview'
    _description = 'BOM Generation Wizard Preview Line'
    
    # Inverse field untuk One2many relationship
    wizard_id = fields.Many2one(
        'bom.generation.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(string='Sequence', default=10)
    level = fields.Integer(string='Level', default=1)
    name = fields.Char(string='Component Name', required=True)
    category = fields.Selection([
        ('raw', 'Raw Material'),
        ('processed', 'Processed/WIP')
    ], string='Category', required=True)
    quantity_formula = fields.Char(string='Quantity Formula', default='1')
    calculated_qty = fields.Float(string='Calculated Qty', default=1.0)
    component_type = fields.Selection([
        ('body', 'Body'),
        ('trim', 'Trim'),
        ('fastener', 'Fasteners'),
        ('sealing', 'Sealing'),
        ('accessory', 'Accessories'),
        ('consumable', 'Consumables'),
        ('other', 'Other')
    ], string='Type')
    template_line_id = fields.Many2one(
        'product.category.template.line',
        string='Template Line Reference'
    )