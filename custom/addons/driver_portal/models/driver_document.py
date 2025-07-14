from odoo import models, fields, api

class DriverDocument(models.Model):
    _name = 'driver.document'
    _description = 'Driver Document'

    name = fields.Char(string='Document Name', required=True)
    driver_id = fields.Many2one('res.users', string='Driver', required=True)
    document_type = fields.Selection([
        ('license', 'Driving License'),
        ('id_card', 'ID Card'),
        ('passport', 'Passport'),
        ('vehicle_registration', 'Vehicle Registration'),
        ('insurance', 'Insurance'),
        ('other', 'Other')
    ], string='Document Type', required=True)
    attachment = fields.Binary(string='Attachment', attachment=True)
    expiration_date = fields.Date(string='Expiration Date')
    notes = fields.Text(string='Notes')
    
    # Computed fields
    is_expired = fields.Boolean(string='Is Expired', compute='_compute_is_expired')
    days_to_expiry = fields.Integer(string='Days to Expiry', compute='_compute_days_to_expiry')
    
    @api.depends('expiration_date')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for record in self:
            if record.expiration_date:
                record.is_expired = record.expiration_date < today
            else:
                record.is_expired = False
    
    @api.depends('expiration_date')
    def _compute_days_to_expiry(self):
        today = fields.Date.today()
        for record in self:
            if record.expiration_date:
                delta = record.expiration_date - today
                record.days_to_expiry = delta.days
            else:
                record.days_to_expiry = 0
    
    # Constraints
    @api.constrains('expiration_date')
    def _check_expiration_date(self):
        for record in self:
            if record.expiration_date and record.expiration_date < fields.Date.today():
                # This is just a warning, not preventing save
                pass


    
    @api.model
    def _cron_check_document_expiry(self):
        """Cron job to check for expiring documents and send notifications"""
        # Find documents expiring in 30 days
        expiring_soon = self.search([
            ('expiration_date', '!=', False),
            ('days_to_expiry', '<=', 30),
            ('days_to_expiry', '>', 0)
        ])
        
        for doc in expiring_soon:
            message = f"Your document '{doc.name}' will expire in {doc.days_to_expiry} days."
            doc.message_post(
                body=message,
                partner_ids=[doc.driver_id.partner_id.id],
                message_type='notification'
            )
        
        # Find expired documents
        expired_docs = self.search([('is_expired', '=', True)])
        for doc in expired_docs:
            message = f"Your document '{doc.name}' has expired. Please renew it."
            doc.message_post(
                body=message,
                partner_ids=[doc.driver_id.partner_id.id],
                message_type='notification'
            )

