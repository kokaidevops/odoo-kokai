from odoo import _, api, fields, models
import logging

_logger = logging.getLogger(__name__)

class ApprovalRefusedReasonWizard(models.TransientModel):
    _name = 'approval.refused.reason.wizard'
    _description = 'Wizard of Approval Refused Reason'

    request_id = fields.Many2one('approval.request', string='Request Doc')
    reason = fields.Char('Reason')

    def rejection_processed(self):
        self.ensure_one()

        request = self.request_id
        request.action_refuse()
        request.write({ 'refused_reason': self.reason })
        approver = request.mapped('approver_ids').filtered(lambda approver: approver.user_id == self.env.user)
        approver.write({'reason': self.reason})