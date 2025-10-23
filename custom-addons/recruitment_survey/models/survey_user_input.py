from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    user_input_id = fields.Many2one('survey.user_input', string='User Input')


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    job_id = fields.Many2one('hr.job', string='Job Position')


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    category_id = fields.Many2one('survey.category', string='Category', related='survey_id.category_id')
    applicant_id = fields.Many2one('hr.applicant', string='Applicant')

    def _prepare_recruitment_data(self):
        self.ensure_one()
        return {
            'user_input_id': self.id,
            'job_id': self.survey_id.job_id.id,
            'department_id': self.survey_id.job_id.department_id.id,
            'partner_name': '',
            'name': '',
            'email_from': '',
            'partner_mobile': '',
            'linkedin_profile': '',
            'type_id': '', # degree
            'salary_expected': '',
            'salary_proposed': '',
            'availability': '', # date available to start working
            'description': '',
            # 'skills': '',
        }

    def post_to_recruitment(self):
        self.ensure_one()
        if not self.survey_id.category_id == self.env.ref('recruitment_survey.survey_category_data_recruitment_profile').id:
            raise ValidationError("Can't set to applicant profile because this survey not for survey recruitment!")
        if self.applicant_id:
            raise ValidationError("Can't create duplicate applicant profile!")
        try:
            data = self._prepare_recruitment_data()
            applicant = self.env['hr.applicant'].create(data)
            self.write({ 'applicant_id': applicant.id })
        except Exception as e:
            raise ValidationError(f"Can't set to applicant profile, {e}")
        