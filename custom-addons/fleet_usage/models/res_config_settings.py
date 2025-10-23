from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    approval_fleet_usage_id = fields.Many2one('approval.category', string='Approval Fleet Usage')
    # fleet_service_team_id = fields.Many2one('helpdesk.team', string='Fleet Service Team')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_fleet_usage_id = fields.Many2one('approval.category', string='Approval Fleet Usage', related='company_id.approval_fleet_usage_id', readonly=False)
    # fleet_service_team_id = fields.Many2one('helpdesk.team', string='Fleet Service Team', related='company_id.fleet_service_team_id', readonly=False)