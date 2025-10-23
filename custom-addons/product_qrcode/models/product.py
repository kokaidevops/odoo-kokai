from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    alias = fields.Char('Alias')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def generate_qrcode(self):
        self.ensure_one()
        try:
            sequence = self.env['ir.sequence'].next_by_code('stock.lot.product')
            return self.env['stock.lot'].create({
                'name': f"{self.product_tmpl_id.alias}{sequence}",
                'product_id': self.id,
                'company_id': self.env.company.id
            }).id
        except:
            raise UserError(f"Failed Generate QR Code for {self.display_name}")