from odoo import _, api, fields, models, http
from odoo.tools.mail import html2plaintext
from odoo.exceptions import ValidationError

import base64
import requests
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    approver_id = fields.Many2one('res.users','Approver', copy=False, tracking=True)
    price_term = fields.Selection([
        ('include', 'Include PPN'),
        ('exclude', 'Exclude PPN'),
    ], string='Price Term', default='include', tracking=True)
    payment_terms = fields.Char('Payment Terms', tracking=True)
    contactperson_id = fields.Many2one('res.partner', string='Contact Person', tracking=True)
    received_id = fields.Many2one('res.users', string='Received By', tracking=True)

    def action_print_py3o(self):
        return self.env.ref("report_purchase_order.action_report_purchase_order_py3o").report_action(self, config=False)

    def _get_string_price_term(self):
        self.ensure_one()
        price_term = dict(self._fields['price_term'].selection).get(self.price_term)
        return price_term

    def currency_format(self, number=0):
        res = ""
        for rec in self:
            if rec.currency_id.position == "before":
                res = rec.currency_id.symbol + "{:20,.0f}".format(number)
            else:
                res = "{:20,.0f}".format(number) + rec.currency_id.symbol
        return res

    def _amount_discount(self):
        for order in self:
            amount_discount = 0.0
            for line in order.order_line:
                amount_discount += ((line.discount/100)*line.product_qty*line.price_unit)
            return amount_discount

    def py3o_get_note(self):
        data = []
        if self.notes:
            notes = html2plaintext(self.notes)
            record = notes.splitlines()
            for line in record:
                data.append(
                    {
                        "name": line,
                    }
                )
        return data


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    size = fields.Char('Size')

    def _get_uom(self):
        self.ensure_one()
        if self.uom_invoice_id != self.product_uom:
            return f"{self.uom_invoice_id.name} [{self.uom_invoice_id.name}={self.product_uom.name}]"
        return self.uom_invoice_id.name