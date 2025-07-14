from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DriverTrip(models.Model):
    _name = 'driver.trip'
    _description = 'Driver Trip'

    name = fields.Char(string='Trip Name', required=True)
    driver_id = fields.Many2one('res.users', string='Driver', required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    start_location = fields.Char(string='Start Location')
    end_location = fields.Char(string='End Location')
    scheduled_datetime = fields.Datetime(string='Scheduled Time')
    actual_start_datetime = fields.Datetime(string='Actual Start Time')
    actual_end_datetime = fields.Datetime(string='Actual End Time')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending')
    notes = fields.Text(string='Notes')
    
    # Computed fields
    duration = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True)
    
    @api.depends('actual_start_datetime', 'actual_end_datetime')
    def _compute_duration(self):
        for record in self:
            if record.actual_start_datetime and record.actual_end_datetime:
                delta = record.actual_end_datetime - record.actual_start_datetime
                record.duration = delta.total_seconds() / 3600.0
            else:
                record.duration = 0.0
    
    # Custom methods
    def action_start_trip(self):
        self.status = 'in_progress'
        self.actual_start_datetime = fields.Datetime.now()
    
    def action_complete_trip(self):
        self.status = 'completed'
        self.actual_end_datetime = fields.Datetime.now()
    
    def action_cancel_trip(self):
        self.status = 'cancelled'
    
    # Constraints
    @api.constrains('scheduled_datetime', 'actual_start_datetime', 'actual_end_datetime')
    def _check_datetime_sequence(self):
        for record in self:
            if record.actual_start_datetime and record.actual_end_datetime:
                if record.actual_start_datetime > record.actual_end_datetime:
                    raise ValidationError("Start time cannot be after end time.")


    
    @api.model
    def create(self, vals):
        """Override create to send notification when trip is created"""
        trip = super(DriverTrip, self).create(vals)
        trip._send_trip_notification('created')
        return trip
    
    def write(self, vals):
        """Override write to send notification when status changes"""
        old_status = self.status
        result = super(DriverTrip, self).write(vals)
        if 'status' in vals and vals['status'] != old_status:
            self._send_trip_notification('status_changed')
        return result
    
    def _send_trip_notification(self, notification_type):
        """Send notification to driver about trip updates"""
        if notification_type == 'created':
            message = f"New trip '{self.name}' has been assigned to you."
        elif notification_type == 'status_changed':
            message = f"Trip '{self.name}' status changed to {self.status}."
        else:
            message = f"Trip '{self.name}' has been updated."
        
        # Send internal message to driver
        self.message_post(
            body=message,
            partner_ids=[self.driver_id.partner_id.id],
            message_type='notification'
        )

