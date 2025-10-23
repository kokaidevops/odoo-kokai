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

    has_hr_overtime = fields.Selection(CATEGORY_SELECTION, string='Has Overtime', default='no')
    has_hr_overtime_batch = fields.Selection(CATEGORY_SELECTION, string='Has Overtime Batch', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    hr_overtime_id = fields.Many2one('hr.overtime', string='Overtime')
    has_hr_overtime = fields.Selection(related='category_id.has_hr_overtime')
    hr_overtime_batch_id = fields.Many2one('hr.overtime.batch', string='Overtime Batch')
    has_hr_overtime_batch = fields.Selection(related='category_id.has_hr_overtime_batch')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            if request.category_id.id == self.env.company.approval_overtime_id.id:
                if request.request_status == 'refused':
                    request.hr_overtime_id.sudo().action_need_improvement(self.refused_reason)
                elif request.request_status == 'approved':
                    request.hr_overtime_id.sudo().action_approved()
            if request.category_id.id == self.env.company.approval_overtime_batch_id.id:
                if request.request_status == 'refused':
                    request.hr_overtime_batch_id.sudo().action_need_improvement(self.refused_reason)
                elif request.request_status == 'approved':
                    request.hr_overtime_batch_id.sudo().action_approved()
        return res