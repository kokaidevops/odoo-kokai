from odoo import _, api, fields, models
import logging

_logger = logging.getLogger(__name__)

class PositionApprover(models.Model):
    _name = 'position.approver'
    _description = 'Position of Approver in Approval Request'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True)

class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    position_id = fields.Many2one('position.approver', string='Position')
    level = fields.Integer('Level')

class ApprovalCategoryApprover(models.Model):
    _inherit = 'approval.category.approver'

    position_id = fields.Many2one('position.approver', string='Position')
    level = fields.Integer('Level')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    @api.depends('category_id', 'request_owner_id')
    def _compute_approver_ids(self):
        res = super(ApprovalRequest, self)._compute_approver_ids()
        
        for approver in self.approver_ids:
            appr = self.env['approval.category.approver'].search([
                ('category_id', '=', self.category_id.id),
                ('user_id', '=', approver.user_id.id),
            ], limit=1)
            if appr:
                approver.sudo().update({'position_id': appr.position_id.id})
        return res
        
    def action_approve(self, approver=None):
        self.ensure_one()
        res = super().action_approve(approver)
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        if not approver:
            return res

        self.env.cr.execute(f"DELETE FROM approval_approver WHERE request_id={self.id} AND level={approver.level} AND NOT id={approver.id}")