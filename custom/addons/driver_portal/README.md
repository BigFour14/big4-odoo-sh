
# Driver Portal Module for Odoo 18

## Overview

The Driver Portal module is a comprehensive solution designed for Odoo 18 that provides drivers with a dedicated portal to manage their trips, vehicles, and documents. This module enhances the fleet management capabilities of Odoo by adding driver-specific functionality and self-service features.

## Features

### Core Functionality
- **Trip Management**: Drivers can view, start, and complete their assigned trips
- **Document Management**: Upload and manage driver documents with expiration tracking
- **Dashboard**: Comprehensive overview of driver activities and status
- **Mobile API**: RESTful API endpoints for mobile application integration
- **Automated Notifications**: Automatic alerts for trip updates and document expiration

### Models
1. **Driver Trip (`driver.trip`)**
   - Trip name and description
   - Driver and vehicle assignment
   - Start and end locations
   - Scheduled and actual times
   - Trip status (pending, in progress, completed, cancelled)
   - Duration calculation
   - Notes and comments

2. **Driver Document (`driver.document`)**
   - Document name and type
   - File attachment
   - Expiration date tracking
   - Automatic expiry notifications
   - Document categories (license, ID, passport, insurance, etc.)

### Security Features
- **User Groups**: Driver Portal User and Driver Portal Manager
- **Record Rules**: Drivers can only access their own records
- **Field-level Security**: Appropriate access controls for sensitive data
- **API Authentication**: Secure API endpoints for mobile access

### Reports
- **Trip Report**: Detailed trip information and statistics
- **Expired Documents Report**: List of expired or expiring documents
- **PDF Generation**: Professional report formatting

## Installation

### Prerequisites
- Odoo 18.0 or later
- Fleet module installed and configured
- Base module (included by default)

### Installation Steps
1. Copy the `driver_portal` folder to your Odoo addons directory
2. Update the addons list in Odoo
3. Install the "Driver Portal" module from the Apps menu
4. Configure user groups and permissions as needed

## Configuration

### User Setup
1. Navigate to Settings > Users & Companies > Users
2. Assign users to the "Driver Portal User" group
3. For managers, assign the "Driver Portal Manager" group

### Fleet Integration
1. Ensure the Fleet module is installed
2. Create vehicle records in Fleet > Vehicles
3. Assign vehicles to drivers as needed

### Security Groups
- **Driver Portal User**: Can view and manage own trips and documents
- **Driver Portal Manager**: Full access to all driver portal features

## Usage

### For Drivers
1. Access the Driver Portal from the main menu
2. View the dashboard for an overview of trips and documents
3. Manage trips: start, complete, or cancel assigned trips
4. Upload and manage personal documents
5. Receive notifications for important updates

### For Managers
1. Create and assign trips to drivers
2. Monitor driver activities and trip progress
3. Generate reports on driver performance
4. Manage document compliance and expiration

### API Endpoints
- `GET /api/driver/trips` - Retrieve driver trips
- `POST /api/driver/trip/start` - Start a trip
- `POST /api/driver/trip/complete` - Complete a trip
- `GET /api/driver/documents` - Retrieve driver documents

## Technical Details

### Dependencies
- `base`: Core Odoo functionality
- `fleet`: Vehicle and fleet management

### File Structure
```
driver_portal/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py
├── data/
│   ├── driver_portal_cron.xml
│   └── driver_portal_data.xml
├── models/
│   ├── __init__.py
│   ├── driver_document.py
│   ├── driver_trip.py
│   └── res_users.py
├── reports/
│   ├── driver_trip_report.xml
│   └── expired_documents_report.xml
├── security/
│   ├── driver_portal_security.xml
│   └── ir.model.access.csv
├── static/src/
│   ├── css/driver_portal.css
│   └── js/driver_portal.js
└── views/
    ├── driver_dashboard_views.xml
    ├── driver_document_views.xml
    └── driver_trip_views.xml
```

### Database Tables
- `driver_trip`: Stores trip information
- `driver_document`: Stores document information
- Extended `res_users`: Adds driver-specific fields

## Customization

### Adding New Document Types
1. Edit `models/driver_document.py`
2. Add new selection options to the `document_type` field
3. Update views if necessary

### Custom Trip Statuses
1. Modify the `status` field in `models/driver_trip.py`
2. Update related views and logic

### Additional Fields
1. Add fields to the respective model files
2. Update views to display new fields
3. Modify security rules if needed

## Troubleshooting

### Common Issues
1. **Module not appearing**: Check addons path and update apps list
2. **Permission errors**: Verify user group assignments
3. **API not working**: Check authentication and CORS settings

### Support
For technical support or customization requests, please contact the development team.

## License

This module is developed by Manus AI and is provided as-is for use with Odoo 18.

## Version History

### Version 1.0
- Initial release
- Core trip and document management
- Dashboard and reporting features
- Mobile API integration
- Security and access controls

## Contributing

To contribute to this module:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Author

**Manus AI**
- Specialized in Odoo development and customization
- Expert in fleet management and driver portal solutions

