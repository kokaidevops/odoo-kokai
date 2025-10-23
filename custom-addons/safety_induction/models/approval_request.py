from odoo import _, api, fields, models

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')
]


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_induction = fields.Selection(CATEGORY_SELECTION, string='Has Induction', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    induction_id = fields.Many2one('safety.induction', string='Induction')
    has_induction = fields.Selection(related='category_id.has_induction')
    
    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        
        for request in self:
            category_induction = self.env.ref('safety_induction.approval_category_data_safety_induction')
            if request.category_id.id == category_induction.id:
                if request.request_status == 'refused':
                    request.induction_id.action_need_improvement()
                elif request.request_status == 'approved':
                    request.induction_id.action_approved()
        return res