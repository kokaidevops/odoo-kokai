from odoo import _, api, fields, models, http
from odoo.tools.mail import html2plaintext
from odoo.exceptions import ValidationError

import base64
import requests
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_print_py3o(self):
        return self.env.ref("report_sale_order.action_report_sale_order_py3o").report_action(self, config=False)

    def action_print_inquiry_py3o(self):
        return self.env.ref("report_sale_order.action_report_inquiry__py3o").report_action(self, config=False)

    def action_print_contract_py3o(self):
        return self.env.ref("report_sale_order.action_report_contract__py3o").report_action(self, config=False)

    def _get_director(self):
        self.ensure_one()
        director = self.env.company.director_id.name
        return director

    def currency_format(self, number=0):
        res = ""
        for rec in self:
            if rec.currency_id.position == "before":
                res = rec.currency_id.symbol + " {:20,.0f}".format(number)
            else:
                res = "{:20,.0f} ".format(number) + rec.currency_id.symbol
        return res

    def py3o_get_note(self):
        data = []
        if self.note:
            notes = html2plaintext(self.note)
            record = notes.splitlines()
            for line in record:
                data.append(
                    {
                        "name": line,
                    }
                )
            return data


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_string_ability(self):
        for record in self:
            ability = dict(self._fields['ability'].selection).get(record.ability)
            return ability