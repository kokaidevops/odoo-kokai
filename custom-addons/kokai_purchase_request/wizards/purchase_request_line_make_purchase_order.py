from odoo import _, api, fields, models


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = 'purchase.request.line.make.purchase.order'

    @api.model
    def _prepare_item(self, line):
        res = super()._prepare_item(line)
        res['request_state'] = line.request_state
        return res

    @api.model
    def get_items(self, request_line_ids):
        res = super().get_items(request_line_ids)
        res_filtered = list(filter(lambda line: not line[2]['request_state'] == 'rejected', res))
        return res_filtered


class PurchaseRequestLineMakePurchaseOrderItem(models.TransientModel):
    _inherit = 'purchase.request.line.make.purchase.order.item'

    request_state = fields.Char('Request State', readonly=True)