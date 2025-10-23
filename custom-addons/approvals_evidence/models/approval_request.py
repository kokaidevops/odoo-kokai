from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)

class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    date = fields.Date('Date', compute='generate_date', store=True)

    @api.depends('status')
    def generate_date(self):
        for record in self:
            if record.status in ['refused', 'approved']:
                record.write({ 'date': fields.Date.today() })
            else:
                record.write({ 'date': '' })