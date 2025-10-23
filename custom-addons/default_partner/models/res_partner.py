from odoo import _, api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_default = fields.Boolean('Is Default')

    def set_is_vendor(self):
        for partner in self:
            partner.write({ 'customer_rank': 1 })

    def set_is_customer(self):
        for partner in self:
            partner.write({ 'supplier_rank': 1 })