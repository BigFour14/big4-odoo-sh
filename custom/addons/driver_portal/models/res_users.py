
from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    driver_trip_ids = fields.One2many(
        'driver.trip', 'driver_id', string='Driver Trips'
    )
    driver_document_ids = fields.One2many(
        'driver.document', 'driver_id', string='Driver Documents'
    )


