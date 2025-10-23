from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class GenerateProductWizard(models.TransientModel):
    _name = 'generate.product.wizard'
    _description = 'Generate Product Wizard'
    
    def _prepare_product_vals(self, fg_category):
        res = super()._prepare_product_vals(fg_category)
        res['base_product_id'] = self.product_tmpl_id.id
        return res