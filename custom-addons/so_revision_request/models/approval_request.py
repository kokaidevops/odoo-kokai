from odoo import _, api, fields, models

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')
]

class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_so_revision = fields.Selection(CATEGORY_SELECTION, string='Has SO Revision', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    so_revision_id = fields.Many2one('sale.order', string='Doc Ref')
    has_so_revision = fields.Selection(related='category_id.has_so_revision')
    
    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            category_pr = self.env.company.so_revision_approval_id
            if request.category_id.id == category_pr.id:
                if request.request_status == 'refused':
                    request.so_revision_id.action_revision_rejected(self.refused_reason)
                elif request.request_status == 'approved':
                    request.so_revision_id.action_revision_approved()
        return res