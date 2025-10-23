from odoo import _, api, fields, models


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    fleet_id = fields.Many2one('fleet.vehicle', string='Vehicle')