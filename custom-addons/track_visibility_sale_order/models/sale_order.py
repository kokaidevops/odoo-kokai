from odoo import _, api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    name = fields.Char('Order Reference', tracking=True)
    origin = fields.Char('Source Document', tracking=True)
    due_date = fields.Date('Due Date', tracking=True)
    date_order = fields.Datetime('Order Date', tracking=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals):
        lines = super(SaleOrderLine, self).create(vals)
        for line in lines:
            msg = f"A new item, `{line.name}` has been added."
            line.order_id.message_post(body=msg)
        return lines

    def write(self, vals):
        self._log_line_tracking(vals)
        return super(SaleOrderLine, self).write(vals)

    def unlink(self):
        for line in self:
            msg = f"`{line.name}` has been deleted"
            line.order_id.message_post(body=msg)
        return super(SaleOrderLine, self).unlink()

    def _log_line_tracking(self, vals):
        for line in self:
            datum = {}
            if not line.order_id.state == 'cancel':
                for val in vals.keys():
                    field_name = self._fields[val].string
                    datum.update({ field_name: [line[val], vals.get(val)] })
            if datum:
                line.order_id.message_post_with_view('track_visibility_sale_order.track_line_ids', values={'line': line, 'datum': datum})