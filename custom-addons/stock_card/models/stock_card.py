from odoo import _, api, fields, models
import logging


_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def refresh_stock_card(self):
        for record in self:
            for product in record.mapped('product_variant_ids'):
                query = f"DELETE FROM stock_card_line WHERE product_id={product.id}"
                self.env.cr.execute(query)
                query = f"UPDATE stock_card_line SET has_count=False WHERE product_id={product.id}"
                self.env.cr.execute(query)

    def generate_stock_card(self):
        for record in self:
            for product in record.mapped('product_variant_ids'):
                self.env['stock.card.line'].process(product.id)

    def action_view_stock_card(self):
        self.generate_stock_card()
        action = self.env.ref('stock_card.stock_card_line_action').sudo().read()[0]
        action['domain'] = [('product_tmpl_id', '=', self.id)]
        return action

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def refresh_stock_card(self):
        for record in self:
            query = f"DELETE FROM stock_card_line WHERE product_id={record.id}"
            self.env.cr.execute(query)
            query = f"UPDATE stock_card_line SET has_count=False WHERE product_id={record.id}"
            self.env.cr.execute(query)

    def generate_stock_card(self):
        for record in self:
            self.env['stock.card.line'].process(record.id)

    def action_view_stock_card(self):
        self.generate_stock_card()
        action = self.env.ref('stock_card.stock_card_line_action').sudo().read()[0]
        action['domain'] = [('product_id', '=', self.id)]
        return action


class StockMove(models.Model):
    _inherit = 'stock.move'

    has_count = fields.Boolean('Has Count', readonly=True, default=False)


class StockCardLine(models.Model):
    _name = 'stock.card.line'
    _description = 'Stock Card Line'

    name = fields.Char('Name', default='New', required=True)
    date = fields.Date('Date')
    description = fields.Char('Description')
    information = fields.Char('Information')
    loc_id = fields.Many2one('stock.location', string='Location', required=True)
    location_id = fields.Many2one('stock.location', string='Source Location', required=True)
    location_dest_id = fields.Many2one('stock.location', string='Location Destination', required=True)
    picking_id = fields.Many2one('stock.picking', string='Picking')
    product_id = fields.Many2one('product.product', string='Product')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
    init_qty = fields.Float('Initial Qty')
    incoming_qty = fields.Float('Incoming Qty')
    output_qty = fields.Float('Output Qty')
    final_qty = fields.Float('Final Qty')
    move_id = fields.Many2one('stock.move', string='Move', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    def convert_uom(self, init, to, value):
        if to.uom_type == 'bigger' or init.uom_type == 'smaller':
            value = value*to.ratio
        if to.uom_type == 'smaller' or init.uom_type == 'bigger':
            value = value/to.ratio
        return value

    def define_information(self, move=False):
        information = move.reference
        if move.location_id.usage == 'supplier':
            information = 'Purchase Order'
        if move.location_id.usage == 'customer':
            information = 'Return Sale Order'
        if move.location_id.usage == 'internal':
            if move.location_dest_id.usage == 'internal':
                information = 'Internal Transfer'
            elif move.location_dest_id.usage == 'supplier':
                information = 'Return Purchase Order'
            elif move.location_dest_id.usage == 'customer':
                information = 'Sale Order'
            elif move.location_dest_id.usage == 'inventory':
                information = 'Inventory Loss'
            elif move.location_dest_id.usage == 'production':
                information = 'BoM'
        if move.location_id.usage == 'production':
            information = 'Production'
        if move.location_id.usage == 'inventory':
            information = 'Stock Opname'
        return information

    @api.model
    def process(self, product_id):
        product = self.env['product.product'].browse(product_id)
        product_uom = product.uom_id

        moves = self.env['stock.move'].search([
            ('product_id.id', '=', product.id),
            ('has_count', '=', False),
            ('state', '=', 'done'),
        ], order='date ASC, id ASC')

        for move in moves:
            move.write({ 'has_count': True })
            information = ''

            if move.location_id.usage == 'internal':
                loc_id = move.location_id
                description = f"Barang Keluar dari {loc_id.display_name}"
                line = self.env['stock.card.line'].search([
                    ('date', '<=', move.date),
                    ('product_id.id', '=', product.id),
                    ('description', 'in', [f"Barang Keluar dari {loc_id.display_name}", f"Barang Masuk ke {loc_id.display_name}"]),
                ], order="date DESC, id DESC", limit=1)
                init_qty = line.final_qty

                information = self.define_information(move)
                value = self.convert_uom( product_uom, move.product_uom, move.product_uom_qty )

                output_qty = value
                incoming_qty = 0
                final_qty = init_qty + (incoming_qty - output_qty)

            if move.location_dest_id.usage == 'internal':
                loc_id = move.location_dest_id
                description = f"Barang Masuk ke {loc_id.display_name}"
                line = self.env['stock.card.line'].search([
                    ('date', '<=', move.date),
                    ('product_id.id', '=', product.id),
                    ('description', 'in', [f"Barang Keluar dari {loc_id.display_name}", f"Barang Masuk ke {loc_id.display_name}"]),
                ], order="date DESC, id DESC", limit=1)
                init_qty = line.final_qty

                information = self.define_information(move)
                value = self.convert_uom( product_uom, move.product_uom, move.product_uom_qty )

                output_qty = 0
                incoming_qty = value
                final_qty = init_qty + (incoming_qty - output_qty)

            self.env['stock.card.line'].sudo().create({
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_id': product.id,
                'date': move.date,
                'information': information,
                'description': description,
                'loc_id': loc_id.id,
                'location_id': move.location_id.id,
                'location_dest_id': move.location_dest_id.id,
                'picking_id': move.picking_id.id,
                'init_qty': init_qty,
                'output_qty': output_qty,
                'incoming_qty': incoming_qty,
                'final_qty': final_qty,
                'move_id': move.id,
            })