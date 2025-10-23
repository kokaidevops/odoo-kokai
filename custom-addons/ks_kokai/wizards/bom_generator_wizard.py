from odoo import models, fields, api

class BomGeneratorWizard(models.TransientModel):
    _name = 'bom.generator.wizard'
    _description = 'BOM Generator Wizard'
    
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        required=True,
        domain=[('auto_generate_bom', '=', True)]
    )
    
    attribute_line_ids = fields.One2many(
        'bom.generator.line',
        'wizard_id',
        string='Attribute Configuration'
    )
    
    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        if self.product_tmpl_id:
            lines = []
            for attr_line in self.product_tmpl_id.attribute_line_ids:
                for value in attr_line.value_ids:
                    lines.append((0, 0, {
                        'attribute_id': attr_line.attribute_id.id,
                        'value_id': value.id,
                        'component_id': False,
                        'quantity': 1.0,
                    }))
            self.attribute_line_ids = lines
    
    def generate_boms(self):
        """Generate BOMs based on configuration"""
        self.product_tmpl_id.generate_variant_boms()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generated BOMs',
            'res_model': 'mrp.bom',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.product_tmpl_id.id)],
        }


class BomGeneratorLine(models.TransientModel):
    _name = 'bom.generator.line'
    _description = 'BOM Generator Line'
    
    wizard_id = fields.Many2one('bom.generator.wizard', required=True)
    attribute_id = fields.Many2one('product.attribute', string='Attribute', required=True)
    value_id = fields.Many2one('product.attribute.value', string='Value', required=True)
    component_id = fields.Many2one('product.product', string='Component')
    quantity = fields.Float(string='Quantity', default=1.0)