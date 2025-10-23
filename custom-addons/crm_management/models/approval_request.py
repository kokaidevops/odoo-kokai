from odoo import _, api, fields, models

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')
]

class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_contract_issue = fields.Selection(CATEGORY_SELECTION, string='Has Contract Issue', default='no')
    has_contract_review = fields.Selection(CATEGORY_SELECTION, string='Has Contract Review', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    issue_id = fields.Many2one('contract.issue', string='Issue')
    has_contract_issue = fields.Selection(related='category_id.has_contract_issue')
    
    order_id = fields.Many2one('sale.order', string='Doc Ref')
    has_contract_review = fields.Selection(related='category_id.has_contract_review')
    
    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            category_pr = self.env.company.issue_approval_id
            if request.category_id.id == category_pr.id:
                if request.request_status == 'refused':
                    request.issue_id.action_reject(self.refused_reason)
                elif request.request_status == 'approved':
                    request.issue_id.action_approved()

            category_pr = self.env.company.contract_approval_id
            if request.category_id.id == category_pr.id:
                if request.request_status == 'refused':
                    request.order_id.action_need_improvement(self.refused_reason)
                elif request.request_status == 'approved':
                    request.order_id.action_approved()
        return res