from odoo import _, api, fields, models
from odoo.exceptions import ValidationError,UserError
import logging


_logger = logging.getLogger(__name__)


class GenerateProductWizard(models.TransientModel):
    _name = 'generate.product.wizard'
    _description = 'Generate Product Wizard'
    
    name = fields.Char('Name')
    suggested_name = fields.Char('Suggested Name')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
    product_id = fields.Many2one('product.template', string='Product')
    code = fields.Char('Product Code') #, compute='_compute_code'
    variant_ids = fields.One2many('variant.line', 'wizard_id', string='Line')
    specification_ids = fields.One2many('variant.specification', 'wizard_id', string='Line')
    order_id = fields.Many2one('sale.order', string='Order', readonly=True, required=True)

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


    def action_search_code(self):
        pass

    def _prepare_product_vals(self):
        # Get category and route
        # fg_category = self.env['ir.config_parameter'].sudo().get_param('default_category_finish_goods')
        fg_category = self.env.ref('crm_management.product_category_data_finished_goods').id
        if not fg_category:
            raise UserError(_('Default Finish Goods category not configured!'))
        return {
            'name': self.suggested_name or self.name,
            'default_code': self.code,
            'detailed_type': 'product',
            'sale_ok': True,
            'purchase_ok': True,
            'categ_id': int(fg_category),
            'tracking': 'serial',
            # 'base_product_id' : self.product_tmpl_id.id
        }
    
    def _prepare_order_line_vals(self, product):
        return {
            'order_id': self.order_id.id,
            'product_template_id': product.id,
            'product_id': product.product_variant_id.id,
            'product_uom_qty': 1,
            'product_uom': product.uom_id.id,
            'price_unit': product.list_price,
            'line_state': 'potential',
            'name': product.display_name,
            'ability': 'indent',
        }

    def action_save_and_close(self):
        """Save product and return to caller form"""
        self.ensure_one()
        
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        
        if not active_model or not active_id:
            return {'type': 'ir.actions.act_window_close'}
        
        # Validasi kode internal reference
        if self.code:
            # Check if code already exists
            existing_product = self.env['product.template'].search([
                '|',
                ('default_code', '=', self.code),
                ('product_variant_ids.default_code', '=', self.code)
            ], limit=1)
            
            if existing_product:
                raise UserError(_(
                    'Product with Internal Reference "%s" already exists!\n'
                    'Product: %s'
                ) % (self.code, existing_product.display_name))
        else:
            # Optional: Force code to be required
            raise UserError(_('Internal Reference is required!'))
        
        # Validasi nama produk
        if not self.suggested_name and not self.name:
            raise UserError(_('Product name is required!'))
        
        # Get manufacture route
        manufacture_route = self.env.ref('mrp.route_warehouse0_manufacture', False)
        if not manufacture_route:
            manufacture_route = self.env['stock.location.route'].search([
                ('name', 'ilike', 'Manufacture')
            ], limit=1)
        
        # Create product template
        product_vals = self._prepare_product_vals()
        
        # Add manufacture route if found
        if manufacture_route:
            product_vals['route_ids'] = [(4, manufacture_route.id)]
        
        try:
            product_template = self.env['product.template'].create(product_vals)
            
            # Create attribute selections
            # for var in self.variant_ids:
            #     if var.attribute_id and var.value_id:
            #         self.env['product.template.attribute.selection'].create({
            #             'product_tmpl_id': product_template.id,
            #             'attribute_id': var.attribute_id.id,
            #             'value_id': var.value_id.id,
            #             'name': var.value_id.name,
            #             'code': var.value_id.code if hasattr(var.value_id, 'code') else '',
            #         })

            order_line_vals = self._prepare_order_line_vals(product_template)
            _logger.warning(order_line_vals)
            order_line = self.env['sale.order.line'].create(order_line_vals)
            
            # Show success notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Product "%s" created successfully with code "%s" and added to order line') % (product_template.name, self.code),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'}
                }
            }
            
        except Exception as e:
            raise UserError(_('Error creating product: %s') % str(e))


    def generate_product(self):
        self.ensure_one()
        # try:
        ProductProduct = self.env['product.template']
        # product = ProductProduct._product_find(self.id, self.variant_ids)
        # product = ProductProduct.search_count([('defaut_code','=',self.code)])

        # if not product:
        product_template_attribute_values = self.env['product.template.attribute.value'].browse()
        product_name = ''
        product_code = ''
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
            print(product_attribute_value)
            print(product_attribute_value.name)
            print(product_attribute_value.code)
            product_name = product_name + ' ' + product_attribute_value.name
            product_code = product_code + product_attribute_value.code.strip()
        print(product_name[1:])
        print(product_code)

        self.write({
            'suggested_name': product_name[1:] if product_name else '',
            'name' : product_name[1:] if product_name else '',
            'code': product_code,
            # 'state': 'generated'
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }        

        # product = ProductProduct.create({
        #     'name': self.name,
        #     'product_template_attribute_value_ids': [
        #         (6, 0, product_template_attribute_values.ids)
        #     ],
        # })
        # self.write({ 'product_id': product.id })
        # self.suggested_name = product.name

        # return {
        #     'name': 'Generate Product',
        #     'view_mode': 'form',
        #     'view_id': False,
        #     'res_model': self._name,
        #     'domain': [],
        #     'context': dict(self._context, active_ids=self.ids),
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        #     'res_id': self.id,
        # }
        # except:
        #     raise ValidationError("Can't create Product Variant")


class VariantLine(models.TransientModel):
    _name = 'variant.line'
    _description = 'Variant Line'

    wizard_id = fields.Many2one('generate.product.wizard', string='Generate Product')
    attribute_id = fields.Many2one('product.attribute', string='Attribute', required=True)
    value_id = fields.Many2one('product.attribute.value', string='Value', domain="[('id', 'in', possible_value_ids)]", required=True)
    possible_value_ids = fields.Many2many('product.attribute.value', string='Possible Value', compute='_compute_possible_value_ids', readonly=True)

    @api.depends("attribute_id")
    def _compute_possible_value_ids(self):
        for record in self:
            # This should be unique due to the new constraint added
            attribute = record.wizard_id.product_tmpl_id.attribute_line_ids.filtered(
                lambda x: x.attribute_id == record.attribute_id
            )
            record.possible_value_ids = attribute.value_ids.sorted()


class VariantSpecification(models.TransientModel):
    _name = 'variant.specification'
    _description = 'Variant Specification'

    wizard_id = fields.Many2one('generate.product.wizard', string='Generate Product')
    name = fields.Char('Name')
    value = fields.Char('Value')