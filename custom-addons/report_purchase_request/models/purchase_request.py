from odoo import _, api, fields, models, http
from odoo.exceptions import ValidationError

import base64
import requests
import logging
_logger = logging.getLogger(__name__)

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    def action_print_py3o(self):
        _logger.warning("report_purchase_request.action_report_purchase_request_py3o")
        return self.env.ref("report_purchase_request.action_report_purchase_request_py3o").report_action(self, config=False)

    def _get_director(self):
        self.ensure_one()
        director = self.env.company.director_id.name
        return director

    def _get_string_priority(self):
        self.ensure_one()
        priority = dict(self._fields['priority'].selection).get(self.priority)
        return priority

    def _get_string_type(self):
        self.ensure_one()
        type = dict(self._fields['request_type'].selection).get(self.request_type)
        return type


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    def _get_uom(self):
        self.ensure_one()
        if self.uom_invoice_id != self.product_uom_id:
            return f"{self.uom_invoice_id.name} [{self.uom_invoice_id.name}={self.product_uom_id.name}]"
        return self.uom_invoice_id.name