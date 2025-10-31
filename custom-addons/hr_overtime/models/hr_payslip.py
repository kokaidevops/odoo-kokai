from odoo import _, api, fields, models
import logging


_logger = logging.getLogger(__name__)


class HrContractOvertime(models.Model):
    _inherit = 'hr.contract'

    get_overtime = fields.Boolean('Get Overtime', default=False)
    have_overtime_package = fields.Boolean('Have Overtime Package')
    over_hour = fields.Monetary('Overtime Hour Wage', compute='_compute_overtime_wage', store=True, readonly=False)
    over_day = fields.Monetary('Overtime Day Wage', compute='_compute_overtime_wage', store=True, readonly=False)

    @api.depends('get_overtime', 'wage_type', 'wage', 'hourly_wage')
    def _compute_overtime_wage(self):
        for record in self:
            if record.get_overtime:
                record.over_hour = record.wage/173 if record.wage_type == 'monthly' else record.hourly_wage
                record.over_day = record.wage/21 if record.wage_type == 'monthly' else record.hourly_wage*8
            else: 
                record.over_hour = 0
                record.over_day = 0


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    overtime_ids = fields.Many2many('hr.overtime', compute='_compute_overtime_ids')
    overtime_cost_amount = fields.Float('Overtime Cost Amount', compute='_compute_overtime_cost_amount')

    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    def _compute_overtime_ids(self):
        for record in self:
            record.update({'overtime_ids': []})
            if not record.struct_id.use_worked_day_lines:
                continue
            date_from = record.date_from
            date_to = record.date_to
            if record.contract_id: 
                date_from = max(record.date_from, record.contract_id.date_start)
            if record.contract_id and record.contract_id.date_end:
                date_to = min(record.date_to, record.contract_id.date_end)
            overtime_ids = self.env['hr.overtime'].search([
                ('state', '=', 'approved'),
                ('payslip_paid', '=', False),
                ('employee_id', '=', record.employee_id.id),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
            ])
            record.update({'overtime_ids': [(4, overtime.id) for overtime in overtime_ids]})

    @api.depends('overtime_ids', 'overtime_ids.overtime_cost')
    def _compute_overtime_cost_amount(self):
        for record in self:
            record.overtime_cost_amount = sum([ overtime.overtime_cost for overtime in record.overtime_ids ])

    def action_payslip_done(self):
        for overtime in self.overtime_ids:
            if overtime.overtime_type_id.type == 'cash':
                overtime.payslip_paid = True
        return super(HRPayslip, self).action_payslip_done()

    def compute_sheet(self):
        for payslip in self:
            for overtime in payslip.overtime_ids:
                overtime._compute_overtime_cost(contract=payslip.contract_id)
        return super(HRPayslip, self).compute_sheet()

    def action_payslip_paid(self):
        res = super().action_payslip_paid()
        for overtime in self.overtime_ids:
            if overtime.overtime_type_id.type == 'cash':
                overtime.update({
                    'payslip_paid': True,
                    'payslip_id': self.id,
                })
        return res

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    source = fields.Selection(selection_add=[ ('overtime', 'Overtime') ], ondelete={ 'overtime': 'cascade' })
    overtime_id = fields.Many2one('hr.overtime', string='Overtime', readonly=True)
