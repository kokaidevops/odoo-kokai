from odoo import _, api, fields, models


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    responsible_id = fields.Many2one('res.users', string='Responsible')
    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance Team')