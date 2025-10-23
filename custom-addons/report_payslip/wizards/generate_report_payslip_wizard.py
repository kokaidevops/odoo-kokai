from odoo import _, api, fields, models
import logging


_logger = logging.getLogger(__name__)


class GenerateReportPayslipWizard(models.TransientModel):
    _name = 'generate.report.payslip.wizard'
    _description = 'Generate Report Payslip Wizard'

    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batch', required=True)
    type = fields.Selection([
        ('salary', 'LAPORAN GAJI KARYAWAN'),
        ('healthy', 'LAPORAN BPJS KESEHATAN KARYAWAN'),
        ('employment', 'LAPORAN BPJS TK KARYAWAN'),
        ('tax', 'LAPORAN PPH 21 KARYAWAN'),
        ('complete', 'LAPORAN GAJI KARYAWAN'),
    ], string='Report Type', default='complete', required=True)

    def action_generate(self):
        insurances = {}
        hr_insurance = self.env['hr.insurance'].search([ ('active', '=', True) ])
        for line in hr_insurance:
            insurances[line.code.lower()] = f"{line.rate}%"

        data = {
            'report_type': self.type,
            'name': self.payslip_run_id.name,
            'working_days': '',
            'title': dict(self._fields['type'].selection).get(self.type),
            'data': {},
            'insurances': insurances,
        }

        for payslip in self.payslip_run_id.slip_ids:
            employee = payslip.employee_id
            department_name = employee.department_id.name
            if not department_name in data['data']:
                data['data'][department_name] = {}
            _logger.warning("employee.name: %s" % str(employee.name))

            employee_dict = {
                'registration_number': employee.registration_number or "",
                'name': employee.name,
                'tax_number': employee.tin or "",
                'gender': dict(employee._fields['gender'].selection).get(employee.gender),
                'aer': employee.hr_employee_aer_id.name if employee.hr_employee_aer_id else "",
                'aer_cat': employee.aer_id.name if employee.aer_id else "",
                'contract_type': employee.contract_type_id.code,
                'department': department_name,
                'job_position': "%s %s" % (employee.job_level_id.name, employee.job_id.name),
                'service_start_date': employee.service_start_date.strftime("%d-%b-%Y") if employee.service_start_date else "",
                'service_end_date': "",
                'desc1': "",
                'gross': 0,
            }

            if self.type in ['complete', 'salary']:
                employee_dict.update({
                    'working_days': sum([line.number_of_days for line in payslip.worked_days_line_ids.filtered(lambda line: line.amount > 0)]),
                    'prorate': '',
                    'day_wage': payslip.contract_id.over_day if payslip.contract_id.wage_type == 'hourly' else "",
                    'basic_salary': payslip.contract_id.basic_salary if payslip.contract_id.wage_type == 'monthly' else sum([line.amount for line in payslip.worked_days_line_ids]),
                    'wage': 0,
                    'ot': 0,
                    'ptop': 0,
                    'compensation': 0,
                    'att_ded': 0,
                    'late': 0,
                    'deduction': 0,
                    'ins_emp': 0,
                    'tax_emp': 0,
                    'net': 0,
                    'work_location': employee.work_location_id.name if employee.work_location_id else "",
                    'bank': employee.bank_account_id.bank_id.name,
                    'account_number': employee.bank_account_id.acc_number,
                    'account_holder': employee.bank_account_id.acc_holder_name,
                    'desc2': "",
                })
                for allowance in payslip.contract_id.allowance_ids:
                    employee_dict.update({ allowance.allowance_id.code.lower(): allowance.value })
            if self.type in ['healthy', 'employment', "complete"]:
                employee_dict.update({
                    'minimum_wage': self.env.company.minimum_wage_id.value,
                    'max_pens_cont': self.env.company.max_pens_cont_id.value,
                    'max_health_ins': self.env.company.max_health_ins_id.value,
                    'gross_tax_emp': 0,
                    'employment': '',
                    'healthy': '',
                    'ins_comp': 0,
                    'ins_emp': 0,
                })
            if self.type in ['complete', 'healthy']:
                for insurance in payslip.contract_id.insurance_ids.filtered(lambda insurance: insurance.insurance_id.insurance_type == 'healthy'):
                    if insurance.rate > 0:
                        employee_dict.update({ 'healthy': 1 })
                    employee_dict.update({ insurance.insurance_id.code.lower(): 0 })
            if self.type in ['complete', 'employment']:
                for insurance in payslip.contract_id.insurance_ids.filtered(lambda insurance: insurance.insurance_id.insurance_type == 'employment'):
                    if insurance.rate > 0:
                        employee_dict.update({ 'employment': 1 })
                    employee_dict.update({ insurance.insurance_id.code.lower(): 0 })
            if self.type in ['complete', 'tax']:
                employee_dict.update({
                    'ins_tax_emp': 0,
                    'income_employee_cover': 0,
                    'income_company_cover': 0,
                    'tax_rate_emp': 0,
                    'tax_rate_comp': 0,
                    'tax_comp': 0,
                    'total_tax': 0,
                    'pm_tax_emp': 0,
                    'pm_tax_comp': 0,
                })
            for line in payslip.line_ids:
                if not line.code.lower() in employee_dict:
                    continue
                employee_dict[line.code.lower()] += float(line.total)
            employee_dict.update({ 
                'ins_emp_summary': employee_dict['ins_emp'],
                'tax_emp_summary': employee_dict['tax_emp'],
                'total_tax': employee_dict['tax_emp'] + employee_dict['pm_tax_emp'],
                'gross_tax': employee_dict['gross_tax_emp'],
                'ins_comp': employee_dict['jkk_comp'] + employee_dict['jk_comp'] + employee_dict['jht_comp'] + employee_dict['jp_comp'] + employee_dict['bpjsk_comp'] + employee_dict['ins_emp'],
                'income_employee_cover': employee_dict['gross_tax_emp'] + employee_dict['ins_tax_emp'],
                'total_induction': employee_dict['ot'] + employee_dict['ptop'] + employee_dict['compensation'],
                'total_deduction': employee_dict['late'] + employee_dict['att_ded'] + employee_dict['deduction'],
            })
            data['data'][department_name][employee.id] = employee_dict

        return self.env.ref('report_payslip.action_report_payslip_batch_xlsx').report_action(self, data=data)