# models/sale_order_import.py
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import xlrd
import xlsxwriter
from io import BytesIO
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class SaleOrderImportWizard(models.TransientModel):
    _name = 'sale.order.import.wizard'
    _description = 'Sales Order Excel Import'
    
    file_data = fields.Binary(
        string='Excel File',
        required=True,
        help='Upload Excel file with sales order data'
    )
    file_name = fields.Char('File Name')
    
    # Import options
    import_type = fields.Selection([
        ('create', 'Create New Orders'),
        ('update', 'Update Existing Orders'),
    ], string='Import Type', default='create', required=True)
    
    skip_validation = fields.Boolean(
        string='Skip Validation',
        help='Skip validation for faster import (use with caution)'
    )
    
    # Results
    imported_count = fields.Integer('Imported Orders', readonly=True)
    failed_count = fields.Integer('Failed Orders', readonly=True)
    log_text = fields.Text('Import Log', readonly=True)
    
    def download_template(self):
        """Generate and download Excel template"""
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Create sheets
        header_sheet = workbook.add_worksheet('Order Headers')
        lines_sheet = workbook.add_worksheet('Order Lines')
        master_sheet = workbook.add_worksheet('Master Data')
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        required_format = workbook.add_format({
            'bold': True,
            'bg_color': '#FFE699',
            'border': 1
        })
        
        optional_format = workbook.add_format({
            'bg_color': '#D9E2F3',
            'border': 1
        })
        
        # === HEADER SHEET ===
        header_columns = [
            ('Order Reference*', 20, True),
            ('Customer Code*', 15, True),
            ('Customer Name', 30, False),
            ('Order Date*', 12, True),
            ('Delivery Date', 12, False),
            ('Payment Terms', 20, False),
            ('Salesperson', 20, False),
            ('Currency', 10, False),
            ('Notes', 40, False),
            ('Customer PO', 20, False),
            ('Pricelist', 20, False),
            ('Warehouse', 15, False),
        ]
        
        # Write header columns
        for col, (name, width, required) in enumerate(header_columns):
            header_sheet.set_column(col, col, width)
            if required:
                header_sheet.write(0, col, name, required_format)
            else:
                header_sheet.write(0, col, name, optional_format)
        
        # Sample data
        header_sheet.write(1, 0, 'SO/2025/001')
        header_sheet.write(1, 1, 'CUST001')
        header_sheet.write(1, 2, 'PT Pertamina')
        header_sheet.write(1, 3, '2025-01-15')
        header_sheet.write(1, 4, '2025-02-15')
        header_sheet.write(1, 5, '30 Days')
        header_sheet.write(1, 6, 'John Doe')
        header_sheet.write(1, 7, 'IDR')
        header_sheet.write(1, 8, 'Urgent order for valve replacement')
        
        # === LINES SHEET ===
        line_columns = [
            ('Order Reference*', 20, True),
            ('Line No*', 10, True),
            ('Product Code*', 15, True),
            ('Product Name', 30, False),
            ('Description', 40, False),
            ('Quantity*', 12, True),
            ('UoM', 10, False),
            ('Unit Price*', 15, True),
            ('Discount %', 12, False),
            ('Tax', 15, False),
            ('Analytic Account', 20, False),
            ('Delivery Date', 12, False),
        ]
        
        # Write line columns
        for col, (name, width, required) in enumerate(line_columns):
            lines_sheet.set_column(col, col, width)
            if required:
                lines_sheet.write(0, col, name, required_format)
            else:
                lines_sheet.write(0, col, name, optional_format)
        
        # Sample lines
        sample_lines = [
            ('SO/2025/001', 1, 'VALVE-001', 'Ball Valve 6"', 'Ball Valve Stainless Steel 6 inch', 10, 'Unit', 4000000, 5, 'PPN 11%'),
            ('SO/2025/001', 2, 'VALVE-002', 'Gate Valve 4"', 'Gate Valve Carbon Steel 4 inch', 5, 'Unit', 3000000, 0, 'PPN 11%'),
            ('SO/2025/001', 3, 'GASKET-001', 'Gasket Set', 'Gasket set for valve installation', 20, 'Set', 150000, 10, 'PPN 11%'),
        ]
        
        for row, line_data in enumerate(sample_lines, start=1):
            for col, value in enumerate(line_data):
                lines_sheet.write(row, col, value)
        
        # === MASTER DATA SHEET ===
        master_sheet.write(0, 0, 'REFERENCE DATA', header_format)
        master_sheet.merge_range(0, 0, 0, 3, 'REFERENCE DATA', header_format)
        
        # Customers
        master_sheet.write(2, 0, 'Customer Codes', header_format)
        master_sheet.write(2, 1, 'Customer Names', header_format)
        
        customers = self.env['res.partner'].search([
            ('customer_rank', '>', 0),
            ('active', '=', True)
        ], limit=100)
        
        for idx, customer in enumerate(customers, start=3):
            master_sheet.write(idx, 0, customer.ref or customer.id)
            master_sheet.write(idx, 1, customer.name)
        
        # Products
        master_sheet.write(2, 3, 'Product Codes', header_format)
        master_sheet.write(2, 4, 'Product Names', header_format)
        
        products = self.env['product.product'].search([
            ('sale_ok', '=', True),
            ('active', '=', True)
        ], limit=100)
        
        for idx, product in enumerate(products, start=3):
            master_sheet.write(idx, 3, product.default_code or '')
            master_sheet.write(idx, 4, product.name)
        
        # Instructions
        instructions_sheet = workbook.add_worksheet('Instructions')
        instructions = [
            "SALES ORDER IMPORT INSTRUCTIONS",
            "",
            "1. GENERAL RULES:",
            "   - Fields marked with * are mandatory",
            "   - Yellow columns are required",
            "   - Blue columns are optional",
            "   - Do not modify column headers",
            "   - Date format: YYYY-MM-DD",
            "",
            "2. ORDER HEADERS TAB:",
            "   - One row per sales order",
            "   - Order Reference must be unique",
            "   - Customer Code must exist in system",
            "",
            "3. ORDER LINES TAB:",
            "   - Multiple rows per order (one-to-many)",
            "   - Order Reference must match header",
            "   - Line numbers should be sequential",
            "   - Product Code must exist in system",
            "",
            "4. IMPORT PROCESS:",
            "   - System will validate all data first",
            "   - Orders are created in draft state",
            "   - Check import log for any errors",
            "",
            "5. COMMON ERRORS:",
            "   - Missing mandatory fields",
            "   - Invalid customer or product codes",
            "   - Duplicate order references",
            "   - Invalid date formats",
        ]
        
        for idx, instruction in enumerate(instructions):
            instructions_sheet.write(idx, 0, instruction)
        
        workbook.close()
        output.seek(0)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'sales_order_import_template.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
    
    def action_import(self):
        """Main import function"""
        self.ensure_one()
        
        if not self.file_data:
            raise UserError(_('Please upload an Excel file'))
        
        # Decode file
        try:
            file_content = base64.b64decode(self.file_data)
            book = xlrd.open_workbook(file_contents=file_content)
        except Exception as e:
            raise UserError(_('Invalid Excel file: %s') % str(e))
        
        # Check required sheets
        if 'Order Headers' not in book.sheet_names():
            raise UserError(_('Sheet "Order Headers" not found'))
        if 'Order Lines' not in book.sheet_names():
            raise UserError(_('Sheet "Order Lines" not found'))
        
        # Read data
        headers_data = self._read_headers_sheet(book.sheet_by_name('Order Headers'))
        lines_data = self._read_lines_sheet(book.sheet_by_name('Order Lines'))
        
        # Validate data
        if not self.skip_validation:
            self._validate_import_data(headers_data, lines_data)
        
        # Process import
        results = self._process_import(headers_data, lines_data)
        
        # Update wizard with results
        self.write({
            'imported_count': results['success'],
            'failed_count': results['failed'],
            'log_text': '\n'.join(results['log'])
        })
        
        # Return view with results
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'show_results': True}
        }
    
    def _read_headers_sheet(self, sheet):
        """Read order headers from Excel sheet"""
        headers = []
        
        # Skip header row
        for row_idx in range(1, sheet.nrows):
            row = sheet.row_values(row_idx)
            
            # Skip empty rows
            if not any(row):
                continue
            
            header_data = {
                'reference': str(row[0]).strip() if row[0] else '',
                'customer_code': str(row[1]).strip() if row[1] else '',
                'customer_name': str(row[2]).strip() if len(row) > 2 and row[2] else '',
                'order_date': self._parse_date(row[3]) if len(row) > 3 else False,
                'delivery_date': self._parse_date(row[4]) if len(row) > 4 else False,
                'payment_terms': str(row[5]).strip() if len(row) > 5 and row[5] else '',
                'salesperson': str(row[6]).strip() if len(row) > 6 and row[6] else '',
                'currency': str(row[7]).strip() if len(row) > 7 and row[7] else 'IDR',
                'notes': str(row[8]).strip() if len(row) > 8 and row[8] else '',
                'customer_po': str(row[9]).strip() if len(row) > 9 and row[9] else '',
                'row_number': row_idx + 1
            }
            
            headers.append(header_data)
        
        return headers
    
    def _read_lines_sheet(self, sheet):
        """Read order lines from Excel sheet"""
        lines = []
        
        # Skip header row
        for row_idx in range(1, sheet.nrows):
            row = sheet.row_values(row_idx)
            
            # Skip empty rows
            if not any(row):
                continue
            
            line_data = {
                'order_reference': str(row[0]).strip() if row[0] else '',
                'line_no': int(row[1]) if row[1] else 0,
                'product_code': str(row[2]).strip() if row[2] else '',
                'product_name': str(row[3]).strip() if len(row) > 3 and row[3] else '',
                'description': str(row[4]).strip() if len(row) > 4 and row[4] else '',
                'quantity': float(row[5]) if len(row) > 5 and row[5] else 0,
                'uom': str(row[6]).strip() if len(row) > 6 and row[6] else '',
                'unit_price': float(row[7]) if len(row) > 7 and row[7] else 0,
                'discount': float(row[8]) if len(row) > 8 and row[8] else 0,
                'tax': str(row[9]).strip() if len(row) > 9 and row[9] else '',
                'analytic': str(row[10]).strip() if len(row) > 10 and row[10] else '',
                'delivery_date': self._parse_date(row[11]) if len(row) > 11 else False,
                'row_number': row_idx + 1
            }
            
            lines.append(line_data)
        
        return lines
    
    def _parse_date(self, date_value):
        """Parse date from Excel"""
        if not date_value:
            return False
        
        try:
            if isinstance(date_value, float):
                # Excel date number
                date_tuple = xlrd.xldate_as_tuple(date_value, 0)
                return datetime(*date_tuple).strftime('%Y-%m-%d')
            else:
                # String date
                return fields.Date.to_date(str(date_value))
        except:
            return False
    
    def _validate_import_data(self, headers, lines):
        """Validate import data before processing"""
        errors = []
        
        # Check for duplicate references
        references = [h['reference'] for h in headers]
        duplicates = set([x for x in references if references.count(x) > 1])
        if duplicates:
            errors.append(f"Duplicate order references found: {', '.join(duplicates)}")
        
        # Validate headers
        for header in headers:
            row = header['row_number']
            
            # Required fields
            if not header['reference']:
                errors.append(f"Row {row}: Order reference is required")
            if not header['customer_code']:
                errors.append(f"Row {row}: Customer code is required")
            if not header['order_date']:
                errors.append(f"Row {row}: Order date is required")
            
            # Check customer exists
            if header['customer_code']:
                partner = self.env['res.partner'].search([
                    ('ref', '=', header['customer_code'])
                ], limit=1)
                if not partner:
                    errors.append(f"Row {row}: Customer '{header['customer_code']}' not found")
        
        # Validate lines
        for line in lines:
            row = line['row_number']
            
            # Required fields
            if not line['order_reference']:
                errors.append(f"Lines sheet row {row}: Order reference is required")
            if not line['product_code']:
                errors.append(f"Lines sheet row {row}: Product code is required")
            if line['quantity'] <= 0:
                errors.append(f"Lines sheet row {row}: Quantity must be positive")
            
            # Check order reference exists in headers
            if line['order_reference'] not in references:
                errors.append(f"Lines sheet row {row}: Order reference '{line['order_reference']}' not found in headers")
            
            # Check product exists
            if line['product_code']:
                product = self.env['product.product'].search([
                    ('default_code', '=', line['product_code']),
                ], limit=1)
                if not product:
                    errors.append(f"Lines sheet row {row}: Product '{line['product_code']}' not found")
        
        if errors:
            raise ValidationError('\n'.join(errors[:20]))  # Show first 20 errors
    
    def _process_import(self, headers, lines):
        """Process the actual import"""
        results = {
            'success': 0,
            'failed': 0,
            'log': []
        }
        
        # Group lines by order reference
        lines_by_order = {}
        for line in lines:
            ref = line['order_reference']
            if ref not in lines_by_order:
                lines_by_order[ref] = []
            lines_by_order[ref].append(line)
        
        # Process each order
        for header in headers:
            try:
                order = self._create_sales_order(header, lines_by_order.get(header['reference'], []))
                results['success'] += 1
                results['log'].append(f"✓ Created order {order.name} (Ref: {header['reference']})")
                
            except Exception as e:
                results['failed'] += 1
                results['log'].append(f"✗ Failed {header['reference']}: {str(e)}")
                _logger.error(f"Import failed for {header['reference']}: {str(e)}")
        
        results['log'].insert(0, f"Import completed: {results['success']} success, {results['failed']} failed")
        return results
    
    @api.model
    def _create_sales_order(self, header, lines):
        """Create a single sales order with lines"""
        
        # Find customer
        partner = self.env['res.partner'].search([
            ('ref', '=', header['customer_code']),
        ], limit=1)
        
        if not partner:
            raise ValidationError(f"Customer {header['customer_code']} not found")
        
        # Find salesperson
        user = False
        if header['salesperson']:
            user = self.env['res.users'].search([
                ('name', 'ilike', header['salesperson'])
            ], limit=1)
        
        # Create order
        order_vals = {
            'partner_id': partner.id,
            'date_order': header['order_date'],
            'validity_date': header['delivery_date'],
            'client_order_ref': header['customer_po'],
            'note': header['notes'],
            'user_id': user.id if user else self.env.user.id,
        }
        
        # Add order lines
        order_lines = []
        for line in lines:
            # Find product
            product = self.env['product.product'].search([
                ('default_code', '=', line['product_code']),
            ], limit=1)
            
            if not product:
                raise ValidationError(f"Product {line['product_code']} not found")
            
            # Find UoM
            uom = product.uom_id
            if line['uom']:
                uom_search = self.env['uom.uom'].search([
                    ('name', 'ilike', line['uom'])
                ], limit=1)
                if uom_search:
                    uom = uom_search
            
            # Find taxes
            taxes = product.taxes_id
            if line['tax']:
                tax_search = self.env['account.tax'].search([
                    ('name', 'ilike', line['tax']),
                    ('type_tax_use', '=', 'sale')
                ], limit=1)
                if tax_search:
                    taxes = tax_search
            
            line_vals = {
                'sequence': line['line_no'],
                'product_id': product.id,
                'name': line['description'] or product.name,
                'product_uom_qty': line['quantity'],
                'product_uom': uom.id,
                'price_unit': line['unit_price'],
                'discount': line['discount'],
                'tax_id': [(6, 0, taxes.ids)],
            }
            
            order_lines.append((0, 0, line_vals))
        
        order_vals['order_line'] = order_lines
        
        # Create order
        order = self.env['sale.order'].create(order_vals)
        
        return order


class SaleOrderImportResults(models.TransientModel):
    """Wizard to show import results"""
    _name = 'sale.order.import.results'
    _description = 'Import Results'
    
    imported_count = fields.Integer('Successfully Imported')
    failed_count = fields.Integer('Failed')
    log_text = fields.Text('Import Log')
    
    def action_view_orders(self):
        """View imported orders"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Imported Sales Orders',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('create_date', '>=', fields.Datetime.now())],
            'target': 'current',
        }