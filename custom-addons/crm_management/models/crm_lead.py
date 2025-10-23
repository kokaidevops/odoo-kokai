from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    def _prepare_value_analytic_account(self, record, frk_type):
        self.ensure_one()
        return {
            'name': f"Budget {frk_type}",
            'partner_id': record.partner_id.id,
            'code': record.name,
            'plan_id': self.env.ref('crm_management.account_analytic_plan_data_project').id,
        }

    def _generate_analytic_account(self, record, frk_type='FRK'):
        self.ensure_one()
        value = self._prepare_value_analytic_account(record, frk_type)
        analytic_acc = self.env['account.analytic.account'].create(value)
        self.write({ 'analytic_account_id': analytic_acc.id })
        return analytic_acc

    @api.model_create_multi
    def create(self, vals):
        # pre create
        for val in vals:
            if 'name' not in val or val.get('name') == 'New':
                val['name'] = self.env['ir.sequence'].next_by_code('crm.lead')
        res = super(CRMLead, self).create(vals)
        # post create
        for record in res:
            self.env['stage.history'].sudo().create({
                'opportunity_id': record._origin.id,
                'old_stage_id': False,
                'stage_id': self.env.ref('crm_management.crm_stage_data_lead').id,
                'reason': 'Create Lead',
                'user_id': self.env.user.id,
                'company_id': self.env.company.id,
                'date': fields.Datetime.now()
            })
        return res

    name = fields.Char('Opportunity', required=True, default='New')
    expected_revenue = fields.Monetary('Expected Revenue', compute='_compute_expected_revenue', store=True)
    source = fields.Selection([
        ('tender', 'Tender'),
        ('service', 'Service'),
        ('retail', 'Retail'),
    ], string='Source', default='retail')
    history_ids = fields.One2many('stage.history', 'opportunity_id', string='History')
    scope = fields.Char('Scope')
    salesperson_id = fields.Many2one('res.users', string='Salesperson')
    attachment_ids = fields.Many2many('ir.attachment', string='Files')
    pic_ids = fields.Many2many('res.partner', string='PIC')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.depends('order_ids')
    def _compute_expected_revenue(self):
        for record in self:
            record.expected_revenue = sum([order.amount_total for order in record.order_ids])

    def action_view_stage_change_wizard(self):
        self.ensure_one()
        ctx = dict(default_ref_id=self.id, active_ids=self.ids)
        return {
            'name': _('Return Previous Stage'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stage.change.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }
    
    def _prepare_value_inquiry(self, inquiry_number):
        self.ensure_one()
        return {
            'name': inquiry_number,
            'partner_id': self.partner_id.id,
            'source': self.source,
            'tag_ids': self.tag_ids.ids,
            'opportunity_id': self.id,
            'inquiry_date': fields.Date.today(),
            'state': 'inquiry',
            'account_executive_id': self.user_id.id,
            'user_id': self.salesperson_id.id,
            'scope': self.name,
            'due_date': self.date_deadline,
            'inquiry_number': inquiry_number,
        }

    def generate_new_inquiry(self):
        self.ensure_one()
        inquiry_number = self.env['ir.sequence'].sudo().next_by_code('inquiry.review')
        val = self._prepare_value_inquiry(inquiry_number)
        inquiry = self.env['sale.order'].create(val)
        self.write({ 'inquiry_number': inquiry_number })
        if inquiry:
            inquiry.generate_project_requirements()
        self.change_stage(self.env.ref('crm_management.crm_stage_data_inquiry').id)

    inquiry_number = fields.Char('Inquiry Number', default='New')
    inquiry_count = fields.Integer('Inquiry Count', compute='_compute_inquiry_count', default=0)
    @api.depends('order_ids', 'order_ids.state')
    def _compute_inquiry_count(self):
        self.ensure_one()
        self.inquiry_count = len([inquiry for inquiry in self.order_ids if inquiry.state == 'inquiry'])

    quotation_count = fields.Integer('Quotation Count', compute='_compute_quotation_count', default=0)
    @api.depends('order_ids', 'order_ids.state')
    def _compute_quotation_count(self):
        self.ensure_one()
        self.quotation_count = len([order for order in self.order_ids if order.state == 'draft'])

    contract_count = fields.Integer('Contract Count', compute='_compute_contract_count', default=0)
    @api.depends('order_ids', 'order_ids.state')
    def _compute_contract_count(self):
        self.ensure_one()
        self.contract_count = len([order for order in self.order_ids if order.state in ['sale', 'done']])
    
    order_count = fields.Integer('Order Count', compute='_compute_order_count', default=0)
    @api.depends('order_ids', 'order_ids.state')
    def _compute_order_count(self):
        self.ensure_one()
        self.order_count = len([order for order in self.order_ids if order.state in ['cancel']])

    def action_show_inquiry(self):
        if self.inquiry_count == 0:
            return
        action = (self.env.ref('sale.action_orders').sudo().read()[0])
        action['domain'] = [('id', 'in', self.order_ids.ids), ('state', '=', 'inquiry')]
        if self.inquiry_count == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = self.order_ids.ids[0]
        return action

    def action_view_sale_quotation(self):
        if self.quotation_count == 0:
            return
        return super().action_view_sale_quotation()

    def action_show_contract(self):
        if self.contract_count == 0:
            return
        action = (self.env.ref('sale.action_orders').sudo().read()[0])
        action['domain'] = [('id', 'in', self.order_ids.ids), ('state', 'in', ['sale', 'done'])]
        if self.contract_count == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = self.order_ids.ids[0]
        return action

    def action_show_order(self):
        if self.order_count == 0:
            return
        action = (self.env.ref('sale.action_quotations_with_onboarding').sudo().read()[0])
        action['domain'] = [('id', 'in', self.order_ids.ids), ('state', 'in', ['cancel'])]
        return action

    def action_set_lost(self):
        self.ensure_one()
        ctx = dict(default_ref_id=self.id, active_ids=self.ids)
        return {
            'name': _('Lost Stage'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stage.lost.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def change_stage(self, stage_id, reason='-'):
        self.ensure_one()
        self.env['stage.history'].create({
            'opportunity_id': self.id,
            'old_stage_id': self.stage_id.id,
            'stage_id': stage_id,
            'user_id': self.env.user.id,
            'reason': reason,
            'date': fields.Datetime.now(),
        })
        self.write({ 'stage_id': stage_id })


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    is_lost = fields.Boolean('Is Lost Stage')