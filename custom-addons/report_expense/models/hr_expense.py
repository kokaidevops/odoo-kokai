from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

import base64
import requests


class HrExpense(models.Model):
    _inherit = 'hr.expense.sheet'

    def print_py3o(self):
        return self.env.ref("report_expense.action_report_expense_py3o").report_action(self, config=False)
    
    qrcode_request_by = fields.Binary('Qrcode Request By', compute='_compute_qrcode_request_by', store=True)
    qrcode_approved_by = fields.Binary('Qrcode Approved By', compute='_compute_qrcode_approved_by', store=True)
    qrcode_director = fields.Binary('Qrcode Director', compute='_compute_qrcode_director', store=True)

    def _get_string_type(self):
        self.ensure_one()
        type = dict(self._fields['type'].selection).get(self.type)
        return type

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
                raise ValidationError(str(e))
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
                raise ValidationError(str(e))
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
                raise ValidationError(str(e))
            record.write({ 'qrcode_director': barcode })