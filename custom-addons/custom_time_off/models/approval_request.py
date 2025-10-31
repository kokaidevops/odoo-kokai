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

    has_time_off = fields.Selection(CATEGORY_SELECTION, string='Has Time Off', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    leave_id = fields.Many2one('hr.leave', string='Time Off')
    has_time_off = fields.Selection(related='category_id.has_time_off')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            if request.category_id.id == self.env.company.approval_time_off_id.id:
                if request.request_status == 'refused':
                    request.leave_id.sudo().action_refuse(self.refused_reason)
                elif request.request_status == 'approved':
                    request.leave_id.sudo().action_custom_validate()
        return res