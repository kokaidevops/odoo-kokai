import os
import base64, binascii, csv, io, tempfile, requests, xlrd
from odoo import fields, models, _
from odoo.exceptions import UserError
import logging
import datetime


_logger = logging.getLogger(__name__)


class ImportEmployeeFingerprint(models.TransientModel):
    _name = 'import.employee.fingerprint'
    _description = 'Import Employee Fingerprint'

    file = fields.Binary('File Excel')

    def action_import(self):
        try:
            try:
                file_pointer = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                file_pointer.write(binascii.a2b_base64(self.file))
                file_pointer.seek(0)
                workbook = xlrd.open_workbook(file_pointer.name)
                sheet = workbook.sheet_by_index(0)
            except:
                raise UserError(_("File not Valid"))
            for rec in range(sheet.nrows):
                if rec >= 1:
                    row_vals = sheet.row_values(rec)
                    if len(row_vals) < int(2):
                        raise UserError(_("Please ensure that you selected the correct file"))

                    employee = self.env['hr.employee'].search([
                        ('name', '=', row_vals[1])
                    ], limit=1)
                    if not employee:
                        # continue
                        raise UserError(_(f"Employee {row_vals[1]} not Found"))
                    
                    self.env['hr.employee.fingerprint'].create({
                        'pin': row_vals[0],
                        'device_id': 1,
                        'employee_id': employee.id,
                    })

        except UserError as e:
            raise UserError(str(e))