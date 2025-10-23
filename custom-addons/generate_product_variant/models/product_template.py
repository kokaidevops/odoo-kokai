from odoo import _, api, fields, models
import itertools
from odoo.exceptions import UserError
import logging


_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def generate_product_variant(self):
        for record in self:
            try:
                variants = []
                for line in record.attribute_line_ids:
                    value_ids = []
                    product_tmpl_attr = self.env['product.template.attribute.line'].search([
                        ('product_tmpl_id', '=', record.id),
                        ('attribute_id', '=', line.attribute_id.id),
                    ])
                    for product_attribute_value in line.value_ids:
                        product_template_variant_value_id = self.env['product.template.attribute.value'].search([
                            ('attribute_id', '=', line.attribute_id.id),
                            ('product_attribute_value_id', '=', product_attribute_value.id),
                            ('product_tmpl_id', '=', record.id),
                            ('attribute_line_id', '=', product_tmpl_attr.id),
                        ], limit=1)
                        value_ids.append(product_template_variant_value_id.id)
                    variants.append(value_ids)
                
                for product_template_attribute_value_ids in itertools.product(*variants):
                    vals = {
                        'name': record.name,
                        'product_tmpl_id': record.id,
                        'product_template_attribute_value_ids': [(6, 0, product_template_attribute_value_ids)]
                    }
                    self.env['product.product'].create(vals)

            except UserError as e:
                raise UserError(str(e))
    
    def action_show_wizard_generate_product(self):
        self.ensure_one()
        return {
            'name': 'Generate Product',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'generate.product.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': dict(active_ids=self.ids),
        }