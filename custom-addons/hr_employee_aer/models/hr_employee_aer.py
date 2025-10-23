from odoo import _, api, fields, models


class HREmployeeAER(models.Model):
    _name = 'hr.employee.aer'
    _description = 'AER Category'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    aer_id = fields.Many2one('average.effective.rate', string='AER')
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced'),
    ], string='Marital', default='single')
    dependents = fields.Integer('Dependents', default=0)


class AverageEffectiveRate(models.Model):
    _name = 'average.effective.rate'
    _description = 'Average Effective Rate'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    name = fields.Char('Name')
    range_ids = fields.One2many('aer.range', 'aer_id', string='Range')
    employee_aer_ids = fields.One2many('hr.employee.aer', 'aer_id', string='Category')


class AerRange(models.Model):
    _name = 'aer.range'
    _description = 'AER Range'

    aer_id = fields.Many2one('average.effective.rate', string='AER')
    start_range = fields.Float('Start Range')
    end_range = fields.Float('End Range')
    rate = fields.Float('Rate (%)', default=0)


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    hr_employee_aer_id = fields.Many2one('hr.employee.aer', string='AER Category')
    aer_id = fields.Many2one('average.effective.rate', string='AER', related='hr_employee_aer_id.aer_id')


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    hr_employee_aer_id = fields.Many2one('hr.employee.aer', string='AER Category', related='employee_id.hr_employee_aer_id')
    aer_id = fields.Many2one('average.effective.rate', string='AER', related='hr_employee_aer_id.aer_id')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    aer_id = fields.Many2one('average.effective.rate', string='AER', related='employee_id.aer_id')