from odoo import _, api, fields, models
import logging


_logger = logging.getLogger(__name__)



class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    code = fields.Char('Code')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hs_code = fields.Char('HS Code')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    hs_code = fields.Char('HS Code', related='product_tmpl_id.hs_code', store=True)
    attribute_code = fields.Char('Attribute Code', compute='_compute_attribute_code', store=True)
    default_code = fields.Char('Internal Reference', compute='_compute_default_code', store=True, index=True)

    @api.depends('product_template_attribute_value_ids', 'product_template_attribute_value_ids.product_attribute_value_id.code')
    def _compute_default_code(self):
        for record in self:
            code = ''
            for attribute in record.product_template_attribute_value_ids:
                code += attribute.product_attribute_value_id.code or ''
            record.default_code = code

    @api.depends('product_template_attribute_value_ids')
    def _compute_attribute_code(self):
        for record in self:
            record.attribute_code = ''.join([attribute.product_attribute_value_id.code or '' for attribute in record.product_template_attribute_value_ids])

    def _generate_attribute_code(self):
        self.ensure_one()
        attribute_code = ''.join([attribute.product_attribute_value_id.code or '' for attribute in self.product_template_attribute_value_ids])
        _logger.warning(attribute_code)
        self.write({ 'attribute_code': attribute_code })
        return attribute_code
