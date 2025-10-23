from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

CODE_SOURCE = {
    'tender': 'a',
    'service': 'b',
    'retail': 'c',
}


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    query_ids = fields.One2many('price.query', 'opportunity_id', string='Price Query')
    query_count = fields.Integer('Query Count', compute='_compute_query_count', store=True)
    @api.depends('query_ids')
    def _compute_query_count(self):
        for record in self:
            record.query_count = len(record.query_ids)

    def action_show_price_query(self):
        self.ensure_one()
        if self.query_count == 0:
            return
        queries = self.env['price.query'].search([ ('opportunity_id', '=', self.id) ])
        action = (self.env.ref('price_query.price_query_action').sudo().read()[0])
        action['domain'] = [('id', '=', queries.ids)]
        return action

    def action_stage_price_query(self):
        self.ensure_one()
        self.write({ 'stage_id': self.env.ref('price_query.crm_stage_data_price_query').id })

    def generate_price_query(self):
        self.ensure_one()
        self.env['price.query'].create({
            'opportunity_id': self.id,
            'user_id': self.env.user.id,
        })

    def _prepare_order_value(self):
        self.ensure_one()
        inquiry_number = self.env['ir.sequence'].sudo().next_by_code('inquiry.review')
        return {
            'name': inquiry_number,
            'partner_id': self.partner_id.id,
            'source': self.source,
            'frk_type': CODE_SOURCE[self.source],
            'tag_ids': self.tag_ids.ids,
            'opportunity_id': self.id,
            'revision': self.inquiry_count+1,
            'inquiry_date': fields.Date.today(),
            'state': 'inquiry',
            'team_id': self.team_id.id,
            'department_team_id': self.sm_team_id.id,
            'account_executive_id': self.user_id.id,
            'user_id': self.salesperson_id.id,
            'manager_id': self.team_id.user_id.id,
            'scope': self.name,
            'due_date': self.date_deadline,
            'inquiry_number': inquiry_number,
        }
    
    def _prepare_order_line(self, order_id, line):
        self.ensure_one()
        return {
            'order_id': order_id,
            'product_template_id': line.product_tmpl_id.id,
            'product_id': line.product_id.id,
            'product_uom_qty': line.qty,
            'product_uom': line.uom_id.id,
            'price_unit': line.price_unit,
            'pq_line_id': line.id,
            'ability': 'indent',
        }

    def process_price_query(self):
        self.ensure_one()
        if self.query_ids[0].inquiry_id:
            return
        val = self._prepare_order_value()
        order = self.env['sale.order'].create(val)
        if not order:
            raise ValidationError("Can't Process Price Query! Please Contact Administrator.")
        order.generate_project_requirements()
        for line in self.query_ids[0].line_ids:
            if line.state == 'approved':
                val_line = self._prepare_order_line(order.id, line)
                order_line = self.env['sale.order.line'].create(val_line)
                line.write({ 'line_id': order_line.id, 'stage_id': self.stage_id.id })
        self.query_ids[0].write({ 'inquiry_id': order.id })
        self.write({ 'order_ids': [(4, order.id)] })


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    query_ids = fields.One2many('price.query', 'inquiry_id', string='Price Query')
    query_count = fields.Integer('Query Count', compute='_compute_query_count', store=True)
    @api.depends('query_ids')
    def _compute_query_count(self):
        for record in self:
            record.query_count = len(record.query_ids)

    def action_show_price_query(self):
        self.ensure_one()
        if self.query_count == 0:
            return
        action = (self.env.ref('price_query.price_query_action').sudo().read()[0])
        action['domain'] = [('id', '=', self.query_ids.ids)]
        return action

    def generate_price_query(self):
        for record in self:
            val = {
                'inquiry_id': record.id,
                'user_id': self.env.user.id,
                'opportunity_id': record.opportunity_id.id,
            }
            record.write({ 'query_ids': [(0, 0, val)] })
            record.opportunity_id.action_stage_price_query()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    pq_line_id = fields.Many2one('price.query.line', string='PQ Line')

    def action_show_datasheet_pq(self):
        self.ensure_one()
        if not self.pq_line_id:
            raise ValidationError(_("Line is not Generating from PQ, so this haven't BoM from PQ Line"))
        view = self.env.ref("price_query.show_datasheet_view_form")
        return {
            "name": _("Datasheet"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "price.query.line",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.pq_line_id.id,
            "context": dict(self.env.context),
        }
    
    def _prepare_data_manufacture_order(self):
        self.ensure_one()
        val = super(SaleOrderLine, self)._prepare_data_manufacture_order()
        if self.pq_line_id:
            val['pq_line_id'] = self.pq_line_id.id
            val['source'] = 'pq'
        return val