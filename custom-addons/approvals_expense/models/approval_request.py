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

    has_expense_report = fields.Selection(CATEGORY_SELECTION, string='Has Expense Report', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    expense_id = fields.Many2one('hr.expense.sheet', string='Expense Report')
    has_expense_report = fields.Selection(related='category_id.has_expense_report')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        
        for request in self:
            category_pr = self.env.company.approval_expense_id
            if request.category_id.id == category_pr.id:
                if request.request_status == 'refused':
                    request.expense_id.sudo().action_need_improvement(request.refused_reason)
                elif request.request_status == 'approved':
                    request.expense_id.sudo().action_approved()

        return res
