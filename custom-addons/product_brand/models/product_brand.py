from odoo import _, api, fields, models


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand'
    
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
    ], string='Type')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_brand_per_so_line = fields.Boolean('Brand', implied_group='product_brand.group_brand_per_so_line')
    group_brand_per_po_line = fields.Boolean('Brand', implied_group='product_brand.group_brand_per_po_line')
    group_brand_per_sm_line = fields.Boolean('Brand', implied_group='product_brand.group_brand_per_sm_line', default=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    brand_id = fields.Many2one('product.brand', string='Brand')


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    brand_id = fields.Many2one('product.brand', string='Brand')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    brand_id = fields.Many2one('product.brand', string='Brand')


class StockMove(models.Model):
    _inherit = 'stock.move'

    brand_id = fields.Many2one('product.brand', string='Brand')


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    brand_id = fields.Many2one('product.brand', string='Brand')