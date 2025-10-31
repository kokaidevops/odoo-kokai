from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = 'purchase.request.line.make.purchase.order'

    @api.model
    def _prepare_purchase_order_line(self, po, item):
        res = super()._prepare_purchase_order_line(po, item)
        res['brand_id'] = item.line_id.batch_id.id
        return res


class PurchaseRequestLineMakePurchaseOrderItem(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order.item"

    brand_id = fields.Many2one('product.brand', string='Brand', related='line_id.brand_id', readonly=False)