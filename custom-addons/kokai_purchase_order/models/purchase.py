from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging


_logger = logging.getLogger(__name__)


class PurchaseOrderBatch(models.Model):
    _name = 'purchase.order.batch'
    _description = 'Purchase Order Batch'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    name = fields.Char('Name')
    request_ids = fields.Many2many('purchase.request', string='Request')
    order_ids = fields.One2many('purchase.order', 'batch_id', string='Purchase Order')
    order_count = fields.Integer('Order Count', compute='_compute_order_count', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('offering', 'Offering'), 
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', required=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    user_ids = fields.Many2many('res.users', string='User')
    date = fields.Datetime('Date', default=fields.Datetime.now(), required=True)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('purchase.order.batch')
        return super(PurchaseOrderBatch, self).create(vals)

    @api.depends('order_ids')
    def _compute_order_count(self):
        for record in self:
            record.order_count = len(record.order_ids)

    def action_show_purchase_order(self):
        self.ensure_one()
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [('id', 'in', self.order_ids.ids)]
        return action

    def _generate_mail_activity(self, user, batch, activity, message=''):
        self.ensure_one()
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('kokai_purchase_order.model_purchase_order_batch').id,
            'res_id': self._origin.id,
            'activity_type_id': activity.id,
            'date_deadline': fields.Date.today() + timedelta(days=activity.delay_count),
            'user_id': user.id,
            'summary': message,
            'batch': batch,
            'handle_by': 'just_one',
        })

    def action_draft(self):
        for order in self.order_ids:
            order.button_draft()
        self.write({ 'state': 'draft' })

    def action_offering(self):
        for order in self.order_ids:
            order.write({ 'state': 'sent' })
        self.ensure_one()
        batch = self.env['ir.sequence'].next_by_code('assignment.activity')
        activity = self.env.ref('kokai_purchase_order.mail_activity_type_data_process_offering')
        message = 'Please process the following Vendor Offering as soon as possible. Thank You!'
        for user in self.user_ids:
            self._generate_mail_activity(user, batch, activity, message)
        self.write({ 'state': 'offering' })

    def action_done(self):
        self.ensure_one()
        batch = self.env['ir.sequence'].next_by_code('assignment.activity')
        activity = self.env.ref('kokai_purchase_order.mail_activity_type_data_process_po')
        message = 'Please process the following Offering to Purchase Order as soon as possible. Thank You!'
        self._generate_mail_activity(self.user_id, batch, activity, message)
        self.write({ 'state': 'done' })

    def generate_order(self):
        for order in self.order_ids:
            accepted_lines = order.order_line.filtered(lambda line: line.offer_state == 'accepted')
            if not accepted_lines and order.state in ['draft', 'sent']:
                order.button_cancel()
                break
            order._generate_order()
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Generate Order'),
                'type': 'info',
                'message': 'Generate Successfully',
                'sticky': False,
            }
        }
        return notification

    def action_cancel(self):
        for order in self.order_ids:
            order.button_cancel()
        query = "DELETE FROM mail_activity WHERE res_id=%s AND res_model_id=%s" % (self.id, self.env.ref('kokai_purchase_order.model_purchase_order_batch').id)
        self.env.cr.execute(query)
        self.write({ 'state': 'cancel' })


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    batch_ids = fields.Many2many('purchase.order.batch', string='Offering Batch')
    batch_count = fields.Integer('Batch Count', compute='_compute_batch_count', store=True)

    @api.depends('batch_ids')
    def _compute_batch_count(self):
        for record in self:
            record.batch_count = len(record.batch_ids)

    def action_show_batch(self):
        self.ensure_one()
        action = self.env.ref('kokai_purchase_order.purchase_order_batch_action').read()[0]
        action['domain'] = [('id', 'in', self.batch_ids.ids)]
        return action

    def sent_vendor_offering(self):
        batches = self.batch_ids.filtered(lambda batch: batch.state == 'draft')
        for batch in batches:
            batch.action_offering()
        notification_type = 'warning'
        message = 'No offers can be sent'
        if batches:
            notification_type = 'info'
            message = 'Vendor Offering has been sent'
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sent Vendor Offering'),
                'type': notification_type,
                'message': message,
                'sticky': False,
            }
        }
        return notification


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    batch_id = fields.Many2one('purchase.order.batch', string='Offering Batch')
    check_line = fields.Boolean('Check Order Line', default=True)
    approver_id = fields.Many2one('res.users','Approver', copy=False, tracking=True, default=lambda self: self.env.company.director_id.id)
    price_term = fields.Selection([
        ('include', 'Include PPN'),
        ('exclude', 'Exclude PPN'),
    ], string='Price Term', default='include', tracking=True)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('vendor.offering')
        return super(PurchaseOrder, self).create(vals)

    def _set_false_check_line(self):
        self.write({ 'check_line': False })
        for line in self.order_line.filtered(lambda line: line.offer_state == 'draft'):
            line.action_accepted(True)
        callback_function = self.env.context.get('callback_function')
        if callback_function == 'button_confirm':
            self.button_confirm()

    def action_offering_done(self):
        self.ensure_one()
        self.batch_id.action_done()

    def action_check(self):
        accepted_lines = self.order_line.filtered(lambda line: line.offer_state == 'accepted')
        message = "Detail of accepted line:\n"
        if not accepted_lines:
            message = "No line is accepted! STILL PROCESS THIS PURCHASE ORDER WITH ALL ORDER LINE?"
        for line in accepted_lines:
            message += "%s - %s %s\n" % (line.product_id.display_name, line.product_qty, line.product_uom.name)
        _logger.warning(message)
        action = (
            self.env["confirmation.wizard"].confirm_message(
                _(message),
                records=self.env["purchase.order"].browse(self.id), # One or more records
                title="Confirm PO",
                method="_set_false_check_line",
                callback_params={}
            )
        )
        if action:
            return action

    def check_and_button_confirm(self):
        self._check_order_line()

    def button_confirm(self):
        if self.check_line:
            return
        self.write({ 'name': self.env['ir.sequence'].next_by_code('purchase.order') })
        return super(PurchaseOrder, self).button_confirm()
    
    def _generate_order(self):
        self.button_confirm()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    offer_state = fields.Selection([
        ('draft', 'RFQ'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], string='Offer State', default='draft', required=True)

    def confirm_accepted(self):
        if not self.state in ['draft', 'sent']:
            return
        if not self.order_id.batch_id:
            self.action_accepted(confirm=True)
            return
        accepted_lines = self.env['purchase.order.line'].search([
            ('product_id', '=', self.product_id.id),
            ('order_id.batch_id', '=', self.order_id.batch_id.id),
            ('offer_state', '=', 'accepted')
        ])
        if not accepted_lines:
            self.action_accepted(confirm=True)
            return
        message = 'Are you sure want to accept this Line? \n'
        for line in accepted_lines:
            message += 'From %s, Order %s %s \n' %(line.order_id.partner_id.name, line.product_qty, line.product_uom.name)
        action = (
            self.env["confirmation.wizard"].confirm_message(
                _(message),
                records=self.env["purchase.order.line"].browse(self.id), # One or more records
                title="Accepted Vendor Offering?",
                method="action_accepted",
                callback_params={"confirm": True}
            )
        )
        if action:
            return action

    def action_accepted(self, confirm=False):
        if not confirm:
            return
        if self.product_qty > 0 and self.offer_state == 'draft':
            self.write({ 'offer_state': 'accepted' })

    def action_rejected(self):
        if not self.order_id.state == 'sent':
            raise ValidationError("Cant' rejected when line not in Sent state")
        self.write({ 'offer_state': 'rejected' })