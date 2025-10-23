from odoo import _, api, fields, models

class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    reason = fields.Char('Reason', default='-', tracking=True)


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    refused_reason = fields.Char('Reason', default='-', tracking=True, readonly=True)

    def action_view_approval_refused_reason_wizard(self):
        ctx = dict(
            default_request_id=self.id,
            active_ids=self.ids,
        )

        return {
            'name': _('Approval Refused Reason Wizard'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'approval.refused.reason.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }