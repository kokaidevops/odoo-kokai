from num2words import num2words
from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_amount_to_words(self):
        self.ensure_one()
        return num2words(self.amount_total, to='currency', lang='id')