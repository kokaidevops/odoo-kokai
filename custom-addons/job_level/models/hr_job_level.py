from odoo import _, api, fields, models


class HRJobLevel(models.Model):
    _name = 'hr.job.level'
    _description = 'HR Job Level'

    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    job_level_id = fields.Many2one('hr.job.level', string='Job Level', related='contract_id.job_level_id')


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    job_level_id = fields.Many2one('hr.job.level', string='Job Level', related='employee_id.job_level_id')


class HRContract(models.Model):
    _inherit = 'hr.contract'

    job_level_id = fields.Many2one('hr.job.level', string='Job Level')
