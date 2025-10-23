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

    has_budget_plan = fields.Selection(CATEGORY_SELECTION, string='Has Budget Plan', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    budget_plan_id = fields.Many2one('kokai.rab', string='Budget Plan')
    has_budget_plan = fields.Selection(related='category_id.has_budget_plan')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        
        for request in self:
            category_pr = self.env.company.approval_po_id
            if request.category_id.id == category_pr.id:
                if request.request_status == 'refused':
                    request.budget_plan_id.sudo().action_reject(request.refused_reason)
                elif request.request_status == 'approved':
                    request.budget_plan_id.sudo().action_approve()

        return res
