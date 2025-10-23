from odoo import _, api, fields, models
import logging

_logger = logging.getLogger(__name__)

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')
]

class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_shift_change = fields.Selection(CATEGORY_SELECTION, string='Has Employee Shift Change', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    shift_change_id = fields.Many2one('employee.shift.change', string='Employee Shift Change')
    has_shift_change = fields.Selection(related='category_id.has_shift_change')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        
        for request in self:
            category_pr = self.env.company.approval_shift_change_id
            if request.category_id.id == category_pr.id:
                if request.request_status == 'refused':
                    request.shift_change_id.sudo().action_rejected(self.refused_reason)
                elif request.request_status == 'approved':
                    request.shift_change_id.sudo().action_approved()

        return res