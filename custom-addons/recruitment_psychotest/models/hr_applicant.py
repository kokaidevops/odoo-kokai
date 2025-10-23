from odoo import _, api, fields, models


class HRApplicant(models.Model):
    _inherit = 'hr.applicant'

    test_results_ids = fields.One2many('recruitment.test', 'applicant_id', string='Test Results')
    test_result_file = fields.Binary('File')