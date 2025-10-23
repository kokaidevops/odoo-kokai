from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class GenerateProductWizard(models.TransientModel):
    _name = 'generate.product.wizard'
    _description = 'Generate Product Wizard'
    
    name = fields.Char('Name')
    suggested_name = fields.Char('Suggested Name')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
    product_id = fields.Many2one('product.product', string='Product')
    code = fields.Char('Product Code') #, compute='_compute_code'
    variant_ids = fields.One2many('variant.line', 'wizard_id', string='Line')

    @api.onchange('product_tmpl_id')
    def generate_drawing_datasheet(self):
        self.ensure_one()
        self.write({ 'variant_ids': [(5,0,0)] })
        if not self.product_tmpl_id:
            return
        self.write({
            'variant_ids': [(0,0,{
                'attribute_id': attribute.attribute_id.id,
            }) for attribute in self.product_tmpl_id.attribute_line_ids],
        })
    
    def generate_product(self):
        self.ensure_one()
        try:
            ProductProduct = self.env['product.product']
            product = ProductProduct._product_find(self.product_tmpl_id, self.variant_ids)
            if not product:
                product_template_attribute_values = self.env['product.template.attribute.value'].browse()
                for product_attribute_value in self.variant_ids.mapped('value_id'):
                    product_attribute = product_attribute_value.attribute_id
                    existing_attribute_line = (
                        self.product_tmpl_id.attribute_line_ids.filtered(
                            lambda l: l.attribute_id == product_attribute
                        )
                    )
                    product_template_attribute_values |= (
                        existing_attribute_line.product_template_value_ids.filtered(
                            lambda v: v.product_attribute_value_id == product_attribute_value
                        )
                    )
                product = ProductProduct.create({
                    'name': self.product_tmpl_id.name,
                    'product_tmpl_id': self.product_tmpl_id.id,
                    'product_template_attribute_value_ids': [
                        (6, 0, product_template_attribute_values.ids)
                    ],
                })
            self.write({ 'product_id': product.id })
            return {
                'name': 'Generate Product',
                'view_mode': 'form',
                'view_id': False,
                'res_model': self._name,
                'domain': [],
                'context': dict(self._context, active_ids=self.ids),
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': self.id,
            }
        except Exception as e:
            raise ValidationError(f"Can't create Product Variant, {e}")


class VariantLine(models.TransientModel):
    _name = 'variant.line'
    _description = 'Variant Line'

    wizard_id = fields.Many2one('generate.product.wizard', string='Generate Product')
    attribute_id = fields.Many2one('product.attribute', string='Attribute', required=True)
    value_id = fields.Many2one('product.attribute.value', string='Value', domain="[('attribute_id', '=', attribute_id)]")