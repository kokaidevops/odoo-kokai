from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = 'purchase.request.line.make.purchase.order'

    supplier_id = fields.Many2one('res.partner', string='Supplier', default=lambda self: self.env.ref('default_partner.res_partner_data_default_partner').id)
    supplier_ids = fields.Many2many('res.partner', string='Supplier', context={'res_partner_search_mode': "supplier"})
    batch_id = fields.Many2one('purchase.order.batch', string='Offering Batch') #, domain=lambda self: self._default_domain_batch())

    # @api.model
    # def _default_domain_batch(self):
    #     return [('request_id', '=', self.env.context.get('active_id'))]

    def make_batch(self):
        try:
            batch = self.batch_id
            request_ids = [(4, request) for request in list(set(self.item_ids.mapped('request_id').ids))]
            if not batch and self.env.context.get('active_id'):
                batch = self.env['purchase.order.batch'].create({
                    'request_ids': request_ids,
                    'user_id': self.env.user.id,
                })
            self.batch_id = batch.id
        except Exception as e:
            raise ValidationError("Failed to create Offering Batch: %s" % str(e))
        for supplier in self.supplier_ids:
            self.supplier_id = supplier.id
            self.make_purchase_order()

    def _prepare_purchase_order(self, picking_type, group_id, company, origin):
        data = super()._prepare_purchase_order(picking_type, group_id, company, origin)
        data['batch_id'] = self.batch_id.id if self.batch_id else False
        return data