from odoo import _, api, fields, models
import logging, copy


_logger = logging.getLogger(__name__)

class Item(object):
    pass

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_employee_id(self):
        return self.employee_id.registration_number or self.employee_id.identification_id

    def action_print_salary_slip(self):
        return self.env.ref("report_payslip.action_report_salary_slip_py3o").report_action(self, config=False)

    def _get_total_working_days(self):
        self.ensure_one()
        total_working_days = 0
        attendance_days = 0
        sick_time_off_days = 0
        time_off_days = 0
        special_time_off_days = 0
        unpaid_days = 0

        attendance_work_type = ['WORK100', 'WORK110', 'WORK150']
        sick_time_off_work_type = ['LEAVE110']
        time_off_work_type = ['LEAVE120']
        special_time_off_work_type = ['LEAVE105']
        unpaid_work_type = ['LEAVE115', 'LEAVE90']

        attendance_days = sum([line.number_of_days for line in self.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id.code in attendance_work_type)])
        if self.contract_id.wage_type == 'monthly':
            sick_time_off_days = sum([line.number_of_days for line in self.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id.code in sick_time_off_work_type)])
            time_off_days = sum(line.number_of_days for line in self.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id.code in time_off_work_type))
            special_time_off_days = sum(line.number_of_days for line in self.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id.code in special_time_off_work_type))
            unpaid_days = sum(line.number_of_days for line in self.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id.code in unpaid_work_type))
        total_working_days = attendance_days + sick_time_off_days + time_off_days + unpaid_days + special_time_off_days

        allocation_time_off = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'validate'),
            ('holiday_status_id', '=', self.env.ref('hr_holidays.holiday_status_cl').id)
        ], limit=1)
        allocation_time_off_period = "%s - %s" % (allocation_time_off.date_from.strftime("%d %b %Y"), allocation_time_off.date_to.strftime("%d %b %Y")) if allocation_time_off else '-'
        allocation_time_off_days = allocation_time_off.number_of_days if allocation_time_off else 0
        usage_time_off_days = allocation_time_off.allocation_usage if allocation_time_off else 0
        remaining_time_off_days = allocation_time_off.remaining_days if allocation_time_off else 0

        return {
            'total_working_days': total_working_days,
            'attendance_days': attendance_days,
            'sick_time_off_days': sick_time_off_days,
            'time_off_days': time_off_days,
            'special_time_off_days': special_time_off_days,
            'all_time_off_days': time_off_days + special_time_off_days,
            'unpaid_days': unpaid_days,
            'allocation_time_off_period': allocation_time_off_period,
            'allocation_time_off_days': allocation_time_off_days,
            'usage_time_off_days': usage_time_off_days,
            'remaining_time_off_days': remaining_time_off_days,
        }

    def _get_income_payslip(self):
        income = {}
        total = 0

        basic_wage = sum([line.amount for line in self.line_ids.filtered(lambda line: line.salary_rule_id.code == 'BASIC')])
        total += basic_wage
        income['basic_wage'] = basic_wage

        for allowance in self.contract_id.allowance_ids:
            income[allowance.allowance_id.code.lower()] = allowance.value
            total += allowance.value

        overtime = sum([line.amount for line in self.line_ids.filtered(lambda line: line.salary_rule_id.code == 'OT')])
        total += overtime
        income['overtime'] = overtime

        pto_payout = sum([line.amount for line in self.line_ids.filtered(lambda line: line.salary_rule_id.code == 'PTOP')])
        total += pto_payout
        income['pto_payout'] = pto_payout

        compensation = sum([line.amount for line in self.line_ids.filtered(lambda line: line.salary_rule_id.code == 'COMPENSATION')])
        total += compensation
        income['compensation'] = compensation

        income['total'] = total
        return income

    def _get_deduction_payslip(self):
        outcome = {}
        total = 0

        unpaid = sum([line.amount for line in self.line_ids.filtered(lambda line: line.salary_rule_id.code == 'ATT_DED')])
        total += unpaid
        outcome['unpaid'] = unpaid

        bpjs_kes = sum([line.amount for line in self.line_ids.filtered(lambda line: line.salary_rule_id.code == 'BPJSK_EMP')])
        total += bpjs_kes
        outcome['bpjs_kes'] = bpjs_kes

        jht = sum([line.amount for line in self.line_ids.filtered(lambda line: line.salary_rule_id.code == 'JHT_EMP')])
        total += jht
        outcome['jht'] = jht

        dana_pensiun = sum([line.amount for line in self.line_ids.filtered(lambda line: line.salary_rule_id.code == 'JP_EMP')])
        total += dana_pensiun
        outcome['dana_pensiun'] = dana_pensiun

        tax = sum([line.amount for line in self.line_ids.filtered(lambda line: line.salary_rule_id.code == 'TAX_EMP')])
        total += tax
        outcome['tax'] = tax

        deduction = sum([line.amount for line in self.line_ids.filtered(lambda line: line.salary_rule_id.code == 'DEDUCTION')])
        total += deduction
        outcome['deduction'] = deduction

        outcome['total'] = total
        return outcome

    def currency_format(self, number=0):
        # res = ""
        # for rec in self:
            # if rec.currency_id.position == "before":
            #     res = rec.currency_id.symbol + " {:20,.0f}".format(number)
            # else:
            #     res = "{:20,.0f} ".format(number) + rec.currency_id.symbol
        return "{:20,.0f} ".format(number)
    
    def _get_today(self):
        return fields.Date.today().strftime("%d-%b-%Y")

    def _get_bank_account(self):
        return self.employee_id.bank_account_id.display_name if self.employee_id.bank_account_id else ''


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def generate_report(self):
        ctx = dict(default_payslip_run_id=self.id, active_ids=self.ids)
        return {
            'name': _('Generate Report Payslip'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'generate.report.payslip.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }