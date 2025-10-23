from odoo import _, api, fields, models


class MRPBom(models.Model):
    _inherit = 'mrp.bom'

    name = fields.Char('Name', compute='_compute_name')

    @api.depends('product_id', 'product_id.default_code')
    def _compute_name(self):
        for record in self:
            record.name = "BOM-%s" % (record.product_id.default_code)