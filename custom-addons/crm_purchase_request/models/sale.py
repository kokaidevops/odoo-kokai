from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def generate_purchase_request(self):
        self.ensure_one()
        