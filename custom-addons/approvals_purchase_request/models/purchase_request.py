from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

import base64
import requests
import logging

_logger = logging.getLogger(__name__)

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    approval_ids = fields.One2many(comodel_name='approval.request', inverse_name='purchase_request_id', string='Approval Request', readonly=True, copy=False, tracking=True)
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', readonly=True)
    approved_date = fields.Datetime('Approved Date', compute='_compute_approved_date', readonly=True, store=True)
    state = fields.Selection(selection_add=[ ('need_improvement', 'Need Improvement') ], ondelete={ 'need_improvement': 'cascade' })

    qrcode_request_by = fields.Binary('Qrcode Request By', compute='_compute_qrcode_request_by', store=True)
    qrcode_approved_by = fields.Binary('Qrcode Approved By', compute='_compute_qrcode_approved_by', store=True)
    qrcode_director = fields.Binary('Qrcode Director', compute='_compute_qrcode_director', store=True)

    @api.depends('approval_ids', 'approval_ids.request_status')
    def _compute_approved_date(self):
        for record in self:
            approved_request = self.approval_ids.filtered(lambda approval: approval.request_status == 'approved')
            record.approved_date = approved_request[0].date_confirmed if approved_request else False

    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for rec in self:
            rec.approval_count = len(rec.mapped('approval_ids'))

    def generate_approval_request(self):
        self.ensure_one()
        self.mapped('line_ids').filtered(lambda line: line.request_state == 'draft').action_to_approve()
        approved_request = self.approval_ids.filtered(lambda approval: approval.request_status == 'approved')
        if approved_request:
            raise ValidationError("This PR has been Approved! Can't request approval again!")
        try:
            self.name = self._generate_name()
            self.sudo().write({ 'state': 'to_approve' })

            category_pr = self.env.company.approval_pr_id
            vals = {
                'name': 'Request Approval for ' + self.name,
                'purchase_request_id': self.id,
                'request_owner_id': self.env.user.id,
                'category_id': category_pr.id,
                'reason': f"Request Approval for {self.name} from {self.requested_by.name} \n {self.description or ''}"
            }
            request = self.env['approval.request'].sudo().create(vals)
            request.action_confirm()
        except Exception as e:
            raise ValidationError("Can't Request Approval. Please Contact Administrator. \n%s" % str(e))

    def action_view_approval_request(self):
        self.ensure_one()
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        approvals = self.mapped('approval_ids')
        if self.approval_count == 0:
            return
        elif self.approval_count > 1:
            action['domain'] = [('id', 'in', approvals.ids)]
        elif approvals:
            action['views'] = [(self.env.ref('approvals.approval_request_view_form').id, 'form')]
            action['res_id'] = approvals.ids[0]
        return action

    def action_approved(self):
        self.ensure_one()
        self.mapped('line_ids').filtered(lambda line: line.request_state == 'to_approve').action_approved()
        self.write({ 'state': 'approved' })

    def action_need_improvement(self, reason):
        self.ensure_one()
        self.write({ 'state': 'need_improvement' })
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('purchase_request.model_purchase_request').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.requested_by.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })

    def generate_qrcode(self):
        self.ensure_one()
        self._compute_qrcode_request_by()
        self._compute_qrcode_approved_by()
        self._compute_qrcode_director()

    def _compute_qrcode_request_by(self):
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
            record.write({ 'qrcode_request_by': barcode })

    def _compute_qrcode_approved_by(self):
        for record in self:
            barcode = ""
            try:
                approver = record.approval_ids[record.approval_count-1].approver_ids[0]
                if approver.status == 'approved':
                    link = f"https://odoo.valve.id/approval?proof={approver.id}"
                    barcode = base64.b64encode(requests.get(f"https://odoo.valve.id/api/qrcode?text={link}").content).replace(b"\n", b"")
            except Exception as e:
                _logger.warning("Can't load the image from URL")
                logging.exception(e)
            record.write({ 'qrcode_approved_by': barcode })

    def _compute_qrcode_director(self):
        for record in self:
            barcode = ""
            try:
                approver = record.approval_ids[record.approval_count-1].approver_ids[1]
                if approver.status == 'approved':
                    link = f"https://odoo.valve.id/approval?proof={approver.id}"
                    barcode = base64.b64encode(requests.get(f"https://odoo.valve.id/api/qrcode?text={link}").content).replace(b"\n", b"")
            except Exception as e:
                _logger.warning("Can't load the image from URL")
                logging.exception(e)
            record.write({ 'qrcode_director': barcode })

    def button_draft(self):
        self.mapped('approval_ids').action_cancel()
        self.mapped('line_ids').action_draft()
        return super().button_draft()

    def button_rejected(self):
        self.mapped('approval_ids').action_cancel()
        return super().button_rejected()