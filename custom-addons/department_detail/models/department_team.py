from odoo import _, api, fields, models
import logging

_logger = logging.getLogger(__name__)


class DepartmentTeam(models.Model):
    _name = 'department.team'
    _inherit = ['mail.thread']
    _description = 'Department Team'

    name = fields.Char('Name', required=True)
    member_ids = fields.Many2many('res.users', string='Member')
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    user_id = fields.Many2one('hr.employee', string='Team Leader')
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, related='department_id.company_id')
    currency_id = fields.Many2one("res.currency", string="Currency", related='company_id.currency_id', readonly=True)


class ResUsers(models.Model):
    _inherit = 'res.users'

    department_team_ids = fields.Many2many('department.team', string='Department Team')

class HRDepartment(models.Model):
    _inherit = 'hr.department'

    team_ids = fields.Many2many('department.team', string='Team')