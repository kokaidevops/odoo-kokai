from odoo import _, api, fields, models
import logging


_logger = logging.getLogger(__name__)


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    get_pto_payout = fields.Boolean('PTO Payout?', default=True)
    pto_payout_ids = fields.Many2many('hr.leave.allocation', string='PTO Payout')
    time_off_ids = fields.Many2many('hr.leave', string='Time Off', compute='_compute_time_off_ids', store=True, readonly=False)
    calculate_leave = fields.Boolean('Calculate Leave?')
    holiday_status_ids = fields.Many2many('hr.leave.type', string='Time Off Type') #, related='payslip_run_id.holiday_status_ids', readonly=False, store=True)

    @api.model_create_multi
    def create(self, vals):
        payslips = super().create(vals)
        for payslip in payslips:
            if not payslip.payslip_run_id:
                continue
            calculate_leave = payslip.payslip_run_id.calculate_leave_for_employee == 'all' or payslip.payslip_run_id.calculate_leave_for_employee == payslip.contract_id.wage_type
            payslip.write({
                'calculate_leave': calculate_leave,
                'holiday_status_ids': payslip.payslip_run_id.holiday_status_ids.ids if calculate_leave else [],
            })
        return payslips

    def compute_sheet(self):
        for payslip in self:
            pto_payouts_ids = []
            payslip.update({ 'pto_payout_ids': pto_payouts_ids })
            if payslip.get_pto_payout:
                pto_payouts = self.env['hr.leave.allocation'].search([
                    ('state', '=', 'expired'),
                    ('employee_id', '=', payslip.employee_id.id),
                    ('payslip_paid', '=', False),
                    ('holiday_status_id.can_payout', '=', True),
                ])
                query = """
                    DELETE FROM hr_payslip_input
                    WHERE payslip_id=%s AND input_type_id=%s
                """ % (payslip.id, self.env.ref('custom_payroll.hr_payslip_input_type_return_pto_payout').id)
                self.env.cr.execute(query)
                for pto_payout in pto_payouts:
                    if pto_payout.remaining_days > 0:
                        day_wage = payslip.contract_id.hourly_wage*8 if payslip.contract_id.wage_type == 'hourly' else payslip.contract_id.wage/21
                        self.env['hr.payslip.input'].create({
                            'payslip_id': payslip.id,
                            'input_type_id': self.env.ref('custom_payroll.hr_payslip_input_type_return_pto_payout').id,
                            'name': 'PTO Payout',
                            'amount': pto_payout.remaining_days*day_wage,
                        })
                        pto_payouts_ids.append((4, pto_payout.id))
                payslip.update({ 'pto_payout_ids': pto_payouts_ids })
        return super(HRPayslip, self).compute_sheet()
    
    @api.depends('employee_id', 'contract_id', 'date_from', 'date_to')
    def _compute_time_off_ids(self):
        for record in self:
            date_from = record.date_from
            date_to = record.date_to
            if record.contract_id: 
                date_from = max(record.date_from, record.contract_id.date_start)
            if record.contract_id and record.contract_id.date_end:
                date_to = min(record.date_to, record.contract_id.date_end)
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', record.employee_id.id),
                ('date_from', '>=', date_from),
                ('date_from', '<=', date_to),
                ('state', '=', 'validate'),
            ])
            record.update({ 'time_off_ids': [(4, leave.id) for leave in leaves] })
    
    def action_payslip_paid(self):
        res = super().action_payslip_paid()
        for pto_payout in self.pto_payout_ids:
            pto_payout.update({
                'payslip_paid': True,
                'payslip_id': self.id,
            })
        return res


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    calculate_leave_for_employee = fields.Selection([
        ('all', 'All'),
        ('monthly', 'Monthly'),
        ('hourly', 'Hourly'),
    ], string='Calculate Leave For Employee', default='monthly', required=True)
    holiday_status_ids = fields.Many2many('hr.leave.type', string='Time Off Type')