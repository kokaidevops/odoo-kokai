from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class AppraisalPlan(models.Model):
    _name = 'appraisal.plan'
    _description = 'Appraisal Plan'

    activity_type_id = fields.Many2one('mail.activity.type', string='Activity Type', required=True)