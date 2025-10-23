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

    has_stock_picking = fields.Selection(CATEGORY_SELECTION, string='Has Stock Picking', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    picking_id = fields.Many2one('stock.picking', string='Stock Picking')
    has_stock_picking = fields.Selection(related='category_id.has_stock_picking')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            if request.category_id.id == self.env.ref('receiving_material.approval_category_data_stock_picking').id:
                if request.request_status == 'refused':
                    request.picking_id.sudo().action_need_improvement()
                elif request.request_status == 'approved':
                    request.picking_id.sudo().action_approved()
        return res