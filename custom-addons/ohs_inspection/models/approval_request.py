from odoo import _, api, fields, models

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')
]


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_ohs_nonconformity = fields.Selection(CATEGORY_SELECTION, string='Has OHS Nonconformity', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    ohs_nonconformity_id = fields.Many2one('ohs.nonconformity', string='Accident')
    has_ohs_nonconformity = fields.Selection(related='category_id.has_ohs_nonconformity')
    
    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        
        for request in self:
            category_ohs_nonconformity = self.env.ref('ohs_inspection.approval_category_data_ohs_nonconformity')
            if request.category_id.id == category_ohs_nonconformity.id:
                if request.request_status == 'refused':
                    request.ohs_nonconformity_id.action_need_improvement()
                elif request.request_status == 'approved':
                    request.ohs_nonconformity_id.action_approved()
        return res