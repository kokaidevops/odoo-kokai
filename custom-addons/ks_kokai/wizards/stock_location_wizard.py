from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)

class StockLocationWizard(models.TransientModel):

    _name = 'kokai.stock.location.wizard'
    _description = 'Stock Location Details'
    
    rab_id = fields.Many2one('kokai.rab', string='RAB', required=True)
    line_ids = fields.One2many('kokai.stock.location.wizard.line', 'wizard_id', string='Stock Details')
    
    @api.model
    def default_get(self, fields):
        res = super(StockLocationWizard, self).default_get(fields)
        if self.env.context.get('active_id'):
            rab = self.env['kokai.rab'].browse(self.env.context['active_id'])
            lines = []
            for rab_line in rab.rab_line_ids:
                if rab_line.product_id and rab_line.is_stockable:
                    lines.append((0, 0, {
                        'product_id': rab_line.product_id.id,
                        'quantity_needed': rab_line.quantity,
                        'stock_details': rab_line.stock_by_location,
                        'total_available': rab_line.stock_available_all_locations,
                        'status': rab_line.stock_status,
                    }))
            res['line_ids'] = lines
            res['rab_id'] = rab.id
        return res

class StockLocationWizardLine(models.TransientModel):
    _name = 'kokai.stock.location.wizard.line'
    _description = 'Stock Location Detail Line'
    
    wizard_id = fields.Many2one('kokai.stock.location.wizard', required=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    quantity_needed = fields.Float(string='Qty Needed', readonly=True)
    total_available = fields.Float(string='Total Available', readonly=True)
    stock_details = fields.Text(string='Stock by Location', readonly=True)
    status = fields.Selection([
        ('available', 'Available'),
        ('partial', 'Partial'),
        ('out_of_stock', 'Out of Stock'),
        ('na', 'N/A')
    ], string='Status', readonly=True)