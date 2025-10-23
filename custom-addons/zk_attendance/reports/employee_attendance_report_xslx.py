from odoo import _, api, fields, models
from datetime import date, datetime, timedelta
import logging


_logger = logging.getLogger(__name__)


class EmployeeAttendanceReportXlsx(models.AbstractModel):
    _name = 'report.zk_attendance.report_employee_attendance_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    def generate_xlsx_report(self, workbook, data, lines):
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        attendances = data['attendances']
        
        sheet = workbook.add_worksheet('Employee Attendance')

        format1 = workbook.add_format({'font_size': 22, 'bold': True})
        format1.set_align('center')
        
        format2 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#D3D3D3'})
        format2.set_border()
        format2.set_align('center')
        format2.set_align('vcenter')
        format3 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#D91656', 'font_color': 'white'})
        format3.set_border()
        format3.set_align('center')
        format3.set_align('vcenter')
        
        format4 = workbook.add_format({'font_size': 11})
        format4.set_border()
        format4.set_align('center')
        format4.set_align('vcenter')
        
        format5 = workbook.add_format({'font_size': 11})
        format5.set_border()
        format6 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#D91656', 'font_color': 'white'}) # absen
        format6.set_border()
        format7 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#1F509A'}) # telat
        format7.set_border()
        format8 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#FFE31A'}) # cuti
        format8.set_border()
        format9 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#F09319'}) # izin
        format9.set_border()
        format10 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#15B392'}) # sakit surat
        format10.set_border()
        format11 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#605EA1'}) # sakit non surat
        format11.set_border()
        format12 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#80C4E9'}) # dinas luar
        format12.set_border()
        format13 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#85A98F'}) # setengah hari
        format13.set_border()
        format14 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#FAF6E3'}) # sekali absen
        format14.set_border()
        format15 = workbook.add_format({'font_size': 11, 'bold': True})
        format15.set_border()

        sheet.merge_range(0, 0, 1, 0, "No", format2)
        sheet.merge_range(0, 1, 1, 1, "Nama", format2)
        sheet.merge_range(0, 2, 1, 2, "Divisi", format2)
        
        column = 3
        row = 2
        
        months = {}
        column_for_date = {}
        day_count = int((end_date - start_date).days)+1
        for single_date in (start_date + timedelta(n) for n in range(day_count)):
            month = single_date.strftime('%b-%y')
            if not month in months:
                months[month] = 0
            months[month] += 1

            date_number = single_date.strftime('%d')
            weekday = single_date.weekday() in [5,6]
            if weekday:
                sheet.write(1, column, date_number, format3)
            else:
                sheet.write(1, column, date_number, format2)

            column_for_date[single_date.strftime('%Y-%m-%d')] = [column, weekday]
            column += 1

        count_date = 0
        for month in months.keys():
            sheet.merge_range(0, 3+count_date, 0, 3+count_date+months[month]-1, month, format2)
            count_date = months[month]

        sheet.merge_range(0, column, 1, column, "Hari Kerja", format2)
        sheet.merge_range(0, column+1, 1, column+1, "Cuti", format2)
        sheet.merge_range(0, column+2, 1, column+2, "Izin", format2)
        sheet.merge_range(0, column+3, 1, column+3, "Sakit SKD", format2)
        sheet.merge_range(0, column+4, 1, column+4, "Sakit Non SKD", format2)
        sheet.merge_range(0, column+5, 1, column+5, "Terlambat", format2)
        
        number = 1
        for employee in attendances.keys():
            employee_name = attendances[employee][0]
            department = attendances[employee][1]
            
            sheet.write(row, 0, number, format5)
            sheet.write(row, 1, employee_name, format5)
            sheet.write(row, 2, department, format5)
            

            late = 0
            max_late = 3
            for attendance in attendances[employee][2].keys():
                check_in_limit = datetime.strptime(attendance + ' 08:15:00', '%Y-%m-%d %H:%M:%S')
                check_in_limit_tolerance = datetime.strptime(attendance + ' 08:00:00', '%Y-%m-%d %H:%M:%S')

                # recapitulasi
                attendance_time = attendances[employee][2][attendance]
                check_in = datetime.strptime(attendance_time[0][0], '%Y-%m-%d %H:%M:%S')
                check_out = datetime.strptime(attendance_time[len(attendance_time)-1][0], '%Y-%m-%d %H:%M:%S')
                
                total_seconds = (check_out-check_in).seconds
                hours = total_seconds//3600
                minutes = (total_seconds%3600)//60
                seconds = total_seconds%60

                if check_in > check_in_limit_tolerance and check_in <= check_in_limit:
                    late += 1

                if column_for_date[attendance][1]:
                    sheet.write(row, column_for_date[attendance][0], '√', format6)
                else:
                    if hours == 0:
                        sheet.write(row, column_for_date[attendance][0], '√', format14)
                    elif hours > 0 and hours <= 6:
                        sheet.write(row, column_for_date[attendance][0], '√', format13)
                    elif check_in > check_in_limit or max_late > 3:
                        sheet.write(row, column_for_date[attendance][0], '√', format7)
                    else:
                        sheet.write(row, column_for_date[attendance][0], '√', format15)

                comment = f"Check In Time: {attendance_time[0][0]} \n Check Out Time: {attendance_time[len(attendance_time)-1][0]}  \n Working Time: {hours} Jam {minutes} Menit {seconds} Detik"
                sheet.write_comment(row, column_for_date[attendance][0], comment)

            row += 1
            number += 1

        row += 2
        sheet.write(row, 1, "Keterangan", format5)
        sheet.write(row+1, 1, "Absen", format5)
        sheet.write(row+2, 1, "Cuti", format5)
        sheet.write(row+3, 1, "Izin", format5)
        sheet.write(row+4, 1, "Sakit Surat", format5)
        sheet.write(row+5, 1, "Sakit Non Surat", format5)
        sheet.write(row+6, 1, "Telat", format5)
        sheet.write(row+7, 1, "Dinas Luar", format5)
        sheet.write(row+8, 1, "Setengah Hari", format5)
        sheet.write(row+9, 1, "Sekali Absen", format5)
        sheet.write(row+1, 2, "", format6)
        sheet.write(row+2, 2, "", format8)
        sheet.write(row+3, 2, "", format9)
        sheet.write(row+4, 2, "", format10)
        sheet.write(row+5, 2, "", format11)
        sheet.write(row+6, 2, "", format7)
        sheet.write(row+7, 2, "", format12)
        sheet.write(row+8, 2, "", format13)
        sheet.write(row+9, 2, "", format14)