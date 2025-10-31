from odoo import _, api, fields, models


class HRApplicant(models.Model):
    _inherit = 'hr.applicant'

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Gender', required=True, default='male')
    nickname = fields.Char('Nickname')
    height = fields.Float("Applicant's Height")
    weight = fields.Float("Applicant's Weight")
    disability = fields.Boolean('Disability?')
    physical_disability = fields.Char('Physical Disability')
    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2one('res.country.state', string='State')
    city_id = fields.Many2one('res.city', string='City')
    subdistrict_id = fields.Many2one('res.subdistrict', string='Subdistrict')
    ward_id = fields.Many2one('res.ward', string='Ward')
    street = fields.Char('Street')
    zip = fields.Char('ZIP')
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced'),
    ], string='Marital', default='single', required=True)
    family_member_ids = fields.One2many('family.member.list', 'applicant_id', string='Family Member')
    personality_ids = fields.One2many('employee.personality.list', 'applicant_id', string='Personality')
    dependents = fields.Integer('Dependents (Person)')
    emergency_contact = fields.Char('Contact Name')
    emergency_phone = fields.Char('Contact Phone')
    emergency_address = fields.Char('Contact Address')


class FamilyMemberList(models.Model):
    _name = 'family.member.list'
    _description = 'Family Member List'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    applicant_id = fields.Many2one('hr.applicant', string='Applicant')
    name = fields.Char('Name')
    member = fields.Selection([
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('husband', 'Husband'),
        ('wife', 'Wife'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('children', 'Children'),
    ], string='Member', required=True)
    age = fields.Integer('Age')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Gender', required=True, default='male')
    education = fields.Char('Education')
    occupation = fields.Char('Occupation')


class EmployeePersonalityList(models.Model):
    _name = 'employee.personality.list'
    _description = 'Employee Personality List'

    name = fields.Char('Name')
    type = fields.Selection([
        ('positive', 'Positive'),
        ('negative', 'Negative'),
    ], string='Type', required=True)
    applicant_id = fields.Many2one('hr.applicant', string='Applicant')
    employee_id = fields.Many2one('hr.employee', string='Employee')


class EmployeeSalaryOffering(models.Model):
    _name = 'employee.salary.offering'
    _description = 'Employee Salary Offering'

    allowance_id = fields.Many2one('hr.contract.allowance', string='Allowance')
    value = fields.Float('Value')
    name = fields.Char('Name', related='allowance_id.name')
    note = fields.Char('Note')