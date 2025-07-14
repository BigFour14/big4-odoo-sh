
from odoo import http
from odoo.http import request
import json

class DriverPortalController(http.Controller):

    @http.route('/driver/portal', type='http', auth='user', website=True)
    def driver_portal_home(self, **kwargs):
        """Driver portal home page"""
        user = request.env.user
        trips = request.env['driver.trip'].search([('driver_id', '=', user.id)])
        documents = request.env['driver.document'].search([('driver_id', '=', user.id)])
        
        values = {
            'user': user,
            'trips': trips,
            'documents': documents,
            'pending_trips': trips.filtered(lambda t: t.status == 'pending'),
            'expired_documents': documents.filtered(lambda d: d.is_expired),
        }
        return request.render('driver_portal.portal_home', values)

    @http.route('/driver/trips', type='http', auth='user', website=True)
    def driver_trips(self, **kwargs):
        """Driver trips page"""
        user = request.env.user
        trips = request.env['driver.trip'].search([('driver_id', '=', user.id)])
        
        values = {
            'trips': trips,
        }
        return request.render('driver_portal.trips_page', values)

    @http.route('/driver/documents', type='http', auth='user', website=True)
    def driver_documents(self, **kwargs):
        """Driver documents page"""
        user = request.env.user
        documents = request.env['driver.document'].search([('driver_id', '=', user.id)])
        
        values = {
            'documents': documents,
        }
        return request.render('driver_portal.documents_page', values)

    @http.route('/api/driver/trips', type='json', auth='user', methods=['GET'])
    def api_get_trips(self, **kwargs):
        """API endpoint to get driver trips"""
        user = request.env.user
        trips = request.env['driver.trip'].search([('driver_id', '=', user.id)])
        
        trip_data = []
        for trip in trips:
            trip_data.append({
                'id': trip.id,
                'name': trip.name,
                'vehicle': trip.vehicle_id.name if trip.vehicle_id else '',
                'start_location': trip.start_location,
                'end_location': trip.end_location,
                'scheduled_datetime': trip.scheduled_datetime.isoformat() if trip.scheduled_datetime else '',
                'status': trip.status,
                'duration': trip.duration,
            })
        
        return {'trips': trip_data}

    @http.route('/api/driver/trip/start', type='json', auth='user', methods=['POST'])
    def api_start_trip(self, trip_id, **kwargs):
        """API endpoint to start a trip"""
        trip = request.env['driver.trip'].browse(trip_id)
        if trip.driver_id.id == request.env.user.id:
            trip.action_start_trip()
            return {'success': True, 'message': 'Trip started successfully'}
        return {'success': False, 'message': 'Unauthorized'}

    @http.route('/api/driver/trip/complete', type='json', auth='user', methods=['POST'])
    def api_complete_trip(self, trip_id, **kwargs):
        """API endpoint to complete a trip"""
        trip = request.env['driver.trip'].browse(trip_id)
        if trip.driver_id.id == request.env.user.id:
            trip.action_complete_trip()
            return {'success': True, 'message': 'Trip completed successfully'}
        return {'success': False, 'message': 'Unauthorized'}

    @http.route('/api/driver/documents', type='json', auth='user', methods=['GET'])
    def api_get_documents(self, **kwargs):
        """API endpoint to get driver documents"""
        user = request.env.user
        documents = request.env['driver.document'].search([('driver_id', '=', user.id)])
        
        doc_data = []
        for doc in documents:
            doc_data.append({
                'id': doc.id,
                'name': doc.name,
                'document_type': doc.document_type,
                'expiration_date': doc.expiration_date.isoformat() if doc.expiration_date else '',
                'is_expired': doc.is_expired,
                'days_to_expiry': doc.days_to_expiry,
            })
        
        return {'documents': doc_data}

