from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_pack = fields.Boolean('Is Product Pack?')

    @api.onchange('is_pack')
    def _onchange_is_pack(self):
        for record in self:
                if record.qty_available > 0:
                    raise ValidationError("Can't change product that already has some qty!")


class ProductPack(models.Model):
    _name = 'product.pack'
    _description = 'Product Pack'

    lot_id = fields.Many2one('stock.lot', string='Lot/Serial Numbers')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    name = fields.Char('Name', related='lot_id.product_id.display_name', store=True)
    lot_ids = fields.One2many('stock.lot', 'pack_id', string='Lot/Serial Numbers', domain="[('product_id', '=', product_id), ('pack_id', '=', False)]")
    uom_id = fields.Many2one('uom.uom', string='UoM', related='product_id.uom_id', store=True)
    qty = fields.Float('Qty', compute='_compute_qty', store=True)

    @api.depends('lot_ids')
    def _compute_qty(self):
        for record in self:
            # record.qty = sum([lot.product_qty for lot in record.lot_ids])
            qty = 0
            for lot in record.lot_ids:
                qty += lot.product_qty
                lot.pack_id = record._origin.id
            record.qty = qty


class StockLot(models.Model):
    _inherit = 'stock.lot'

    is_pack = fields.Boolean('Is Product Pack?', related='product_id.is_pack')
    pack_ids = fields.One2many('product.pack', 'lot_id', string='Bundle List')
    pack_id = fields.Many2one('product.pack', string='Bundle')