# models/ir_actions.py
from odoo import models, api

class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'
    
    def read(self, fields=None, load='_classic_read'):
        """Override read to inject context"""
        result = super().read(fields, load)
        
        for res in result:
            if res.get('res_model') == 'purchase.order':
                if not self.env.user.has_group('purchase.group_purchase_manager'):
                    # Update context in the action
                    context = res.get('context', '{}')
                    if isinstance(context, str):
                        import ast
                        try:
                            context = ast.literal_eval(context)
                        except:
                            context = {}
                    context['create'] = False
                    res['context'] = str(context)
        
        return result
