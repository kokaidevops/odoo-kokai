from odoo import _, api, fields, models


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    pic_id = fields.Many2one('res.users', string='PIC')
    department_id = fields.Many2one('hr.department', string='Department')