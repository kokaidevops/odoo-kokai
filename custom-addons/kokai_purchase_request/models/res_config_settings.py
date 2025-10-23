from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_purchase_team_id = fields.Many2one('department.team', string='Default Purchasing Team')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_purchase_team_id = fields.Many2one('department.team', string='Default Purchasing Team', related='company_id.default_purchase_team_id', config_parameter='kokai_purchase_request.default_purchase_team_id', readonly=False, default_model='department.team')