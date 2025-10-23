from odoo import _, api, fields, models


class RecruitmentTestType(models.Model):
    _name = 'recruitment.test.type'
    _description = 'Recruitment Test Type'

    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', default=True)


class RecruitmentTestValue(models.Model):
    _name = 'recruitment.test.value'
    _description = 'Recruitment Test Value'
    _order = 'sequence ASC, id DESC'

    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Description')
    value = fields.Float('Value')


class RecruitmentTest(models.Model):
    _name = 'recruitment.test'
    _description = 'Recruitment Test'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', required=True)
    test_type_id = fields.Many2one('recruitment.test.type', string='Test Type')
    value_id = fields.Many2one('recruitment.test.value', string='Value')
    description = fields.Char('Description', related='value_id.name', store=True)