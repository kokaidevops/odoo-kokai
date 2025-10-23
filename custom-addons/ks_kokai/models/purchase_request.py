from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'
    
    rab_id = fields.Many2one(
        'kokai.rab',
        string='RAB Reference',
        readonly=True
    )

class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'
    
    rab_line_id = fields.Many2one(
        'kokai.rab.line',
        string='RAB Line Reference',
        ondelete='set null',
        index=True
    )
    
    rab_id = fields.Many2one(
        'kokai.rab',
        related='rab_line_id.rab_id',
        string='RAB Reference',
        store=True,
        readonly=True
    )   
    
    @api.model_create_multi
    def create(self, vals_list):
        lines = super(PurchaseRequestLine, self).create(vals_list)
        # Update RAB line status
        for line in lines:
            if line.rab_line_id:
                line.rab_line_id.write({
                    'reason': 'pr_draft'
                })
        return lines