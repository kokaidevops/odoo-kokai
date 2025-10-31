from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

import base64
import requests
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(selection_add=[('approved', 'Approved'), ('need_improvement', 'Need Improvement')], string='Status')
    approval_ids = fields.One2many(comodel_name='approval.request', inverse_name='purchase_order_id', string='Approval Request', readonly=True, copy=False, tracking=True)
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', readonly=True)
    approved_date = fields.Datetime('Approved Date', compute='_compute_approved_date', readonly=True, store=True)

    qrcode_prepared_by = fields.Binary('Qrcode Prepared By', compute='_compute_qrcode_prepared_by', store=True)
    qrcode_approved_by = fields.Binary('Qrcode Approved By', compute='_compute_qrcode_approved_by', store=True)

    @api.depends('approval_ids', 'approval_ids.request_status')
    def _compute_approved_date(self):
        for record in self:
            if record.approval_ids:
                request = record.approval_ids[record.approval_count-1]
                if request.request_status == 'approved':
                    record.approved_date = request.date_confirmed
                else:
                    record.approved_date = ''

    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for rec in self:
            rec.approval_count = len(rec.mapped('approval_ids'))

    def generate_approval_request(self):
        self.ensure_one()
        category_pr = self.env.company.approval_po_id
        vals = {
            'name': 'Request Approval for ' + self.name,
            'purchase_order_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for {self.name} from {self.user_id.name} \n {self.notes}",
            'approver_id': self.approver_id.id,
        }
        self.sudo().write({ 'state': 'to approve' })
        request = self.env['approval.request'].create(vals)
        request.action_confirm()
    
    def _set_false_check_line(self):
        super()._set_false_check_line()
        callback_function = self.env.context.get('callback_function')
        if callback_function == 'generate_approval_request':
            self.generate_approval_request()

    def action_view_approval_request(self):
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        approvals = self.mapped('approval_ids')
        if len(approvals) > 1:
            action['domain'] = [('id', 'in', approvals.ids)]
        elif approvals:
            action['views'] = [(self.env.ref('approvals.approval_request_view_form').id, 'form')]
            action['res_id'] = approvals.ids[0]
        return action

    def action_approved(self):
        self.ensure_one()
        self.write({ 'state': 'approved' })
        # TODO
        # needed to create notification?
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('purchase.model_purchase_order').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': 'Please process the following Purchase Order as soon as possible. Thank You!',
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        self._compute_qrcode_prepared_by()
        self._compute_qrcode_approved_by()

    def action_need_improvement(self, reason):
        self.ensure_one()
        self.write({ 'state': 'need_improvement' })
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('purchase.model_purchase_order').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })

    def _check_approval_request(self):
        self.ensure_one()
        return not self.state == 'approved'

    def button_confirm(self):
        check_approval_state = self._check_approval_request()
        if check_approval_state:
            raise ValidationError("Please Request Approval first before confirm PO!")
        self.write({ 'state': 'draft' })
        return super(PurchaseOrder, self).button_confirm()

    def _compute_qrcode_prepared_by(self):
        for record in self:
            barcode = ""
            try:
                approval = record.approval_ids[record.approval_count-1]
                link = f"https://odoo.valve.id/requested?requested={approval.id}"
                barcode = base64.b64encode(requests.get(f"https://odoo.valve.id/api/qrcode?text={link}").content).replace(b"\n", b"")
            except Exception as e:
                _logger.warning("Can't load the image from URL")
                logging.exception(e)
            _logger.warning(barcode)
            record.write({ 'qrcode_prepared_by': barcode })

    def _compute_qrcode_approved_by(self):
        for record in self:
            barcode = ""
            try:
                approver = record.approval_ids[record.approval_count-1].approver_ids[0]
                link = f"https://odoo.valve.id/approval?proof={approver.id}"
                barcode = base64.b64encode(requests.get(f"https://odoo.valve.id/api/qrcode?text={link}").content).replace(b"\n", b"")
            except Exception as e:
                _logger.warning("Can't load the image from URL")
                logging.exception(e)
            record.write({ 'qrcode_approved_by': barcode })

    def _generate_order(self):
        self._set_false_check_line()

    def button_cancel(self):
        res = super().button_cancel()
        for approval in self.approval_ids.filtered(lambda approval: approval.request_status == 'pending'):
            approval.action_cancel()
        return res