from odoo import _, api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    tin = fields.Char('Taxpayer Identification Number (TIN)')
    blood_type = fields.Char('Blood Type')
    family_card_no = fields.Char('Family Card Number')
    emergency_address = fields.Char('Contact Address')


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    tin = fields.Char('Taxpayer Identification Number (TIN)', related='employee_id.tin')
    blood_type = fields.Char('Blood Type', related='employee_id.blood_type')
    family_card_no = fields.Char('Family Card Number', related='employee_id.family_card_no')


class HrContractType(models.Model):
    _inherit = 'hr.contract.type'

    code = fields.Char('Code')