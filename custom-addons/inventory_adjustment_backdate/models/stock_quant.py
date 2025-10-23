from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    backdate = fields.Date('Backdate')
    remarks = fields.Char('Remarks')

    def _apply_inventory(self):
        move_vals = []
        date_list = []
        if not self.user_has_groups('stock.group_stock_manager'):
            raise UserError(_('Only a stock manager can validate an inventory adjustment.'))
        for quant in self:
            # Create and validate a move so that the quant matches its `inventory_quantity`.
            if float_compare(quant.inventory_diff_quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0:
                move_vals.append(
                    quant._get_inventory_move_values(quant.inventory_diff_quantity,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     quant.location_id))
            else:
                move_vals.append(
                    quant._get_inventory_move_values(-quant.inventory_diff_quantity,
                                                     quant.location_id,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     out=True))
        moves = self.env['stock.move'].with_context(inventory_mode=False).create(move_vals)
        for quant in self:
            date_list.append(quant.backdate)
        if moves:
            for move in moves:
                move.with_context(backdate=date_list[0])._action_done()
                del(date_list[0])
        # moves.with_context(backdate=self.backdate)._action_done()
        self.location_id.write({'last_inventory_date': fields.Date.today()})
        date_by_location = {loc: loc._get_next_inventory_date() for loc in self.mapped('location_id')}
        for quant in self:
            quant.inventory_date = date_by_location[quant.location_id]
        self.write({'inventory_quantity': 0, 'user_id': False})
        self.write({'inventory_diff_quantity': 0})


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    backdate = fields.Date('Backdate')


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done()
        if res.picking_id and res.picking_id.backdate or self._context.get('backdate'):
            for move in res:
                if move.picking_id:
                    backdate = move.picking_id.backdate
                elif self._context.get('backdate'):
                    backdate = self._context.get('backdate')
                else:
                    backdate = fields.Date.today()
                move.write({'date':backdate})
                for move_line in move.move_line_ids:
                    move_line.write({'date':backdate})
                for svl in move.stock_valuation_layer_ids:
                    self._cr.execute("update stock_valuation_layer set create_date = %s where id = %s", [backdate, svl.id])
        return res

    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        # move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, svl_id, description)
        # if self.picking_id.backdate:
        #     date = self.picking_id.backdate
        # elif self._context.get('backdate'):
        #     date = self._context.get('backdate')
        # else:
        #     date = self.env.context.get('force_period_date')
        # return {
        #     'journal_id': journal_id,
        #     'line_ids': move_lines,
        #     'date': date,
        #     'ref': description,
        #     'stock_move_id': self.id,
        #     'stock_valuation_layer_ids': [(6, None, [svl_id])],
        #     'move_type': 'entry',
        # }
        val = super(StockMove, self)._prepare_account_move_vals(credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost)
        if self.picking_id.backdate:
            val['date'] = self.picking_id.backdate
        elif self._context.get('backdate'):
            val['date'] = self._context.get('backdate')
        return val