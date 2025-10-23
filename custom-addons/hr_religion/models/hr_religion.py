from odoo import _, api, fields, models


class HrReligion(models.Model):
    _name = 'hr.religion'
    _description = 'Hr Religion'

    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Name')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    religion_id = fields.Many2one('hr.religion', string='Religion')


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    religion_id = fields.Many2one('hr.religion', string='Religion', related='employee_id.religion_id')