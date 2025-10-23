from odoo import _, api, fields, models


class FleetRequestTicketWizard(models.Model):
    _name = 'fleet.request.ticket.wizard'
    _description = 'Fleet Request Ticket Wizard'

    description = fields.Html('Description')