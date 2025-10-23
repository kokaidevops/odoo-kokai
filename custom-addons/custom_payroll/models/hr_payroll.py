from odoo import _, api, fields, models
from odoo.tools.misc import format_date


class HrMinimumWage(models.Model):
    _name = 'hr.minimum.wage'
    _description = 'Hr Minimum Wage'
    _order = 'value ASC, id DESC'

    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    country_id = fields.Many2one('res.country', string='Country', related='company_id.country_id', readonly=False, store=True)
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=', country_id)]")
    city_id = fields.Many2one('res.city', string='City', domain="[('state_id', '=', state_id)]")
    name = fields.Char('Name', compute='_compute_name', store=True, readonly=False)
    value = fields.Monetary('Value')

    @api.depends('country_id', 'city_id', 'country_id.name', 'city_id.name')
    def _compute_name(self):
        for record in self:
            code = record.state_id.name if not record.city_id else record.city_id.name
            record.name = "Minimum Wage - %s" % (code)


class HrAllowance(models.Model):
    _name = 'hr.allowance'
    _description = 'Hr Allowance'
    _order = 'sequence ASC, id DESC'

    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    type = fields.Selection([
        ('allowance', 'Allowance'),
        ('nf_allowance', 'Non-Fixed Allowance'),
    ], string='Type', default='allowance')


class HrContractAllowance(models.Model):
    _name = 'hr.contract.allowance'
    _description = 'Hr Contract Allowance'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', ondelete='cascade')
    allowance_id = fields.Many2one('hr.allowance', string='Allowance', ondelete='cascade')
    value = fields.Monetary('Value')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    basic_salary = fields.Monetary('Basic Salary')
    wage = fields.Monetary('Wage', compute='_compute_wage')
    minimum_wage_id = fields.Many2one('hr.minimum.wage', string='Minimum Wage', related='company_id.minimum_wage_id', store=True, readonly=False)
    employee_shift_id = fields.Many2one('hr.employee.shift', string='Employee Shift', ondelete='cascade')
    allowance_ids = fields.One2many('hr.contract.allowance', 'contract_id', string='Allowance')
    total_allowance = fields.Monetary('Total Allowance', compute='_compute_total_allowance', store=True, readonly=False)
    tin = fields.Char('Taxpayer Identification Number (TIN)', related='employee_id.tin', store=True)

    def _calculate_take_home_pay(self):
        self.ensure_one()
        return self.basic_salary + self.total_allowance
    
    @api.depends('basic_salary', 'total_allowance', 'wage_type')
    def _compute_wage(self):
        for record in self:
            record.wage = record._calculate_take_home_pay() if record.wage_type == 'monthly' else 0

    @api.depends('allowance_ids', 'allowance_ids.value')
    def _compute_total_allowance(self):
        for record in self:
            record.total_allowance = sum([allowance.value for allowance in record.allowance_ids])


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_shift_id = fields.Many2one('hr.employee.shift', string='Employee Shift', compute='_compute_employee_shift_id', store=True, ondelete='cascade')
    contract_type_id = fields.Many2one('hr.contract.type', string='Contract Type', compute='_compute_contract_type_id', store=True)

    @api.depends('contract_id', 'contract_id.employee_shift_id')
    def _compute_employee_shift_id(self):
        for record in self:
            record.employee_shift_id = record.contract_id.employee_shift_id

    @api.depends('contract_id', 'contract_id.state')
    def _compute_contract_type_id(self):
        for record in self:
            record.contract_type_id = record.contract_id.contract_type_id


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    contract_type_id = fields.Many2one('hr.contract.type', string='Contract Type', related='employee_id.contract_type_id')


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    calculate_tax = fields.Boolean('Calculate Tax', default=True)
    merge_payslip = fields.Boolean('Merge Payslip')
    payslip_ids = fields.Many2many(
        'hr.payslip', 
        relation='hr_payslip_hr_payslip_rel',
        column1='hr_payslip_id',
        column2='related_hr_payslip_id',
        string='Payslip', 
        domain="[('employee_id', '=', employee_id), ('state', '=', 'verify')]"
    )

    def compute_sheet(self):
        for record in self:
            if record.merge_payslip:
                query = """
                    DELETE FROM hr_payslip_input
                    WHERE payslip_id=%s AND input_type_id=%s
                """ % (record.id, self.env.ref('custom_payroll.hr_payslip_input_type_merge_payslip').id)
                self.env.cr.execute(query)
                for payslip in record.payslip_ids:
                    self.env['hr.payslip.input'].create({
                        'payslip_id': record.id,
                        'input_type_id': self.env.ref('custom_payroll.hr_payslip_input_type_merge_payslip').id,
                        'name': payslip.number,
                        'amount': payslip.net_wage,
                    })
        return super().compute_sheet()

    def action_payslip_done(self):
        res = super().action_payslip_done()
        for payslip in self.payslip_ids:
            payslip.action_payslip_done()
        return res

    def action_payslip_paid(self):
        res = super().action_payslip_paid()
        for payslip in self.payslip_ids:
            payslip.action_payslip_paid()
        query = """
            UPDATE hr_attendance SET state='paid', payslip_id=%s
            WHERE employee_id=%s AND check_in<='%s' AND check_out>='%s'
        """ % (self.id, self.employee_id.id, self.date_to, self.date_from)
        self.env.cr.execute(query)
        return res