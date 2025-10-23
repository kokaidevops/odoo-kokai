from odoo import _, api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    potential_product = fields.Boolean('Potential Product', default=False, tracking=True)