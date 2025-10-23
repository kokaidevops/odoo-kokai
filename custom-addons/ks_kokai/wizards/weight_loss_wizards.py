from odoo import models, fields, api
import json

class WeightLossAnalysisWizard(models.TransientModel):
    _name = 'weight.loss.analysis.wizard'
    _description = 'Weight Loss Analysis Wizard'
    
    date_from = fields.Date(
        string='From Date',
        required=True,
        default=fields.Date.today
    )
    
    date_to = fields.Date(
        string='To Date',
        required=True,
        default=fields.Date.today
    )
    
    product_ids = fields.Many2many(
        'product.product',
        string='Products',
        domain=[('track_weight_by_serial', '=', True)]
    )
    
    analysis_data = fields.Text(
        string='Analysis Data',
        compute='_compute_analysis'
    )
    
    @api.depends('date_from', 'date_to', 'product_ids')
    def _compute_analysis(self):
        for wizard in self:
            domain = [
                ('date_start', '>=', wizard.date_from),
                ('date_start', '<=', wizard.date_to),
                ('state', '=', 'done')
            ]
            
            if wizard.product_ids:
                domain.append(('product_id', 'in', wizard.product_ids.ids))
            
            productions = self.env['mrp.production'].search(domain)
            
            analysis = {
                'total_productions': len(productions),
                'total_input_weight': sum(p.total_input_weight for p in productions),
                'total_output_weight': sum(p.total_output_weight for p in productions),
                'total_weight_loss': sum(p.actual_weight_loss for p in productions),
                'average_loss_percentage': sum(p.actual_weight_loss_percentage for p in productions) / len(productions) if productions else 0,
                'productions_over_tolerance': len(productions.filtered(lambda p: abs(p.weight_variance) > p.product_id.weight_tolerance)),
            }
            
            wizard.analysis_data = json.dumps(analysis)
    
    def action_print_report(self):
        self.ensure_one()
        return self.env.ref('weight_tracking_production.action_weight_loss_report').report_action(self)