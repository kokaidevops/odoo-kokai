from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import logging


_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    bundle_ids = fields.One2many('purchase.order.line.bundle', 'line_id', string='Bundle')

    def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking)
        if not self.product_id.is_pack or not self.bundle_ids:
            return res
        price_unit = self._get_stock_move_price_unit()
        parent_res = {
            'propagate_cancel': res[0]['propagate_cancel'], 
            'product_packaging_id': res[0]['product_packaging_id'], 
            'sequence': res[0]['sequence'], 
        }
        for item in self.bundle_ids:
            template = {
                'name': item.product_id.name or '', 
                'product_id': item.product_id.id, 
                'product_uom': item.uom_id.id, 
                'date': self.order_id.date_order, 
                'date_deadline': self.date_planned, 
                'location_id': self.order_id.partner_id.property_stock_supplier.id,
                'location_dest_id': self.order_id._get_destination_location(),
                'picking_id': picking.id,
                'partner_id': self.order_id.dest_address_id.id,
                'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
                'state': 'draft', 
                'purchase_line_id': self.id,
                'company_id': self.order_id.company_id.id,
                'price_unit': price_unit,
                'picking_type_id': self.order_id.picking_type_id.id,
                'group_id': self.order_id.group_id.id,
                'origin': self.order_id.name,
                'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
                'description_picking': item.product_id.name or '', 
                'propagate_cancel': parent_res['propagate_cancel'], 
                'product_packaging_id': parent_res['product_packaging_id'], 
                'sequence': parent_res['sequence'], 
                'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            }
            diff_quantity = item.qty_uom
            if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
                template['product_uom_qty'] = diff_quantity * self.product_qty
                res.append(template)
        return res

    def action_show_bundle(self):
        self.ensure_one()
        view = self.env.ref("product_bundle_pack.purchase_order_line_view_form_bundle")
        ctx = dict( self.env.context )
        return {
            "name": _("PO Line Bundle"),
            "view_mode": "form",
            "view_id": False,
            "res_model": "purchase.order.line",
            "views": [(view.id, "form")],
            "context": ctx,
            "type": "ir.actions.act_window",
            "target": "new",
            "res_id": self.id,
        }


class PurchaseOrderLineBundle(models.Model):
    _name = 'purchase.order.line.bundle'
    _description = 'Purchase Order Line Bundle'

    line_id = fields.Many2one('purchase.order.line', string='Line', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product')
    qty_uom = fields.Float(string='Quantity', required=True, default=1.0)
    uom_id = fields.Many2one(related='product_id.uom_id' , string="Unit of Measure", readonly="1")
    name = fields.Char(related='product_id.name', readonly="1")