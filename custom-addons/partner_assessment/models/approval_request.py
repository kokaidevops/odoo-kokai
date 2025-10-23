from odoo import _, api, fields, models

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')
]

class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_partner_assessment = fields.Selection(CATEGORY_SELECTION, string='Has Partner Assessment', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    assessment_id = fields.Many2one('partner.assessment', string='Doc Ref')
    has_partner_assessment = fields.Selection(related='category_id.has_partner_assessment')
    
    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            category_pr = self.env.company.partner_assessment_approval_id
            if request.category_id.id == category_pr.id:
                if request.request_status == 'refused':
                    request.assessment_id.action_reject(self.refused_reason)
                elif request.request_status == 'approved':
                    request.assessment_id.action_approved()
        return res