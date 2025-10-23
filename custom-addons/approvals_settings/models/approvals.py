from odoo import _, api, fields, models


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'
    _order = 'id DESC'