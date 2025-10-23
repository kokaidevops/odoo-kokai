from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductDatasheet(models.Model):
    _name = 'product.datasheet'
    _description = 'Product Datasheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    date = fields.Date('Date', default=fields.Date.today())
    line_id = fields.Many2one('sale.order.line', string='Line')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Text('Description')
    line_ids = fields.One2many('datasheet.line', 'sheet_id', string='Specification')
    variant_ids = fields.One2many('datasheet.attribute', 'sheet_id', string='Variant')

    @api.onchange('product_tmpl_id')
    def generate_attribute(self):
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
            self.line_id.write({ 'product_id': product.id, 'product_template_id': self.product_tmpl_id.id })
            return {
                'name': 'Datasheet',
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


class DatasheetLine(models.Model):
    _name = 'datasheet.line'
    _description = 'Datasheet Line'

    sheet_id = fields.Many2one('product.datasheet', string='Sheet', required=True, ondelete='cascade')
    name = fields.Char('Component')
    value = fields.Char('Value')


class DatasheetAttribute(models.Model):
    _name = 'datasheet.attribute'
    _description = 'Datasheet Attribute'

    sheet_id = fields.Many2one('product.datasheet', string='Sheet', required=True, ondelete='cascade')
    attribute_id = fields.Many2one('product.attribute', string='Attribute', required=True)
    value_id = fields.Many2one('product.attribute.value', string='Value', domain="[('id', 'in', possible_value_ids)]")
    possible_value_ids = fields.Many2many(comodel_name="product.attribute.value", compute="_compute_possible_value_ids", readonly=True)

    @api.depends("attribute_id")
    def _compute_possible_value_ids(self):
        for record in self:
            attribute = record.sheet_id.product_tmpl_id.attribute_line_ids.filtered( lambda x: x.attribute_id == record.attribute_id )
            record.possible_value_ids = attribute.value_ids.sorted()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    datasheet_id = fields.Many2one('product.datasheet', string='Datasheet')

    def action_show_datasheet(self):
        self.ensure_one()
        return {
            'name': 'Datasheet',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'product.datasheet',
            'context': dict(
                self._context, 
                active_ids=self.ids, 
                default_product_tmpl_id=self.product_template_id.id, 
                default_product_id=self.product_id.id,
                default_line_id=self.id,
            ),
            'type': 'ir.actions.act_window',
            'target': 'new',
        }