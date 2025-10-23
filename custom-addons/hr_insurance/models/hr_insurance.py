from odoo import _, api, fields, models


class HrInsurance(models.Model):
    _name = 'hr.insurance'
    _description = 'Hr Insurance'

    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Name')
    code = fields.Char('Code')
    borne_by = fields.Selection([
        ('company', 'Company'),
        ('employee', 'Employee'),
    ], string='Borne By', default='company')
    insurance_type = fields.Selection([
        ('healthy', 'Healthy'),
        ('employment', 'Employment'),
    ], string='Insurance Type', default='healthy')
    rate = fields.Float('Rate (%)')


class HrContractInsurance(models.Model):
    _name = 'hr.contract.insurance'
    _description = 'Hr Contract Insurance'

    contract_id = fields.Many2one('hr.contract', string='Contract', ondelete='cascade')
    insurance_id = fields.Many2one('hr.insurance', string='Insurance', ondelete='cascade')
    amount_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('code', 'Python Code'),
    ], string='Amount Type', default='code', required=True)
    amount_fixed = fields.Float('Amount Fixed', default=0)
    rate = fields.Float('Rate (%)', store=True, readonly=False)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    insurance_ids = fields.One2many('hr.contract.insurance', 'contract_id', string='Insurance')

    # @api.model_create_multi
    # def create(self, vals):
    #     res = super(HrContract, self).create(vals)
    #     for record in res:
    #         record.write({
    #             'insurance_ids': [()]
    #         })
    #     return res


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    calculate_insurance = fields.Boolean('Calculate Insurance', default=True)