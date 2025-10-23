# # -*- coding: utf-8 -*-
# # wizard/account_budget_pnl_report.py

# from odoo import models, fields, api, _
# from odoo.exceptions import UserError
# import base64
# from io import BytesIO
# from datetime import datetime, date
# import logging

# _logger = logging.getLogger(__name__)

# try:
#     import xlsxwriter
# except ImportError:
#     _logger.warning('xlsxwriter library is not installed. P&L Excel export will not work.')
#     xlsxwriter = None

# class AccountBudgetPnlReport(models.TransientModel):
#     """P&L Report with Budget vs Actual Comparison"""
#     _name = 'account.budget.pnl.report'
#     _description = 'Profit & Loss Budget vs Actual Report'
    
#     # Basic fields
#     date_from = fields.Date(
#         string='Start Date',
#         required=True,
#         default=lambda self: date(date.today().year, 1, 1)
#     )
#     date_to = fields.Date(
#         string='End Date', 
#         required=True,
#         default=fields.Date.today
#     )
#     company_id = fields.Many2one(
#         'res.company',
#         string='Company',
#         required=True,
#         default=lambda self: self.env.company
#     )
#     budget_ids = fields.Many2many(
#         'crossovered.budget',
#         string='Budgets',
#         help='Select specific budgets. Leave empty for all budgets in period.'
#     )
    
#     def action_generate_excel(self):
#         """Generate Excel P&L Report with Budget vs Actual"""
#         self.ensure_one()
        
#         if not xlsxwriter:
#             raise UserError(_('Please install xlsxwriter library: pip install xlsxwriter'))
        
#         # Create Excel file
#         output = BytesIO()
#         workbook = xlsxwriter.Workbook(output, {'in_memory': True})
#         worksheet = workbook.add_worksheet('Profit and Loss')
        
#         # Define formats
#         formats = self._get_formats(workbook)
        
#         # Set column widths
#         worksheet.set_column('A:A', 40)  # Description
#         worksheet.set_column('B:B', 15)  # Planning
#         worksheet.set_column('C:C', 15)  # Actual
#         worksheet.set_column('D:D', 15)  # Variance
#         worksheet.set_column('E:E', 10)  # %
        
#         # Write report
#         self._write_report(worksheet, formats)
        
#         workbook.close()
#         output.seek(0)
        
#         # Create attachment
#         attachment = self.env['ir.attachment'].create({
#             'name': f'PnL_BudgetVsActual_{self.date_from.year}.xlsx',
#             'type': 'binary',
#             'datas': base64.b64encode(output.read()),
#             'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#         })
        
#         # Return download action
#         return {
#             'type': 'ir.actions.act_url',
#             'url': f'/web/content/{attachment.id}?download=true',
#             'target': 'self',
#         }
    
#     def _get_formats(self, workbook):
#         """Define all Excel formats"""
#         return {
#             'title': workbook.add_format({
#                 'bold': True,
#                 'font_size': 14,
#                 'align': 'center',
#                 'valign': 'vcenter',
#                 'bg_color': '#1F4E79',
#                 'font_color': 'white',
#                 'border': 1
#             }),
#             'subtitle': workbook.add_format({
#                 'font_size': 11,
#                 'align': 'center',
#                 'valign': 'vcenter',
#                 'border': 1
#             }),
#             'header': workbook.add_format({
#                 'bold': True,
#                 'font_size': 11,
#                 'align': 'center',
#                 'bg_color': '#1F4E79',
#                 'font_color': 'white',
#                 'border': 1,
#                 'text_wrap': True
#             }),
#             'category_main': workbook.add_format({
#                 'bold': True,
#                 'font_size': 11,
#                 'bg_color': '#D9E2F3',
#                 'border': 1
#             }),
#             'category_sub': workbook.add_format({
#                 'font_size': 10,
#                 'indent': 1,
#                 'border': 1
#             }),
#             'item': workbook.add_format({
#                 'font_size': 10,
#                 'indent': 2,
#                 'border': 1
#             }),
#             'number': workbook.add_format({
#                 'num_format': '#,##0.00;[Red](#,##0.00)',
#                 'font_size': 10,
#                 'border': 1,
#                 'align': 'right'
#             }),
#             'number_bold': workbook.add_format({
#                 'num_format': '#,##0.00;[Red](#,##0.00)',
#                 'bold': True,
#                 'border': 1,
#                 'align': 'right'
#             }),
#             'percent': workbook.add_format({
#                 'num_format': '0.00%;[Red](0.00%)',
#                 'font_size': 10,
#                 'border': 1,
#                 'align': 'center'
#             }),
#             'percent_bold': workbook.add_format({
#                 'num_format': '0.00%;[Red](0.00%)',
#                 'bold': True,
#                 'border': 1,
#                 'align': 'center'
#             }),
#             'total': workbook.add_format({
#                 'bold': True,
#                 'font_size': 11,
#                 'bg_color': '#FFE699',
#                 'border': 1
#             }),
#             'total_number': workbook.add_format({
#                 'num_format': '#,##0.00;[Red](#,##0.00)',
#                 'bold': True,
#                 'bg_color': '#FFE699',
#                 'border': 1,
#                 'align': 'right'
#             }),
#             'total_percent': workbook.add_format({
#                 'num_format': '0.00%;[Red](0.00%)',
#                 'bold': True,
#                 'bg_color': '#FFE699',
#                 'border': 1,
#                 'align': 'center'
#             }),
#             'net_profit': workbook.add_format({
#                 'bold': True,
#                 'font_size': 12,
#                 'bg_color': '#70AD47',
#                 'font_color': 'white',
#                 'border': 2
#             }),
#             'net_profit_number': workbook.add_format({
#                 'num_format': '#,##0.00;[Red](#,##0.00)',
#                 'bold': True,
#                 'font_size': 12,
#                 'bg_color': '#70AD47',
#                 'font_color': 'white',
#                 'border': 2,
#                 'align': 'right'
#             }),
#             'net_profit_percent': workbook.add_format({
#                 'num_format': '0.00%;[Red](0.00%)',
#                 'bold': True,
#                 'font_size': 12,
#                 'bg_color': '#70AD47',
#                 'font_color': 'white',
#                 'border': 2,
#                 'align': 'center'
#             }),
#         }
    
#     def _write_report(self, worksheet, formats):
#         """Write the complete report to worksheet"""
#         row = 0
        
#         # Title
#         worksheet.merge_range(row, 0, row, 4, 
#                             f'{self.company_id.name}', 
#                             formats['title'])
#         row += 1
        
#         worksheet.merge_range(row, 0, row, 4, 
#                             'PROFIT AND LOSS STATEMENT', 
#                             formats['title'])
#         row += 1
        
#         worksheet.merge_range(row, 0, row, 4,
#                             f'For the period from {self.date_from.strftime("%B %d, %Y")} to {self.date_to.strftime("%B %d, %Y")}',
#                             formats['subtitle'])
#         row += 2
        
#         # Headers
#         worksheet.write(row, 0, 'Description', formats['header'])
#         worksheet.write(row, 1, 'Planning', formats['header'])
#         worksheet.write(row, 2, 'Actual', formats['header'])
#         worksheet.write(row, 3, 'Variance', formats['header'])
#         worksheet.write(row, 4, '%', formats['header'])
#         row += 1
        
#         # Get data
#         pnl_data = self._get_pnl_data()
        
#         # REVENUE Section
#         worksheet.write(row, 0, 'REVENUE', formats['category_main'])
#         worksheet.write(row, 1, pnl_data['revenue']['total_planned'], formats['number_bold'])
#         worksheet.write(row, 2, pnl_data['revenue']['total_actual'], formats['number_bold'])
#         variance = pnl_data['revenue']['total_actual'] - pnl_data['revenue']['total_planned']
#         worksheet.write(row, 3, variance, formats['number_bold'])
#         if pnl_data['revenue']['total_planned'] != 0:
#             percent = (pnl_data['revenue']['total_actual'] / pnl_data['revenue']['total_planned']) - 1
#         else:
#             percent = 0
#         worksheet.write(row, 4, percent, formats['percent_bold'])
#         row += 1
        
#         # Other category (if exists)
#         if pnl_data['revenue']['other']:
#             worksheet.write(row, 0, 'Other', formats['category_sub'])
#             worksheet.write(row, 1, 0.00, formats['number'])
#             worksheet.write(row, 2, 0.00, formats['number'])
#             worksheet.write(row, 3, 0.00, formats['number'])
#             worksheet.write(row, 4, 0.00, formats['percent'])
#             row += 1
        
#         # Revenue items
#         for item in pnl_data['revenue']['items']:
#             worksheet.write(row, 0, f"  {item['name']}", formats['item'])
#             worksheet.write(row, 1, item['planned'], formats['number'])
#             worksheet.write(row, 2, item['actual'], formats['number'])
#             worksheet.write(row, 3, item['variance'], formats['number'])
#             worksheet.write(row, 4, item['percent'], formats['percent'])
#             row += 1
        
#         # Total Revenue
#         worksheet.write(row, 0, 'Total Revenue', formats['total'])
#         worksheet.write(row, 1, pnl_data['revenue']['total_planned'], formats['total_number'])
#         worksheet.write(row, 2, pnl_data['revenue']['total_actual'], formats['total_number'])
#         worksheet.write(row, 3, variance, formats['total_number'])
#         worksheet.write(row, 4, percent, formats['total_percent'])
#         row += 2
        
#         # COST OF GOODS SOLD Section
#         if pnl_data['cogs']['total_planned'] > 0 or pnl_data['cogs']['total_actual'] > 0:
#             worksheet.write(row, 0, 'COST OF GOODS SOLD', formats['category_main'])
#             worksheet.write(row, 1, -pnl_data['cogs']['total_planned'], formats['number_bold'])
#             worksheet.write(row, 2, -pnl_data['cogs']['total_actual'], formats['number_bold'])
#             variance = pnl_data['cogs']['total_actual'] - pnl_data['cogs']['total_planned']
#             worksheet.write(row, 3, -variance, formats['number_bold'])
#             if pnl_data['cogs']['total_planned'] != 0:
#                 percent = (pnl_data['cogs']['total_actual'] / pnl_data['cogs']['total_planned']) - 1
#             else:
#                 percent = 0
#             worksheet.write(row, 4, percent, formats['percent_bold'])
#             row += 1
            
#             # COGS items
#             for item in pnl_data['cogs']['items']:
#                 worksheet.write(row, 0, f"  {item['name']}", formats['item'])
#                 worksheet.write(row, 1, -item['planned'], formats['number'])
#                 worksheet.write(row, 2, -item['actual'], formats['number'])
#                 worksheet.write(row, 3, -item['variance'], formats['number'])
#                 worksheet.write(row, 4, item['percent'], formats['percent'])
#                 row += 1
            
#             row += 1
        
#         # GROSS PROFIT
#         gross_profit_planned = pnl_data['revenue']['total_planned'] - pnl_data['cogs']['total_planned']
#         gross_profit_actual = pnl_data['revenue']['total_actual'] - pnl_data['cogs']['total_actual']
#         gross_variance = gross_profit_actual - gross_profit_planned
        
#         worksheet.write(row, 0, 'GROSS PROFIT', formats['total'])
#         worksheet.write(row, 1, gross_profit_planned, formats['total_number'])
#         worksheet.write(row, 2, gross_profit_actual, formats['total_number'])
#         worksheet.write(row, 3, gross_variance, formats['total_number'])
#         if gross_profit_planned != 0:
#             percent = (gross_profit_actual / gross_profit_planned) - 1
#         else:
#             percent = 0
#         worksheet.write(row, 4, percent, formats['total_percent'])
#         row += 2
        
#         # OPERATING EXPENSES Section
#         if pnl_data['expenses']['total_planned'] > 0 or pnl_data['expenses']['total_actual'] > 0:
#             worksheet.write(row, 0, 'OPERATING EXPENSES', formats['category_main'])
#             worksheet.write(row, 1, -pnl_data['expenses']['total_planned'], formats['number_bold'])
#             worksheet.write(row, 2, -pnl_data['expenses']['total_actual'], formats['number_bold'])
#             variance = pnl_data['expenses']['total_actual'] - pnl_data['expenses']['total_planned']
#             worksheet.write(row, 3, -variance, formats['number_bold'])
#             if pnl_data['expenses']['total_planned'] != 0:
#                 percent = (pnl_data['expenses']['total_actual'] / pnl_data['expenses']['total_planned']) - 1
#             else:
#                 percent = 0
#             worksheet.write(row, 4, percent, formats['percent_bold'])
#             row += 1
            
#             # Expense items
#             for item in pnl_data['expenses']['items']:
#                 worksheet.write(row, 0, f"  {item['name']}", formats['item'])
#                 worksheet.write(row, 1, -item['planned'], formats['number'])
#                 worksheet.write(row, 2, -item['actual'], formats['number'])
#                 worksheet.write(row, 3, -item['variance'], formats['number'])
#                 worksheet.write(row, 4, item['percent'], formats['percent'])
#                 row += 1
            
#             row += 1
        
#         # NET PROFIT
#         net_profit_planned = gross_profit_planned - pnl_data['expenses']['total_planned']
#         net_profit_actual = gross_profit_actual - pnl_data['expenses']['total_actual']
#         net_variance = net_profit_actual - net_profit_planned
        
#         worksheet.write(row, 0, 'NET PROFIT', formats['net_profit'])
#         worksheet.write(row, 1, net_profit_planned, formats['net_profit_number'])
#         worksheet.write(row, 2, net_profit_actual, formats['net_profit_number'])
#         worksheet.write(row, 3, net_variance, formats['net_profit_number'])
#         if net_profit_planned != 0:
#             percent = (net_profit_actual / net_profit_planned) - 1
#         else:
#             percent = 0
#         worksheet.write(row, 4, percent, formats['net_profit_percent'])
    
#     def _get_pnl_data(self):
#         """Get P&L data with budget (planned) and actual amounts"""
#         result = {
#             'revenue': {
#                 'items': [],
#                 'other': False,
#                 'total_planned': 0.0,
#                 'total_actual': 0.0
#             },
#             'cogs': {
#                 'items': [],
#                 'total_planned': 0.0,
#                 'total_actual': 0.0
#             },
#             'expenses': {
#                 'items': [],
#                 'total_planned': 0.0,
#                 'total_actual': 0.0
#             }
#         }
        
#         # Get budget lines
#         domain = [
#             ('date_from', '<=', self.date_to),
#             ('date_to', '>=', self.date_from),
#             ('company_id', '=', self.company_id.id)
#         ]
        
#         if self.budget_ids:
#             domain.append(('crossovered_budget_id', 'in', self.budget_ids.ids))
        
#         budget_lines = self.env['crossovered.budget.lines'].search(domain)
        
#         # Group by budgetary position
#         position_data = {}
        
#         for line in budget_lines:
#             position = line.general_budget_id
#             if not position:
#                 continue
            
#             if position.id not in position_data:
#                 position_data[position.id] = {
#                     'name': position.name,
#                     'position': position,
#                     'planned': 0.0,
#                     'actual': 0.0
#                 }
            
#             # Sum planned and actual amounts
#             position_data[position.id]['planned'] += abs(line.planned_amount)
#             position_data[position.id]['actual'] += abs(line.practical_amount)
        
#         # Categorize and add to result
#         for pos_id, data in position_data.items():
#             position = data['position']
            
#             # Calculate variance and percentage
#             variance = data['actual'] - data['planned']
#             if data['planned'] != 0:
#                 percent = (data['actual'] / data['planned']) - 1
#             else:
#                 percent = 0 if data['actual'] == 0 else 1
            
#             item = {
#                 'name': data['name'],
#                 'planned': data['planned'],
#                 'actual': data['actual'],
#                 'variance': variance,
#                 'percent': percent
#             }
            
#             # Categorize based on account codes or position category
#             category = self._categorize_position(position)
            
#             if category == 'income':
#                 result['revenue']['items'].append(item)
#                 result['revenue']['total_planned'] += data['planned']
#                 result['revenue']['total_actual'] += data['actual']
#             elif category == 'cogs':
#                 result['cogs']['items'].append(item)
#                 result['cogs']['total_planned'] += data['planned']
#                 result['cogs']['total_actual'] += data['actual']
#             elif category == 'expense':
#                 result['expenses']['items'].append(item)
#                 result['expenses']['total_planned'] += data['planned']
#                 result['expenses']['total_actual'] += data['actual']
        
#         return result
    
#     def _categorize_position(self, position):
#         """Categorize budgetary position"""
#         # Check custom category if exists
#         if hasattr(position, 'pnl_category') and position.pnl_category:
#             if position.pnl_category in ['operating_income', 'other_income']:
#                 return 'income'
#             elif position.pnl_category == 'cost_of_revenue':
#                 return 'cogs'
#             else:
#                 return 'expense'
        
#         # Categorize based on account code
#         if position.account_ids:
#             first_code = position.account_ids[0].code or ''
            
#             # Indonesian COA standard
#             if first_code.startswith('4'):  # Revenue
#                 return 'income'
#             elif first_code.startswith('5'):  # COGS
#                 return 'cogs'
#             elif first_code.startswith(('6', '7', '8')):  # Expenses
#                 return 'expense'
        
#         # Default
#         return 'expense'


# class AccountBudgetPost(models.Model):
#     """Extend Budgetary Position for P&L categorization"""
#     _inherit = 'account.budget.post'
    
#     pnl_category = fields.Selection([
#         ('operating_income', 'Operating Income'),
#         ('other_income', 'Other Income'), 
#         ('cost_of_revenue', 'Cost of Revenue'),
#         ('operating_expense', 'Operating Expense'),
#         ('depreciation', 'Depreciation'),
#         ('other_expense', 'Other Expense'),
#     ], string='P&L Category', 
#        help='Category for Profit & Loss Report classification')
    
#     is_income = fields.Boolean(
#         string='Is Income Account',
#         compute='_compute_is_income',
#         store=True,
#         help='Indicates if this position represents income'
#     )
    
#     @api.depends('pnl_category')
#     def _compute_is_income(self):
#         """Compute whether this is an income category"""
#         income_categories = ['operating_income', 'other_income']
#         for rec in self:
#             rec.is_income = rec.pnl_category in income_categories

# -*- coding: utf-8 -*-
# wizard/account_budget_pnl_report.py

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
from io import BytesIO
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import logging

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.warning('xlsxwriter library is not installed. P&L Excel export will not work.')
    xlsxwriter = None

class AccountBudgetPnlReport(models.TransientModel):
    """P&L Report with Budget vs Actual Comparison"""
    _name = 'account.budget.pnl.report'
    _description = 'Profit & Loss Budget vs Actual Report'
    
    # Basic fields
    date_from = fields.Date(
        string='Start Date',
        required=True,
        default=lambda self: date(date.today().year, 1, 1)
    )
    date_to = fields.Date(
        string='End Date', 
        required=True,
        default=fields.Date.today
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    budget_ids = fields.Many2many(
        'crossovered.budget',
        string='Budgets',
        help='Select specific budgets. Leave empty for all budgets in period.'
    )
    
    def action_generate_excel(self):
        """Generate Excel P&L Report with Budget vs Actual"""
        self.ensure_one()
        
        if not xlsxwriter:
            raise UserError(_('Please install xlsxwriter library: pip install xlsxwriter'))
        
        # Create Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Profit and Loss')
        
        # Define formats
        formats = self._get_formats(workbook)
        
        # Write report
        self._write_monthly_report(worksheet, formats)
        
        workbook.close()
        output.seek(0)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'PnL_Monthly_BudgetVsActual_{self.date_from.year}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
    
    def _get_formats(self, workbook):
        """Define all Excel formats"""
        return {
            'title': workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#1F4E79',
                'font_color': 'white',
                'border': 1
            }),
            'subtitle': workbook.add_format({
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            }),
            'header': workbook.add_format({
                'bold': True,
                'font_size': 10,
                'align': 'center',
                'bg_color': '#1F4E79',
                'font_color': 'white',
                'border': 1,
                'text_wrap': True,
                'valign': 'vcenter'
            }),
            'subheader': workbook.add_format({
                'bold': True,
                'font_size': 9,
                'align': 'center',
                'bg_color': '#5B9BD5',
                'font_color': 'white',
                'border': 1,
                'text_wrap': True,
                'valign': 'vcenter'
            }),
            'category_main': workbook.add_format({
                'bold': True,
                'font_size': 11,
                'bg_color': '#D9E2F3',
                'border': 1
            }),
            'category_sub': workbook.add_format({
                'font_size': 10,
                'indent': 1,
                'border': 1
            }),
            'item': workbook.add_format({
                'font_size': 9,
                'indent': 2,
                'border': 1
            }),
            'number': workbook.add_format({
                'num_format': '#,##0;[Red](#,##0)',
                'font_size': 9,
                'border': 1,
                'align': 'right'
            }),
            'number_bold': workbook.add_format({
                'num_format': '#,##0;[Red](#,##0)',
                'bold': True,
                'border': 1,
                'align': 'right'
            }),
            'percent': workbook.add_format({
                'num_format': '0.0%;[Red](0.0%)',
                'font_size': 9,
                'border': 1,
                'align': 'center'
            }),
            'percent_bold': workbook.add_format({
                'num_format': '0.0%;[Red](0.0%)',
                'bold': True,
                'border': 1,
                'align': 'center'
            }),
            'total': workbook.add_format({
                'bold': True,
                'font_size': 10,
                'bg_color': '#FFE699',
                'border': 1
            }),
            'total_number': workbook.add_format({
                'num_format': '#,##0;[Red](#,##0)',
                'bold': True,
                'font_size': 9,
                'bg_color': '#FFE699',
                'border': 1,
                'align': 'right'
            }),
            'total_percent': workbook.add_format({
                'num_format': '0.0%;[Red](0.0%)',
                'bold': True,
                'bg_color': '#FFE699',
                'border': 1,
                'align': 'center'
            }),
            'net_profit': workbook.add_format({
                'bold': True,
                'font_size': 11,
                'bg_color': '#70AD47',
                'font_color': 'white',
                'border': 2
            }),
            'net_profit_number': workbook.add_format({
                'num_format': '#,##0;[Red](#,##0)',
                'bold': True,
                'font_size': 10,
                'bg_color': '#70AD47',
                'font_color': 'white',
                'border': 2,
                'align': 'right'
            }),
            'gray_bg': workbook.add_format({
                'bg_color': '#F2F2F2',
                'border': 1
            }),
        }
    
    def _get_months_list(self):
        """Get list of months between date_from and date_to"""
        months = []
        current_date = self.date_from.replace(day=1)
        end_date = self.date_to.replace(day=1)
        
        while current_date <= end_date:
            months.append({
                'date': current_date,
                'name': current_date.strftime('%b %Y'),
                'start': current_date,
                'end': current_date + relativedelta(months=1, days=-1)
            })
            current_date += relativedelta(months=1)
        
        return months
    
    def _write_monthly_report(self, worksheet, formats):
        """Write the monthly report to worksheet"""
        months = self._get_months_list()
        num_months = len(months)
        
        # Calculate column positions
        desc_col = 0
        first_month_col = 1
        total_col = first_month_col + (num_months * 3)  # 3 columns per month
        
        # Set column widths
        worksheet.set_column(desc_col, desc_col, 40)  # Description
        for i in range(num_months):
            col = first_month_col + (i * 3)
            worksheet.set_column(col, col + 2, 12)  # Planning, Actual, Variance
        worksheet.set_column(total_col, total_col + 2, 14)  # Total columns
        
        row = 0
        
        # Title
        last_col = total_col + 2
        worksheet.merge_range(row, 0, row, last_col, 
                            f'{self.company_id.name}', 
                            formats['title'])
        row += 1
        
        worksheet.merge_range(row, 0, row, last_col, 
                            'PROFIT AND LOSS STATEMENT - MONTHLY', 
                            formats['title'])
        row += 1
        
        worksheet.merge_range(row, 0, row, last_col,
                            f'For the period from {self.date_from.strftime("%B %d, %Y")} to {self.date_to.strftime("%B %d, %Y")}',
                            formats['subtitle'])
        row += 2
        
        # Headers
        # First row - Month names
        worksheet.merge_range(row, desc_col, row + 1, desc_col, 'Description', formats['header'])
        
        for i, month in enumerate(months):
            col = first_month_col + (i * 3)
            worksheet.merge_range(row, col, row, col + 2, month['name'], formats['header'])
        
        worksheet.merge_range(row, total_col, row, total_col + 2, 'TOTAL', formats['header'])
        row += 1
        
        # Second row - P/A/V headers
        for i in range(num_months + 1):  # +1 for total
            col = first_month_col + (i * 3)
            worksheet.write(row, col, 'Plan', formats['subheader'])
            worksheet.write(row, col + 1, 'Actual', formats['subheader'])
            worksheet.write(row, col + 2, 'Var %', formats['subheader'])
        row += 1
        
        # Get monthly data
        monthly_data = self._get_monthly_pnl_data(months)
        
        # REVENUE Section
        self._write_section(worksheet, formats, row, 'REVENUE', 
                          monthly_data['revenue'], months, 
                          first_month_col, total_col, True)
        row += len(monthly_data['revenue']['items']) + 3
        
        # COST OF GOODS SOLD Section
        if any(monthly_data['cogs']['totals'][m['date'].strftime('%Y-%m')]['planned'] > 0 or 
               monthly_data['cogs']['totals'][m['date'].strftime('%Y-%m')]['actual'] > 0 
               for m in months):
            self._write_section(worksheet, formats, row, 'COST OF GOODS SOLD', 
                              monthly_data['cogs'], months, 
                              first_month_col, total_col, False)
            row += len(monthly_data['cogs']['items']) + 2
        
        # GROSS PROFIT
        row = self._write_gross_profit(worksheet, formats, row, monthly_data, 
                                     months, first_month_col, total_col)
        row += 2
        
        # OPERATING EXPENSES Section
        if any(monthly_data['expenses']['totals'][m['date'].strftime('%Y-%m')]['planned'] > 0 or 
               monthly_data['expenses']['totals'][m['date'].strftime('%Y-%m')]['actual'] > 0 
               for m in months):
            self._write_section(worksheet, formats, row, 'OPERATING EXPENSES', 
                              monthly_data['expenses'], months, 
                              first_month_col, total_col, False)
            row += len(monthly_data['expenses']['items']) + 2
        
        # NET PROFIT
        self._write_net_profit(worksheet, formats, row, monthly_data, 
                             months, first_month_col, total_col)
    
    def _write_section(self, worksheet, formats, row, title, section_data, 
                      months, first_month_col, total_col, is_revenue):
        """Write a section (Revenue, COGS, or Expenses)"""
        # Section header
        worksheet.write(row, 0, title, formats['category_main'])
        
        # Monthly totals for section
        total_planned = 0
        total_actual = 0
        
        for i, month in enumerate(months):
            col = first_month_col + (i * 3)
            month_key = month['date'].strftime('%Y-%m')
            
            planned = section_data['totals'][month_key]['planned']
            actual = section_data['totals'][month_key]['actual']
            
            if not is_revenue:
                planned = -planned
                actual = -actual
            
            worksheet.write(row, col, planned, formats['number_bold'])
            worksheet.write(row, col + 1, actual, formats['number_bold'])
            
            if planned != 0:
                variance = ((actual - planned) / abs(planned)) * 100
            else:
                variance = 0
            worksheet.write(row, col + 2, variance / 100, formats['percent_bold'])
            
            total_planned += planned if is_revenue else -planned
            total_actual += actual if is_revenue else -actual
        
        # Total column
        worksheet.write(row, total_col, total_planned if is_revenue else -total_planned, 
                       formats['number_bold'])
        worksheet.write(row, total_col + 1, total_actual if is_revenue else -total_actual, 
                       formats['number_bold'])
        if total_planned != 0:
            total_variance = ((total_actual - total_planned) / abs(total_planned)) * 100
        else:
            total_variance = 0
        worksheet.write(row, total_col + 2, total_variance / 100, formats['percent_bold'])
        row += 1
        
        # Items
        for item in section_data['items']:
            worksheet.write(row, 0, f"  {item['name']}", formats['item'])
            
            item_total_planned = 0
            item_total_actual = 0
            
            for i, month in enumerate(months):
                col = first_month_col + (i * 3)
                month_key = month['date'].strftime('%Y-%m')
                
                planned = item['monthly'][month_key]['planned']
                actual = item['monthly'][month_key]['actual']
                
                if not is_revenue:
                    planned = -planned
                    actual = -actual
                
                worksheet.write(row, col, planned, formats['number'])
                worksheet.write(row, col + 1, actual, formats['number'])
                
                if planned != 0:
                    variance = ((actual - planned) / abs(planned)) * 100
                else:
                    variance = 0
                worksheet.write(row, col + 2, variance / 100, formats['percent'])
                
                item_total_planned += planned if is_revenue else -planned
                item_total_actual += actual if is_revenue else -actual
            
            # Item total
            worksheet.write(row, total_col, item_total_planned if is_revenue else -item_total_planned, 
                           formats['number'])
            worksheet.write(row, total_col + 1, item_total_actual if is_revenue else -item_total_actual, 
                           formats['number'])
            if item_total_planned != 0:
                item_variance = ((item_total_actual - item_total_planned) / abs(item_total_planned)) * 100
            else:
                item_variance = 0
            worksheet.write(row, total_col + 2, item_variance / 100, formats['percent'])
            row += 1
        
        return row
    
    def _write_gross_profit(self, worksheet, formats, row, monthly_data, 
                          months, first_month_col, total_col):
        """Write gross profit row"""
        worksheet.write(row, 0, 'GROSS PROFIT', formats['total'])
        
        total_planned = 0
        total_actual = 0
        
        for i, month in enumerate(months):
            col = first_month_col + (i * 3)
            month_key = month['date'].strftime('%Y-%m')
            
            gross_planned = (monthly_data['revenue']['totals'][month_key]['planned'] - 
                           monthly_data['cogs']['totals'][month_key]['planned'])
            gross_actual = (monthly_data['revenue']['totals'][month_key]['actual'] - 
                          monthly_data['cogs']['totals'][month_key]['actual'])
            
            worksheet.write(row, col, gross_planned, formats['total_number'])
            worksheet.write(row, col + 1, gross_actual, formats['total_number'])
            
            if gross_planned != 0:
                variance = ((gross_actual - gross_planned) / abs(gross_planned)) * 100
            else:
                variance = 0
            worksheet.write(row, col + 2, variance / 100, formats['total_percent'])
            
            total_planned += gross_planned
            total_actual += gross_actual
        
        # Total
        worksheet.write(row, total_col, total_planned, formats['total_number'])
        worksheet.write(row, total_col + 1, total_actual, formats['total_number'])
        if total_planned != 0:
            total_variance = ((total_actual - total_planned) / abs(total_planned)) * 100
        else:
            total_variance = 0
        worksheet.write(row, total_col + 2, total_variance / 100, formats['total_percent'])
        
        return row
    
    def _write_net_profit(self, worksheet, formats, row, monthly_data, 
                        months, first_month_col, total_col):
        """Write net profit row"""
        worksheet.write(row, 0, 'NET PROFIT', formats['net_profit'])
        
        total_planned = 0
        total_actual = 0
        
        for i, month in enumerate(months):
            col = first_month_col + (i * 3)
            month_key = month['date'].strftime('%Y-%m')
            
            net_planned = (monthly_data['revenue']['totals'][month_key]['planned'] - 
                         monthly_data['cogs']['totals'][month_key]['planned'] -
                         monthly_data['expenses']['totals'][month_key]['planned'])
            net_actual = (monthly_data['revenue']['totals'][month_key]['actual'] - 
                        monthly_data['cogs']['totals'][month_key]['actual'] -
                        monthly_data['expenses']['totals'][month_key]['actual'])
            
            worksheet.write(row, col, net_planned, formats['net_profit_number'])
            worksheet.write(row, col + 1, net_actual, formats['net_profit_number'])
            
            if net_planned != 0:
                variance = ((net_actual - net_planned) / abs(net_planned)) * 100
            else:
                variance = 0
            worksheet.write(row, col + 2, variance / 100, formats['percent_bold'])
            
            total_planned += net_planned
            total_actual += net_actual
        
        # Total
        worksheet.write(row, total_col, total_planned, formats['net_profit_number'])
        worksheet.write(row, total_col + 1, total_actual, formats['net_profit_number'])
        if total_planned != 0:
            total_variance = ((total_actual - total_planned) / abs(total_planned)) * 100
        else:
            total_variance = 0
        worksheet.write(row, total_col + 2, total_variance / 100, formats['percent_bold'])
    

    def _get_monthly_pnl_data(self, months):
        """Get P&L data broken down by month with analytic distribution consideration"""
        result = {
            'revenue': {'items': [], 'totals': {}},
            'cogs': {'items': [], 'totals': {}},
            'expenses': {'items': [], 'totals': {}}
        }
        
        # Initialize month totals
        for month in months:
            month_key = month['date'].strftime('%Y-%m')
            for category in ['revenue', 'cogs', 'expenses']:
                result[category]['totals'][month_key] = {
                    'planned': 0.0,
                    'actual': 0.0
                }
        
        # Get budget lines directly
        domain = [
            ('date_from', '<=', self.date_to),
            ('date_to', '>=', self.date_from),
            ('company_id', '=', self.company_id.id),
        ]
        
        if self.budget_ids:
            domain.append(('crossovered_budget_id', 'in', self.budget_ids.ids))
        
        budget_lines = self.env['crossovered.budget.lines'].search(domain)
        
        # Group by budgetary position AND analytic account
        position_analytic_data = {}
        
        for line in budget_lines:
            position = line.general_budget_id
            analytic = line.analytic_account_id
            
            if not position:
                continue
            
            # Create unique key combining position and analytic account
            key = f"{position.id}_{analytic.id if analytic else 'no_analytic'}"
            
            if key not in position_analytic_data:
                position_analytic_data[key] = {
                    'name': position.name,
                    'position': position,
                    'analytic_account_id': analytic.id if analytic else False,
                    'analytic_account_name': analytic.name if analytic else '',
                    'monthly': {}
                }
                
                # Initialize monthly data
                for month in months:
                    month_key = month['date'].strftime('%Y-%m')
                    position_analytic_data[key]['monthly'][month_key] = {
                        'planned': 0.0,
                        'actual': 0.0
                    }
            
            # Calculate monthly PLANNED amounts
            for month in months:
                month_key = month['date'].strftime('%Y-%m')
                
                # Check overlap
                line_start = max(line.date_from, month['start'])
                line_end = min(line.date_to, month['end'])
                
                if line_start <= line_end:
                    total_days = (line.date_to - line.date_from).days + 1
                    month_days = (line_end - line_start).days + 1
                    
                    if total_days > 0:
                        ratio = month_days / total_days
                        position_analytic_data[key]['monthly'][month_key]['planned'] += abs(line.planned_amount * ratio)
        
        # Get ACTUAL amounts for each position-analytic combination
        for key, data in position_analytic_data.items():
            position = data['position']
            analytic_id = data['analytic_account_id']
            account_ids = position.account_ids.ids
            
            if account_ids:
                # Get actual amounts using SQL for better performance
                monthly_actuals = self._get_actual_with_analytic(account_ids, analytic_id, months)
                
                for month_key, actual_amount in monthly_actuals.items():
                    position_analytic_data[key]['monthly'][month_key]['actual'] = actual_amount
        
        # Now group by position name for display
        position_grouped = {}
        
        for key, data in position_analytic_data.items():
            pos_name = data['name']
            
            # If analytic account exists, append it to the name
            if data['analytic_account_name']:
                display_name = f"{pos_name} - {data['analytic_account_name']}"
            else:
                display_name = pos_name
            
            if display_name not in position_grouped:
                position_grouped[display_name] = {
                    'name': display_name,
                    'position': data['position'],
                    'monthly': {}
                }
                
                # Initialize
                for month in months:
                    month_key = month['date'].strftime('%Y-%m')
                    position_grouped[display_name]['monthly'][month_key] = {
                        'planned': 0.0,
                        'actual': 0.0
                    }
            
            # Add amounts
            for month_key, amounts in data['monthly'].items():
                position_grouped[display_name]['monthly'][month_key]['planned'] += amounts['planned']
                position_grouped[display_name]['monthly'][month_key]['actual'] += amounts['actual']
        
        # Categorize and add to result
        for display_name, data in position_grouped.items():
            position = data['position']
            category = self._categorize_position(position)
            
            # Only add if there's data
            has_data = any(
                month_data['planned'] > 0 or month_data['actual'] > 0 
                for month_data in data['monthly'].values()
            )
            
            if has_data:
                item = {
                    'name': display_name,
                    'monthly': data['monthly']
                }
                
                if category == 'income':
                    result['revenue']['items'].append(item)
                    for month_key, month_data in data['monthly'].items():
                        result['revenue']['totals'][month_key]['planned'] += month_data['planned']
                        result['revenue']['totals'][month_key]['actual'] += month_data['actual']
                elif category == 'cogs':
                    result['cogs']['items'].append(item)
                    for month_key, month_data in data['monthly'].items():
                        result['cogs']['totals'][month_key]['planned'] += month_data['planned']
                        result['cogs']['totals'][month_key]['actual'] += month_data['actual']
                elif category == 'expense':
                    result['expenses']['items'].append(item)
                    for month_key, month_data in data['monthly'].items():
                        result['expenses']['totals'][month_key]['planned'] += month_data['planned']
                        result['expenses']['totals'][month_key]['actual'] += month_data['actual']
        
        # Sort items
        for category in ['revenue', 'cogs', 'expenses']:
            result[category]['items'].sort(key=lambda x: x['name'])
        
        return result

    def _get_actual_with_analytic(self, account_ids, analytic_id, months):
        """Get actual amounts with analytic distribution filter using SQL"""
        monthly_actuals = {}
        
        # Initialize
        for month in months:
            month_key = month['date'].strftime('%Y-%m')
            monthly_actuals[month_key] = 0.0
        
        if not account_ids:
            return monthly_actuals
        
        if analytic_id:
            # Query with analytic distribution filter
            # analytic_distribution is stored as JSON like {"1": 100.0} where 1 is analytic account id
            query = """
                SELECT 
                    TO_CHAR(aml.date, 'YYYY-MM') as month_key,
                    SUM(aml.balance) as balance
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                WHERE 
                    aml.account_id = ANY(%s)
                    AND aml.date >= %s
                    AND aml.date <= %s
                    AND aml.company_id = %s
                    AND am.state = 'posted'
                    AND aml.analytic_distribution ? %s
                GROUP BY TO_CHAR(aml.date, 'YYYY-MM')
            """
            
            params = (
                account_ids,
                self.date_from,
                self.date_to,
                self.company_id.id,
                str(analytic_id)  # Key in JSON
            )
        else:
            # Query for lines WITHOUT analytic distribution
            query = """
                SELECT 
                    TO_CHAR(aml.date, 'YYYY-MM') as month_key,
                    SUM(aml.balance) as balance
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                WHERE 
                    aml.account_id = ANY(%s)
                    AND aml.date >= %s
                    AND aml.date <= %s
                    AND aml.company_id = %s
                    AND am.state = 'posted'
                    AND (aml.analytic_distribution IS NULL OR aml.analytic_distribution = '{}')
                GROUP BY TO_CHAR(aml.date, 'YYYY-MM')
            """
            
            params = (
                account_ids,
                self.date_from,
                self.date_to,
                self.company_id.id
            )
        
        self.env.cr.execute(query, params)
        
        for row in self.env.cr.dictfetchall():
            if row['month_key'] in monthly_actuals:
                monthly_actuals[row['month_key']] = abs(row['balance'] or 0.0)
        
        return monthly_actuals


    # def _get_monthly_pnl_data(self, months):
    #     """Get P&L data broken down by month"""
    #     result = {
    #         'revenue': {
    #             'items': [],
    #             'totals': {}
    #         },
    #         'cogs': {
    #             'items': [],
    #             'totals': {}
    #         },
    #         'expenses': {
    #             'items': [],
    #             'totals': {}
    #         }
    #     }
        
    #     # Initialize month totals
    #     for month in months:
    #         month_key = month['date'].strftime('%Y-%m')
    #         for category in ['revenue', 'cogs', 'expenses']:
    #             result[category]['totals'][month_key] = {
    #                 'planned': 0.0,
    #                 'actual': 0.0
    #             }
        
    #     # Get budget lines
    #     domain = [
    #         ('date_from', '<=', self.date_to),
    #         ('date_to', '>=', self.date_from),
    #         ('company_id', '=', self.company_id.id)
    #     ]
        
    #     if self.budget_ids:
    #         domain.append(('crossovered_budget_id', 'in', self.budget_ids.ids))
        
    #     budget_lines = self.env['crossovered.budget.lines'].search(domain)
        
    #     # Group by budgetary position
    #     position_data = {}
        
    #     for line in budget_lines:
    #         position = line.general_budget_id
    #         if not position:
    #             continue
            
    #         if position.id not in position_data:
    #             position_data[position.id] = {
    #                 'name': position.name,
    #                 'position': position,
    #                 'monthly': {}
    #             }
    #             # Initialize monthly data
    #             for month in months:
    #                 month_key = month['date'].strftime('%Y-%m')
    #                 position_data[position.id]['monthly'][month_key] = {
    #                     'planned': 0.0,
    #                     'actual': 0.0
    #                 }
            
    #         # Calculate monthly amounts
    #         for month in months:
    #             month_key = month['date'].strftime('%Y-%m')
                
    #             # Check if budget line overlaps with this month
    #             line_start = max(line.date_from, month['start'])
    #             line_end = min(line.date_to, month['end'])
                
    #             if line_start <= line_end:
    #                 # Calculate the portion for this month
    #                 total_days = (line.date_to - line.date_from).days + 1
    #                 month_days = (line_end - line_start).days + 1
                    
    #                 if total_days > 0:
    #                     ratio = month_days / total_days
                        
    #                     position_data[position.id]['monthly'][month_key]['planned'] += abs(line.planned_amount * ratio)
    #                     position_data[position.id]['monthly'][month_key]['actual'] += abs(line.practical_amount * ratio)
        
    #     # Categorize and add to result
    #     for pos_id, data in position_data.items():
    #         position = data['position']
    #         category = self._categorize_position(position)
            
    #         item = {
    #             'name': data['name'],
    #             'monthly': data['monthly']
    #         }
            
    #         if category == 'income':
    #             result['revenue']['items'].append(item)
    #             for month_key, month_data in data['monthly'].items():
    #                 result['revenue']['totals'][month_key]['planned'] += month_data['planned']
    #                 result['revenue']['totals'][month_key]['actual'] += month_data['actual']
    #         elif category == 'cogs':
    #             result['cogs']['items'].append(item)
    #             for month_key, month_data in data['monthly'].items():
    #                 result['cogs']['totals'][month_key]['planned'] += month_data['planned']
    #                 result['cogs']['totals'][month_key]['actual'] += month_data['actual']
    #         elif category == 'expense':
    #             result['expenses']['items'].append(item)
    #             for month_key, month_data in data['monthly'].items():
    #                 result['expenses']['totals'][month_key]['planned'] += month_data['planned']
    #                 result['expenses']['totals'][month_key]['actual'] += month_data['actual']
        
    #     return result

    # def _get_monthly_pnl_data(self, months):
    #     """Get P&L data broken down by month"""
    #     result = {
    #         'revenue': {
    #             'items': [],
    #             'totals': {}
    #         },
    #         'cogs': {
    #             'items': [],
    #             'totals': {}
    #         },
    #         'expenses': {
    #             'items': [],
    #             'totals': {}
    #         }
    #     }
        
    #     # Initialize month totals
    #     for month in months:
    #         month_key = month['date'].strftime('%Y-%m')
    #         for category in ['revenue', 'cogs', 'expenses']:
    #             result[category]['totals'][month_key] = {
    #                 'planned': 0.0,
    #                 'actual': 0.0
    #             }
        
    #     # Get budget lines
    #     domain = [
    #         ('date_from', '<=', self.date_to),
    #         ('date_to', '>=', self.date_from),
    #         ('company_id', '=', self.company_id.id)
    #     ]
        
    #     if self.budget_ids:
    #         domain.append(('crossovered_budget_id', 'in', self.budget_ids.ids))
        
    #     budget_lines = self.env['crossovered.budget.lines'].search(domain)
        
    #     # Group by budgetary position
    #     position_data = {}
        
    #     for line in budget_lines:
    #         position = line.general_budget_id
    #         if not position:
    #             continue
            
    #         if position.id not in position_data:
    #             position_data[position.id] = {
    #                 'name': position.name,
    #                 'position': position,
    #                 'monthly': {}
    #             }
    #             # Initialize monthly data
    #             for month in months:
    #                 month_key = month['date'].strftime('%Y-%m')
    #                 position_data[position.id]['monthly'][month_key] = {
    #                     'planned': 0.0,
    #                     'actual': 0.0
    #                 }
            
    #         # Calculate monthly PLANNED amounts
    #         for month in months:
    #             month_key = month['date'].strftime('%Y-%m')
                
    #             # Check if budget line overlaps with this month
    #             line_start = max(line.date_from, month['start'])
    #             line_end = min(line.date_to, month['end'])
                
    #             if line_start <= line_end:
    #                 # Calculate the portion for this month
    #                 total_days = (line.date_to - line.date_from).days + 1
    #                 month_days = (line_end - line_start).days + 1
                    
    #                 if total_days > 0:
    #                     ratio = month_days / total_days
    #                     position_data[position.id]['monthly'][month_key]['planned'] += abs(line.planned_amount * ratio)
        
    #     # Get ACTUAL amounts from journal entries
    #     for pos_id, data in position_data.items():
    #         position = data['position']
            
    #         # Get accounts linked to this budgetary position
    #         account_ids = position.account_ids.ids
            
    #         if account_ids:
    #             # Get actual amounts from account.move.line
    #             for month in months:
    #                 month_key = month['date'].strftime('%Y-%m')
                    
    #                 # Query journal entries for this month
    #                 aml_domain = [
    #                     ('account_id', 'in', account_ids),
    #                     ('date', '>=', month['start']),
    #                     ('date', '<=', month['end']),
    #                     ('company_id', '=', self.company_id.id),
    #                     ('parent_state', '=', 'posted'),  # Only posted entries
    #                 ]
                    
    #                 # Get account move lines
    #                 move_lines = self.env['account.move.line'].search(aml_domain)
                    
    #                 # Calculate balance
    #                 balance = sum(move_lines.mapped('balance'))
                    
    #                 # Store actual amount (use absolute value)
    #                 position_data[pos_id]['monthly'][month_key]['actual'] = abs(balance)
        
    #     # Categorize and add to result
    #     for pos_id, data in position_data.items():
    #         position = data['position']
    #         category = self._categorize_position(position)
            
    #         item = {
    #             'name': data['name'],
    #             'monthly': data['monthly']
    #         }
            
    #         if category == 'income':
    #             result['revenue']['items'].append(item)
    #             for month_key, month_data in data['monthly'].items():
    #                 result['revenue']['totals'][month_key]['planned'] += month_data['planned']
    #                 result['revenue']['totals'][month_key]['actual'] += month_data['actual']
    #         elif category == 'cogs':
    #             result['cogs']['items'].append(item)
    #             for month_key, month_data in data['monthly'].items():
    #                 result['cogs']['totals'][month_key]['planned'] += month_data['planned']
    #                 result['cogs']['totals'][month_key]['actual'] += month_data['actual']
    #         elif category == 'expense':
    #             result['expenses']['items'].append(item)
    #             for month_key, month_data in data['monthly'].items():
    #                 result['expenses']['totals'][month_key]['planned'] += month_data['planned']
    #                 result['expenses']['totals'][month_key]['actual'] += month_data['actual']
        
    #     return result

    # def _get_monthly_pnl_data(self, months):
    #     """Get P&L data broken down by month with analytic account consideration"""
    #     result = {
    #         'revenue': {'items': [], 'totals': {}},
    #         'cogs': {'items': [], 'totals': {}},
    #         'expenses': {'items': [], 'totals': {}}
    #     }
        
    #     # Initialize month totals
    #     for month in months:
    #         month_key = month['date'].strftime('%Y-%m')
    #         for category in ['revenue', 'cogs', 'expenses']:
    #             result[category]['totals'][month_key] = {
    #                 'planned': 0.0,
    #                 'actual': 0.0
    #             }
        
    #     # Get budget lines directly
    #     domain = [
    #         ('date_from', '<=', self.date_to),
    #         ('date_to', '>=', self.date_from),
    #         ('company_id', '=', self.company_id.id),
    #     ]
        
    #     if self.budget_ids:
    #         domain.append(('crossovered_budget_id', 'in', self.budget_ids.ids))
        
    #     budget_lines = self.env['crossovered.budget.lines'].search(domain)
        
    #     # Group by budgetary position AND analytic account
    #     position_analytic_data = {}
        
    #     for line in budget_lines:
    #         position = line.general_budget_id
    #         analytic = line.analytic_account_id
            
    #         if not position:
    #             continue
            
    #         # Create unique key combining position and analytic account
    #         key = f"{position.id}_{analytic.id if analytic else 'no_analytic'}"
            
    #         if key not in position_analytic_data:
    #             position_analytic_data[key] = {
    #                 'name': position.name,
    #                 'position': position,
    #                 'analytic_account_id': analytic.id if analytic else False,
    #                 'analytic_account_name': analytic.name if analytic else '',
    #                 'monthly': {}
    #             }
                
    #             # Initialize monthly data
    #             for month in months:
    #                 month_key = month['date'].strftime('%Y-%m')
    #                 position_analytic_data[key]['monthly'][month_key] = {
    #                     'planned': 0.0,
    #                     'actual': 0.0
    #                 }
            
    #         # Calculate monthly PLANNED amounts
    #         for month in months:
    #             month_key = month['date'].strftime('%Y-%m')
                
    #             # Check overlap
    #             line_start = max(line.date_from, month['start'])
    #             line_end = min(line.date_to, month['end'])
                
    #             if line_start <= line_end:
    #                 total_days = (line.date_to - line.date_from).days + 1
    #                 month_days = (line_end - line_start).days + 1
                    
    #                 if total_days > 0:
    #                     ratio = month_days / total_days
    #                     position_analytic_data[key]['monthly'][month_key]['planned'] += abs(line.planned_amount * ratio)
        
    #     # Get ACTUAL amounts for each position-analytic combination
    #     for key, data in position_analytic_data.items():
    #         position = data['position']
    #         analytic_id = data['analytic_account_id']
    #         account_ids = position.account_ids.ids
            
    #         if account_ids:
    #             # Get actual amounts with analytic filter
    #             for month in months:
    #                 month_key = month['date'].strftime('%Y-%m')
                    
    #                 # Build domain for account.move.line
    #                 aml_domain = [
    #                     ('account_id', 'in', account_ids),
    #                     ('date', '>=', month['start']),
    #                     ('date', '<=', month['end']),
    #                     ('company_id', '=', self.company_id.id),
    #                     ('parent_state', '=', 'posted'),
    #                 ]
                    
    #                 # Add analytic account filter if exists
    #                 if analytic_id:
    #                     aml_domain.append(('analytic_account_id', '=', analytic_id))
    #                 else:
    #                     aml_domain.append(('analytic_account_id', '=', False))
                    
    #                 # Get account move lines
    #                 move_lines = self.env['account.move.line'].search(aml_domain)
                    
    #                 # Calculate balance
    #                 balance = sum(move_lines.mapped('balance'))
                    
    #                 # Store actual amount
    #                 position_analytic_data[key]['monthly'][month_key]['actual'] = abs(balance)
        
    #     # Now group by position name for display (combining analytic accounts)
    #     position_grouped = {}
        
    #     for key, data in position_analytic_data.items():
    #         pos_name = data['name']
            
    #         # If analytic account exists, append it to the name
    #         if data['analytic_account_name']:
    #             display_name = f"{pos_name} - {data['analytic_account_name']}"
    #         else:
    #             display_name = pos_name
            
    #         if display_name not in position_grouped:
    #             position_grouped[display_name] = {
    #                 'name': display_name,
    #                 'position': data['position'],
    #                 'monthly': {}
    #             }
                
    #             # Initialize
    #             for month in months:
    #                 month_key = month['date'].strftime('%Y-%m')
    #                 position_grouped[display_name]['monthly'][month_key] = {
    #                     'planned': 0.0,
    #                     'actual': 0.0
    #                 }
            
    #         # Add amounts
    #         for month_key, amounts in data['monthly'].items():
    #             position_grouped[display_name]['monthly'][month_key]['planned'] += amounts['planned']
    #             position_grouped[display_name]['monthly'][month_key]['actual'] += amounts['actual']
        
    #     # Categorize and add to result
    #     for display_name, data in position_grouped.items():
    #         position = data['position']
    #         category = self._categorize_position(position)
            
    #         # Only add if there's data
    #         has_data = any(
    #             month_data['planned'] > 0 or month_data['actual'] > 0 
    #             for month_data in data['monthly'].values()
    #         )
            
    #         if has_data:
    #             item = {
    #                 'name': display_name,
    #                 'monthly': data['monthly']
    #             }
                
    #             if category == 'income':
    #                 result['revenue']['items'].append(item)
    #                 for month_key, month_data in data['monthly'].items():
    #                     result['revenue']['totals'][month_key]['planned'] += month_data['planned']
    #                     result['revenue']['totals'][month_key]['actual'] += month_data['actual']
    #             elif category == 'cogs':
    #                 result['cogs']['items'].append(item)
    #                 for month_key, month_data in data['monthly'].items():
    #                     result['cogs']['totals'][month_key]['planned'] += month_data['planned']
    #                     result['cogs']['totals'][month_key]['actual'] += month_data['actual']
    #             elif category == 'expense':
    #                 result['expenses']['items'].append(item)
    #                 for month_key, month_data in data['monthly'].items():
    #                     result['expenses']['totals'][month_key]['planned'] += month_data['planned']
    #                     result['expenses']['totals'][month_key]['actual'] += month_data['actual']
        
    #     # Sort items
    #     for category in ['revenue', 'cogs', 'expenses']:
    #         result[category]['items'].sort(key=lambda x: x['name'])
        
    #     return result

    def _categorize_position(self, position):
        """Categorize budgetary position"""
        # Check custom category if exists
        if hasattr(position, 'pnl_category') and position.pnl_category:
            if position.pnl_category in ['operating_income', 'other_income']:
                return 'income'
            elif position.pnl_category == 'cost_of_revenue':
                return 'cogs'
            else:
                return 'expense'
        
        # Categorize based on account code
        if position.account_ids:
            first_code = position.account_ids[0].code or ''
            
            # Indonesian COA standard
            if first_code.startswith('4'):  # Revenue
                return 'income'
            elif first_code.startswith('5'):  # COGS
                return 'cogs'
            elif first_code.startswith(('6', '7', '8')):  # Expenses
                return 'expense'
        
        # Default
        return 'expense'


class AccountBudgetPost(models.Model):
    """Extend Budgetary Position for P&L categorization"""
    _inherit = 'account.budget.post'
    
    pnl_category = fields.Selection([
        ('operating_income', 'Operating Income'),
        ('other_income', 'Other Income'), 
        ('cost_of_revenue', 'Cost of Revenue'),
        ('operating_expense', 'Operating Expense'),
        ('depreciation', 'Depreciation'),
        ('other_expense', 'Other Expense'),
    ], string='P&L Category', 
       help='Category for Profit & Loss Report classification')
    
    is_income = fields.Boolean(
        string='Is Income Account',
        compute='_compute_is_income',
        store=True,
        help='Indicates if this position represents income'
    )
    
    @api.depends('pnl_category')
    def _compute_is_income(self):
        """Compute whether this is an income category"""
        income_categories = ['operating_income', 'other_income']
        for rec in self:
            rec.is_income = rec.pnl_category in income_categories