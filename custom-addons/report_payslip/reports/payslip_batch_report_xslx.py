from odoo import _, api, fields, models
from datetime import date, datetime, timedelta
import logging


_logger = logging.getLogger(__name__)

HEADER_COLUMN = {
    "sequence":{"title":"NO. URUT","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":0,"end_column":0,"report_type":["salary","healthy","employment","tax","complete"]},
    "sequence_dept":{"title":"NO. DEPT.","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":1,"end_column":1,"report_type":["salary","healthy","employment","tax","complete"]},
    "registration_number":{"title":"NIK","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":2,"end_column":2,"report_type":["salary","healthy","employment","tax","complete"]},
    "name":{"title":"NAMA","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":3,"end_column":3,"report_type":["salary","healthy","employment","tax","complete"]},
    "tax_number":{"title":"NPWP","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":4,"end_column":4,"report_type":["salary","healthy","employment","tax","complete"]},
    "gender":{"title":"JENIS KELAMIN","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":5,"end_column":5,"report_type":["salary","healthy","employment","tax","complete"]},
    "aer":{"title":"STATUS KAWIN","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":6,"end_column":6,"report_type":["salary","healthy","employment","tax","complete"]},
    "contract_type":{"title":"STATUS KERJA","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":7,"end_column":7,"report_type":["salary","healthy","employment","tax","complete"]},
    "department":{"title":"DEPT","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":8,"end_column":8,"report_type":["salary","healthy","employment","tax","complete"]},
    "job_position":{"title":"JABATAN","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":9,"end_column":9,"report_type":["salary","healthy","employment","tax","complete"]},
    "service_start_date":{"title":"TGL MASUK","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":10,"end_column":10,"report_type":["salary","healthy","employment","tax","complete"]},
    "service_end_date":{"title":"TGL KELUAR","value_format":"format2","format":"format2","start_row":0,"end_row":2,"start_column":11,"end_column":11,"report_type":["salary","healthy","employment","tax","complete"]},
    "desc1":{"title":"KETERANGAN","value_format":"format2","format":"format3","start_row":0,"end_row":2,"start_column":12,"end_column":12,"report_type":["salary","healthy","employment","tax","complete"]},
    "working_days":{"title":"JUMLAH HARI KERJA","value_format":"format2","format":"format4","start_row":0,"end_row":2,"start_column":14,"end_column":14,"report_type":["salary","complete"]},
    "prorate":{"title":"NILAI PRORATE","value_format":"format2","format":"format4","start_row":0,"end_row":2,"start_column":15,"end_column":15,"report_type":["salary","complete"]},
    "day_wage":{"title":"TARIF GAJI PHL","value_format":"format2","format":"format4","start_row":0,"end_row":2,"start_column":16,"end_column":16,"report_type":["salary","complete"]},
    "title1":{"title":"UPAH & TUNJANGAN ","value_format":"format2","format":"format2","start_row":0,"end_row":0,"start_column":18,"end_column":22,"report_type":["salary","complete"]},
    "title2":{"title":"TUNJANGAN TIDAK TETAP","value_format":"format2","format":"format2","start_row":0,"end_row":0,"start_column":23,"end_column":26,"report_type":["salary","complete"]},
    "title3":{"title":"JUMLAH","value_format":"format2","format":"format2","start_row":0,"end_row":0,"start_column":27,"end_column":27,"report_type":["salary","complete"]},
    "title4":{"title":"PENAMBAHAN","value_format":"format2","format":"format2","start_row":0,"end_row":0,"start_column":28,"end_column":30,"report_type":["salary","complete"]},
    "title5":{"title":"JUMLAH","value_format":"format2","format":"format2","start_row":0,"end_row":0,"start_column":31,"end_column":31,"report_type":["salary","complete"]},
    "title6":{"title":"PENGURANGAN","value_format":"format2","format":"format2","start_row":0,"end_row":0,"start_column":32,"end_column":34,"report_type":["salary","complete"]},
    "title7":{"title":"JUMLAH","value_format":"format2","format":"format2","start_row":0,"end_row":0,"start_column":35,"end_column":35,"report_type":["salary","complete"]},
    "title8":{"title":"BEBAN KARYAWAN","value_format":"format2","format":"format2","start_row":0,"end_row":0,"start_column":37,"end_column":38,"report_type":["salary","complete"]},
    "basic_salary":{"title":"GAJI POKOK","value_format":"currency_format","format":"format6","start_row":1,"end_row":2,"start_column":18,"end_column":18,"report_type":["salary","complete"]},
    "positional_allowance":{"title":"TUNJANGAN JABATAN","value_format":"currency_format","format":"format6","start_row":1,"end_row":2,"start_column":19,"end_column":19,"report_type":["salary","complete"]},
    "expertise_allowance":{"title":"TUNJANGAN KEAHLIAN","value_format":"currency_format","format":"format6","start_row":1,"end_row":2,"start_column":20,"end_column":20,"report_type":["salary","complete"]},
    "health_allowance":{"title":"TUNJANGAN KESEHATAN","value_format":"currency_format","format":"format6","start_row":1,"end_row":2,"start_column":21,"end_column":21,"report_type":["salary","complete"]},
    "telephone_allowance":{"title":"TUNJANGAN TELEPON","value_format":"currency_format","format":"format6","start_row":1,"end_row":2,"start_column":22,"end_column":22,"report_type":["salary","complete"]},
    "meal_allowance":{"title":"UANG MAKAN","value_format":"currency_format","format":"format6","start_row":1,"end_row":2,"start_column":23,"end_column":23,"report_type":["salary","complete"]},
    "transportation_money":{"title":"UANG TRANPORT","value_format":"currency_format","format":"format6","start_row":1,"end_row":2,"start_column":24,"end_column":24,"report_type":["salary","complete"]},
    "craft_money":{"title":"UANG KERAJINAN","value_format":"currency_format","format":"format6","start_row":1,"end_row":2,"start_column":25,"end_column":25,"report_type":["salary","complete"]},
    "ot_package":{"title":"LEMBUR PAKET","value_format":"currency_format","format":"format6","start_row":1,"end_row":2,"start_column":26,"end_column":26,"report_type":["salary","complete"]},
    "wage":{"title":"UPAH & TUNJ (PRORATE)","value_format":"currency_format","format":"format6","start_row":1,"end_row":2,"start_column":27,"end_column":27,"report_type":["salary","complete"]},
    "ot":{"title":"LEMBUR","value_format":"currency_format","format":"format3","start_row":1,"end_row":2,"start_column":28,"end_column":28,"report_type":["salary","complete"]},
    "ptop":{"title":"P. SISA CUTI","value_format":"currency_format","format":"format3","start_row":1,"end_row":2,"start_column":29,"end_column":29,"report_type":["salary","complete"]},
    "compensation":{"title":"KOMPENSASI (LAIN-LAIN)","value_format":"currency_format","format":"format3","start_row":1,"end_row":2,"start_column":30,"end_column":30,"report_type":["salary","complete"]},
    "total_induction":{"title":"PENAMBAHAN","value_format":"currency_format","format":"format3","start_row":1,"end_row":2,"start_column":31,"end_column":31,"report_type":["salary","complete"]},
    "late":{"title":"TELAT","value_format":"currency_format","format":"format7","start_row":1,"end_row":2,"start_column":32,"end_column":32,"report_type":["salary","complete"]},
    "att_ded":{"title":"ABSEN","value_format":"currency_format","format":"format7","start_row":1,"end_row":2,"start_column":33,"end_column":33,"report_type":["salary","complete"]},
    "deduction":{"title":"LAINNYA","value_format":"currency_format","format":"format7","start_row":1,"end_row":2,"start_column":34,"end_column":34,"report_type":["salary","complete"]},
    "total_deduction":{"title":"PENGURANGAN","value_format":"currency_format","format":"format7","start_row":1,"end_row":2,"start_column":35,"end_column":35,"report_type":["salary","complete"]},
    "gross":{"title":"GAJI BRUTO","value_format":"currency_format","format":"format6","start_row":0,"end_row":2,"start_column":36,"end_column":36,"report_type":["salary","healthy","employment","tax","complete"]},
    "ins_emp_summary":{"title":"POT BPJS KARYAWAN","value_format":"format2","format":"format8","start_row":1,"end_row":2,"start_column":37,"end_column":37,"report_type":["salary","complete"]},
    "tax_emp_summary":{"title":"POT PPH 21","value_format":"format2","format":"format8","start_row":1,"end_row":2,"start_column":38,"end_column":38,"report_type":["salary","complete"]},
    "net":{"title":"TOTAL GAJI YANG HARUS DIBAYAR","value_format":"currency_format","format":"format6","start_row":0,"end_row":2,"start_column":39,"end_column":39,"report_type":["salary","complete"]},
    "work_location":{"title":"LOKASI KERJA","value_format":"format2","format":"format3","start_row":0,"end_row":2,"start_column":41,"end_column":41,"report_type":["salary","complete"]},
    "bank":{"title":"BANK","value_format":"format2","format":"format3","start_row":0,"end_row":2,"start_column":42,"end_column":42,"report_type":["salary","complete"]},
    "account_number":{"title":"NO. REKENING","value_format":"format2","format":"format3","start_row":0,"end_row":2,"start_column":43,"end_column":43,"report_type":["salary","complete"]},
    "account_holder":{"title":"NAMA PEMILIK REKENING","value_format":"format2","format":"format3","start_row":0,"end_row":2,"start_column":44,"end_column":44,"report_type":["salary","complete"]},
    "desc2":{"title":"KETERANGAN","value_format":"format2","format":"format3","start_row":0,"end_row":2,"start_column":45,"end_column":45,"report_type":["salary","complete"]},
    "title9":{"title":"2025","value_format":"format2","format":"format6","start_row":2,"end_row":2,"start_column":47,"end_column":48,"report_type":["healthy","employment","complete"]},
    "title10":{"title":"PROGRAM BPJS 1 = Ya ; 0 = Tidak","value_format":"format2","format":"format9","start_row":0,"end_row":1,"start_column":49,"end_column":50,"report_type":["healthy","employment","complete"]},
    "title11":{"title":"2025","value_format":"format2","format":"format6","start_row":2,"end_row":2,"start_column":51,"end_column":52,"report_type":["healthy","employment","complete"]},
    "minimum_wage":{"title":"GAJI BPJS TK","value_format":"currency_format","format":"format6","start_row":0,"end_row":1,"start_column":47,"end_column":47,"report_type":["healthy","employment","complete"]},
    "gross_tax_emp":{"title":"GAJI BPJS KES","value_format":"currency_format","format":"format6","start_row":0,"end_row":1,"start_column":48,"end_column":48,"report_type":["healthy","employment","complete"]},
    "employment":{"title":"BPJS TK","value_format":"currency_format","format":"format11","start_row":2,"end_row":2,"start_column":49,"end_column":49,"report_type":["healthy","employment","complete"]},
    "healthy":{"title":"BPJS KESEHATAN","value_format":"currency_format","format":"format10","start_row":2,"end_row":2,"start_column":50,"end_column":50,"report_type":["healthy","employment","complete"]},
    "max_pens_cont":{"title":"GAJI MAX IUR PENSIUN","value_format":"currency_format","format":"format6","start_row":0,"end_row":1,"start_column":51,"end_column":51,"report_type":["healthy","employment","complete"]},
    "max_health_ins":{"title":"GAJI MAX IUR BPJS KESEHATAN","value_format":"currency_format","format":"format6","start_row":0,"end_row":1,"start_column":52,"end_column":52,"report_type":["healthy","employment","complete"]},
    "insurance1":{"title":"JAM. KEC KERJA","value_format":"format2","format":"format11","start_row":0,"end_row":0,"start_column":54,"end_column":54,"report_type":["employment","complete"]},
    "insurance2":{"title":"JAMINAN KEMATIAN","value_format":"format2","format":"format11","start_row":0,"end_row":0,"start_column":55,"end_column":55,"report_type":["employment","complete"]},
    "insurance3":{"title":"JAMINAN HARI TUA","value_format":"format2","format":"format11","start_row":0,"end_row":0,"start_column":56,"end_column":57,"report_type":["employment","complete"]},
    "insurance4":{"title":"JAMINAN PENSIUN","value_format":"format2","format":"format11","start_row":0,"end_row":0,"start_column":58,"end_column":59,"report_type":["employment","complete"]},
    "insurance5":{"title":"BPJS KESEHATAN","value_format":"format2","format":"format10","start_row":0,"end_row":0,"start_column":60,"end_column":61,"report_type":["employment","complete"]},
    "insurance6":{"title":"BPJS YANG DIBAYARKAN","value_format":"format2","format":"format9","start_row":0,"end_row":0,"start_column":62,"end_column":63,"report_type":["employment","complete"]},
    "jkk_comp":{"title":"PERUSAHAAN","value_format":"currency_format","format":"format7","start_row":1,"end_row":1,"start_column":54,"end_column":54,"report_type":["employment","complete"]},
    "jk_comp":{"title":"PERUSAHAAN","value_format":"currency_format","format":"format7","start_row":1,"end_row":1,"start_column":55,"end_column":55,"report_type":["employment","complete"]},
    "jht_comp":{"title":"PERUSAHAAN","value_format":"currency_format","format":"format7","start_row":1,"end_row":1,"start_column":56,"end_column":56,"report_type":["employment","complete"]},
    "jht_emp":{"title":"KARYAWAN","value_format":"currency_format","format":"format8","start_row":1,"end_row":1,"start_column":57,"end_column":57,"report_type":["employment","complete"]},
    "jp_comp":{"title":"PERUSAHAAN","value_format":"currency_format","format":"format7","start_row":1,"end_row":1,"start_column":58,"end_column":58,"report_type":["employment","complete"]},
    "jp_emp":{"title":"KARYAWAN","value_format":"currency_format","format":"format8","start_row":1,"end_row":1,"start_column":59,"end_column":59,"report_type":["employment","complete"]},
    "bpjsk_comp":{"title":"PERUSAHAAN","value_format":"currency_format","format":"format7","start_row":1,"end_row":1,"start_column":60,"end_column":60,"report_type":["healthy","complete"]},
    "bpjsk_emp":{"title":"KARYAWAN","value_format":"currency_format","format":"format8","start_row":1,"end_row":1,"start_column":61,"end_column":61,"report_type":["healthy","complete"]},
    "ins_comp":{"title":"PERUSAHAAN","value_format":"currency_format","format":"format7","start_row":1,"end_row":2,"start_column":62,"end_column":62,"report_type":["healthy","employment","complete"]},
    "ins_emp":{"title":"KARYAWAN","value_format":"currency_format","format":"format8","start_row":1,"end_row":2,"start_column":63,"end_column":63,"report_type":["healthy","employment","complete"]},
    "gross_tax":{"title":"GAJI BRUTO","value_format":"currency_format","format":"format3","start_row":0,"end_row":2,"start_column":65,"end_column":65,"report_type":["tax","complete"]},
    "ins_tax_emp":{"title":"BPJS YG DITANGGUNG PERUSAHAAN","value_format":"currency_format","format":"format3","start_row":0,"end_row":2,"start_column":66,"end_column":66,"report_type":["tax","complete"]},
    "income_employee_cover":{"title":"JUMLAH PENGHASILAN SEBULAN (PPH DITANGGUNG KARYAWAN)","value_format":"currency_format","format":"format3","start_row":0,"end_row":2,"start_column":67,"end_column":67,"report_type":["tax","complete"]},
    "income_company_cover":{"title":"JUMLAH PENGHASILAN SEBULAN (PPH DITANGGUNG PERUSAHAAN","value_format":"currency_format","format":"format3","start_row":0,"end_row":2,"start_column":68,"end_column":68,"report_type":["tax","complete"]},
    "aer_cat":{"title":"KATEGORI TER","value_format":"currency_format","format":"format6","start_row":0,"end_row":2,"start_column":69,"end_column":69,"report_type":["tax","complete"]},
    "tax_rate_emp":{"title":"TARIF TER (PPH DITANGGUNG KARYAWAN)","value_format":"currency_format","format":"format6","start_row":0,"end_row":2,"start_column":70,"end_column":70,"report_type":["tax","complete"]},
    "tax_rate_comp":{"title":"TARIF TER (PPH DITANGGUNG PERUSAHAAN)","value_format":"currency_format","format":"format6","start_row":0,"end_row":2,"start_column":71,"end_column":71,"report_type":["tax","complete"]},
    "tax_emp":{"title":"PPH TERHUTANG 1 BULAN KARYAWAN","value_format":"currency_format","format":"format12","start_row":0,"end_row":2,"start_column":72,"end_column":72,"report_type":["tax","complete"]},
    "tax_comp":{"title":"PPH TERHUTANG 1 BULAN PERUSAHAAN","value_format":"currency_format","format":"format12","start_row":0,"end_row":2,"start_column":73,"end_column":73,"report_type":["tax","complete"]},
    "pm_tax_emp":{"title":"PPH LEBIH/KURANG BAYAR PERIODE SEBELUMNYA KARYAWAN","value_format":"currency_format","format":"format12","start_row":0,"end_row":2,"start_column":74,"end_column":74,"report_type":["tax","complete"]},
    "pm_tax_comp":{"title":"PPH LEBIH/KURANG BAYAR PERIODE SEBELUMNYA PERUSAHAAN","value_format":"currency_format","format":"format12","start_row":0,"end_row":2,"start_column":75,"end_column":75,"report_type":["tax","complete"]},
    "total_tax":{"title":"PPH YANG HARUS DIBAYAR KARYAWAN","value_format":"currency_format","format":"format13","start_row":0,"end_row":2,"start_column":76,"end_column":76,"report_type":["tax","complete"]}
}


class PayslipBatchReportXlsx(models.AbstractModel):
    _name = 'report.report_payslip.report_payslip_batch_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet(data['name'])

        dict_format = {}

        format1 = workbook.add_format({'font_size': 11, 'bold': True})
        dict_format.update({ 'format1': format1 })
        format2 = workbook.add_format({'font_size': 9})
        format2.set_border()
        dict_format.update({ 'format2': format2 })
        format3 = workbook.add_format({'font_size': 9, 'bg_color': '#bdd7ee'})
        format3.set_border()
        dict_format.update({ 'format3': format3 })
        format4 = workbook.add_format({'font_size': 9, 'bg_color': '#f4b183'})
        format4.set_border()
        dict_format.update({ 'format4': format4 })
        format6 = workbook.add_format({'font_size': 9, 'bg_color': '#c5e0b4'})
        format6.set_border()
        dict_format.update({ 'format6': format6 })
        format7 = workbook.add_format({'font_size': 9, 'bg_color': '#ffe699'})
        format7.set_border()
        dict_format.update({ 'format7': format7 })
        format8 = workbook.add_format({'font_size': 9, 'bg_color': '#f8cbad'})
        format8.set_border()
        dict_format.update({ 'format8': format8 })
        format9 = workbook.add_format({'font_size': 9, 'bg_color': '#fff2cc'})
        format9.set_border()
        dict_format.update({ 'format9': format9 })
        format10 = workbook.add_format({'font_size': 9, 'bg_color': '#99ffcc'})
        format10.set_border()
        dict_format.update({ 'format10': format10 })
        format11 = workbook.add_format({'font_size': 9, 'bg_color': '#99ccff'})
        format11.set_border()
        dict_format.update({ 'format11': format11 })
        format12 = workbook.add_format({'font_size': 9, 'bg_color': '#dae3f3'})
        format12.set_border()
        dict_format.update({ 'format12': format12 })
        format13 = workbook.add_format({'font_size': 9, 'bg_color': '#ccffff'})
        format13.set_border()
        dict_format.update({ 'format13': format13 })
        format14 = workbook.add_format({'font_size': 9, 'bold': True, 'bg_color': '#c5e0b4'})
        format14.set_border()
        dict_format.update({ 'format14': format14 })
        format15 = workbook.add_format({'font_size': 9, 'bold': True, 'bg_color': '#ffe699'})
        format15.set_border()
        dict_format.update({ 'format15': format15 })

        # currency format
        company_currency = self.env.user.company_id.currency_id
        currency_symbol = company_currency.symbol
        lang = self.env.user.lang
        lang_data = self.env['res.lang']._lang_get(lang)
        thousands_sep = lang_data.grouping
        decimal_point = lang_data.decimal_point
        currency_format_str = f'{currency_symbol}#,##0{decimal_point}00'
        currency_format = workbook.add_format({'font_size': 9, 'num_format': currency_format_str})
        currency_format.set_border()
        dict_format.update({ 'currency_format': currency_format })


        sheet.merge_range(1, 1, 1, 3, data['title'], format1)
        sheet.merge_range(2, 1, 2, 3, "PERIODE", format1)
        sheet.merge_range(2, 4, 2, 4, "", format1)
        sheet.merge_range(3, 1, 3, 3, "HARI KERJA", format1)
        sheet.merge_range(3, 4, 3, 4, "", format1)
        
        column = 1
        row = 6
        for key in HEADER_COLUMN.keys():
            header = HEADER_COLUMN[key]
            if not data['report_type'] in header['report_type']:
                continue
            if header['start_row'] == header['end_row'] and header['start_column'] == header['end_column']:
                sheet.write(
                    header['start_row']+row, 
                    header['start_column']+column, 
                    header['title'], 
                    dict_format[header['format']],
                )
            else:
                sheet.merge_range(
                    header['start_row']+row, 
                    header['start_column']+column, 
                    header['end_row']+row, 
                    header['end_column']+column, 
                    header['title'], 
                    dict_format[header['format']],
                )

        for insurance in data['insurances'].keys():
            sheet.write(
                8,
                HEADER_COLUMN[insurance]['start_column']+column,
                data['insurances'][insurance],
                dict_format[HEADER_COLUMN[insurance]['format']],
            )

        sequence = 0
        row = 10
        for department in data['data'].keys():
            sequence_dept = 0
            sheet.merge_range(
                row,
                1,
                row,
                13,
                department,
                format14,
            )
            row += 1
            for emp_id in data['data'][department].keys():
                sequence += 1
                sequence_dept += 1
                employee_data = data['data'][department][emp_id]
                employee_data.update({ 'sequence': sequence, 'sequence_dept': sequence_dept })
                for emp_data_key in employee_data.keys():
                    if not emp_data_key in HEADER_COLUMN:
                        continue
                    sheet.write(
                        row,
                        HEADER_COLUMN[emp_data_key]['start_column']+column,
                        employee_data[emp_data_key],
                        dict_format[HEADER_COLUMN[emp_data_key]['value_format']],
                    )
                row += 1
            sheet.merge_range(
                row,
                1,
                row,
                13,
                "JUMLAH %s" % (department),
                format15,
            )
            row += 2