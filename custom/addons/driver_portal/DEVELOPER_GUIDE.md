
# Driver Portal Module - Developer Guide

## Architecture Overview

The Driver Portal module follows Odoo's MVC (Model-View-Controller) architecture and integrates seamlessly with the existing Fleet module. It extends core functionality while maintaining compatibility with Odoo 18 standards.

### Module Structure
```
driver_portal/
├── models/          # Data models and business logic
├── views/           # XML view definitions
├── controllers/     # HTTP controllers and API endpoints
├── security/        # Access rights and security rules
├── data/           # Demo data and cron jobs
├── reports/        # Report templates
└── static/         # CSS, JavaScript, and assets
```

## Data Models

### Driver Trip Model (`driver.trip`)

**Purpose**: Manages driver trip assignments and tracking

**Key Fields**:
- `name`: Trip identifier (Char, required)
- `driver_id`: Reference to res.users (Many2one, required)
- `vehicle_id`: Reference to fleet.vehicle (Many2one, required)
- `start_location`: Starting point (Char)
- `end_location`: Destination (Char)
- `scheduled_datetime`: Planned start time (Datetime)
- `actual_start_datetime`: Actual start time (Datetime)
- `actual_end_datetime`: Actual end time (Datetime)
- `status`: Trip status (Selection)
- `duration`: Calculated trip duration (Float, computed)
- `notes`: Additional information (Text)

**Computed Fields**:
```python
@api.depends('actual_start_datetime', 'actual_end_datetime')
def _compute_duration(self):
    for record in self:
        if record.actual_start_datetime and record.actual_end_datetime:
            delta = record.actual_end_datetime - record.actual_start_datetime
            record.duration = delta.total_seconds() / 3600.0
        else:
            record.duration = 0.0
```

**Business Methods**:
- `action_start_trip()`: Starts a trip and sets actual start time
- `action_complete_trip()`: Completes a trip and sets actual end time
- `action_cancel_trip()`: Cancels a trip

**Constraints**:
- Start time must be before end time
- Only assigned driver can modify trip

### Driver Document Model (`driver.document`)

**Purpose**: Manages driver-related documents and expiration tracking

**Key Fields**:
- `name`: Document name (Char, required)
- `driver_id`: Reference to res.users (Many2one, required)
- `document_type`: Document category (Selection, required)
- `attachment`: File attachment (Binary)
- `expiration_date`: Document expiry date (Date)
- `is_expired`: Expiration status (Boolean, computed)
- `days_to_expiry`: Days until expiration (Integer, computed)
- `notes`: Additional notes (Text)

**Computed Fields**:
```python
@api.depends('expiration_date')
def _compute_is_expired(self):
    today = fields.Date.today()
    for record in self:
        if record.expiration_date:
            record.is_expired = record.expiration_date < today
        else:
            record.is_expired = False
```

**Cron Methods**:
- `_cron_check_document_expiry()`: Daily check for expiring documents

## Views and User Interface

### XML View Structure

**Tree Views**: List display with filtering and sorting
```xml
<tree string="Driver Trips" decoration-info="status=='pending'">
    <field name="name"/>
    <field name="driver_id"/>
    <field name="vehicle_id"/>
    <field name="status"/>
</tree>
```

**Form Views**: Detailed record editing with grouped fields
```xml
<form string="Driver Trip">
    <header>
        <button name="action_start_trip" type="object" string="Start Trip"/>
        <field name="status" widget="statusbar"/>
    </header>
    <sheet>
        <group>
            <field name="name"/>
            <field name="driver_id"/>
        </group>
    </sheet>
</form>
```

**Dashboard View**: Custom overview for drivers
- Real-time trip status
- Document expiration alerts
- Quick action buttons

### CSS Customization

**File**: `static/src/css/driver_portal.css`

**Key Classes**:
- `.driver_portal_dashboard`: Main dashboard styling
- `.driver_portal_card`: Card-based layout
- `.driver_trip_status_*`: Status-specific styling
- `.driver_document_expired`: Expired document highlighting

### JavaScript Enhancements

**File**: `static/src/js/driver_portal.js`

**Features**:
- Real-time dashboard updates
- AJAX-based quick actions
- Automatic refresh functionality
- Mobile-responsive interactions

## Controllers and API

### Web Controllers

**File**: `controllers/main.py`

**Routes**:
- `/driver/portal`: Main portal homepage
- `/driver/trips`: Trip management page
- `/driver/documents`: Document management page

**Example Controller**:
```python
@http.route('/driver/portal', type='http', auth='user', website=True)
def driver_portal_home(self, **kwargs):
    user = request.env.user
    trips = request.env['driver.trip'].search([('driver_id', '=', user.id)])
    return request.render('driver_portal.portal_home', {'trips': trips})
```

### JSON API Endpoints

**Authentication**: User session required

**Endpoints**:
- `GET /api/driver/trips`: Retrieve driver trips
- `POST /api/driver/trip/start`: Start a trip
- `POST /api/driver/trip/complete`: Complete a trip
- `GET /api/driver/documents`: Retrieve driver documents

**Example API Method**:
```python
@http.route('/api/driver/trips', type='json', auth='user')
def api_get_trips(self, **kwargs):
    user = request.env.user
    trips = request.env['driver.trip'].search([('driver_id', '=', user.id)])
    return {'trips': [trip.read() for trip in trips]}
```

## Security Implementation

### User Groups

**Driver Portal User**:
- Basic access to own records
- Can view and update trips
- Can manage own documents
- Cannot create trips (assigned by managers)

**Driver Portal Manager**:
- Full access to all records
- Can create and assign trips
- Can generate reports
- Can manage all driver documents

### Record Rules

**Own Records Rule**:
```xml
<record id="driver_trip_rule_own_records" model="ir.rule">
    <field name="name">Driver Trip: Own Records Only</field>
    <field name="model_id" ref="model_driver_trip"/>
    <field name="domain_force">[('driver_id', '=', user.id)]</field>
    <field name="groups" eval="[(4, ref('group_driver_portal_user'))]"/>
</record>
```

### Model Access Rights

**CSV Format**: `security/ir.model.access.csv`
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_driver_trip_user,driver.trip.user,model_driver_trip,group_driver_portal_user,1,1,0,0
```

## Reports and Analytics

### QWeb Reports

**Trip Report**: Detailed trip information
- Trip details and timeline
- Driver and vehicle information
- Duration and status analysis

**Expired Documents Report**: Document compliance tracking
- Expired document listing
- Expiration timeline
- Driver-wise breakdown

### Report Templates

**Structure**:
```xml
<template id="report_driver_trip_document">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="o">
            <div class="page">
                <h2>Driver Trip Report</h2>
                <!-- Report content -->
            </div>
        </t>
    </t>
</template>
```

## Database Schema

### Table Relationships

```
res_users (drivers)
    ├── driver_trip (one-to-many)
    └── driver_document (one-to-many)

fleet_vehicle
    └── driver_trip (one-to-many)
```

### Indexes and Performance

**Recommended Indexes**:
- `driver_trip.driver_id`
- `driver_trip.status`
- `driver_document.driver_id`
- `driver_document.expiration_date`

## Customization Guidelines

### Adding New Fields

1. **Model Extension**:
```python
class DriverTrip(models.Model):
    _inherit = 'driver.trip'
    
    custom_field = fields.Char(string='Custom Field')
```

2. **View Updates**:
```xml
<record id="view_driver_trip_form_inherit" model="ir.ui.view">
    <field name="name">driver.trip.form.inherit</field>
    <field name="model">driver.trip</field>
    <field name="inherit_id" ref="driver_portal.view_driver_trip_form"/>
    <field name="arch" type="xml">
        <field name="notes" position="after">
            <field name="custom_field"/>
        </field>
    </field>
</record>
```

### Creating Custom Reports

1. **Template Creation**:
```xml
<template id="custom_report_template">
    <!-- Custom report structure -->
</template>
```

2. **Report Action**:
```xml
<record id="action_custom_report" model="ir.actions.report">
    <field name="name">Custom Report</field>
    <field name="model">driver.trip</field>
    <field name="report_type">qweb-pdf</field>
    <field name="report_name">module.custom_report_template</field>
</record>
```

### API Extensions

**Custom Endpoints**:
```python
@http.route('/api/driver/custom', type='json', auth='user')
def custom_api_method(self, **kwargs):
    # Custom API logic
    return {'result': 'success'}
```

## Testing and Debugging

### Unit Testing

**Test Structure**:
```python
from odoo.tests.common import TransactionCase

class TestDriverTrip(TransactionCase):
    def setUp(self):
        super(TestDriverTrip, self).setUp()
        self.driver = self.env['res.users'].create({
            'name': 'Test Driver',
            'login': 'test_driver'
        })
    
    def test_trip_creation(self):
        trip = self.env['driver.trip'].create({
            'name': 'Test Trip',
            'driver_id': self.driver.id
        })
        self.assertEqual(trip.status, 'pending')
```

### Debugging Tips

1. **Enable Developer Mode**: Settings > Activate Developer Mode
2. **Check Logs**: Monitor Odoo server logs for errors
3. **Use Debugger**: Add `import pdb; pdb.set_trace()` for breakpoints
4. **Database Queries**: Use `_logger.info()` to log SQL queries

### Performance Optimization

**Query Optimization**:
- Use `search_count()` instead of `len(search())`
- Implement proper indexing
- Use `read()` for bulk data retrieval
- Avoid N+1 query problems

**Memory Management**:
- Use `with_context()` for temporary context changes
- Clear large recordsets when done
- Use generators for large datasets

## Deployment Considerations

### Production Deployment

1. **Database Migration**: Test schema changes in staging
2. **Asset Compilation**: Ensure CSS/JS assets are properly compiled
3. **Security Review**: Verify all security rules are in place
4. **Performance Testing**: Load test with realistic data volumes

### Maintenance

**Regular Tasks**:
- Monitor cron job execution
- Review security logs
- Update documentation
- Backup critical data

**Version Control**:
- Use Git for source code management
- Tag releases appropriately
- Maintain changelog
- Document breaking changes

## Best Practices

### Code Quality

1. **Follow PEP 8**: Python coding standards
2. **Use Type Hints**: Improve code readability
3. **Write Docstrings**: Document methods and classes
4. **Handle Exceptions**: Proper error handling

### Security

1. **Validate Input**: Always validate user input
2. **Use CSRF Protection**: For web forms
3. **Implement Rate Limiting**: For API endpoints
4. **Regular Security Audits**: Review access controls

### Performance

1. **Optimize Queries**: Use appropriate ORM methods
2. **Cache Results**: For expensive computations
3. **Lazy Loading**: Load data only when needed
4. **Monitor Performance**: Use profiling tools

## Contributing

### Development Workflow

1. **Fork Repository**: Create personal fork
2. **Create Branch**: Feature-specific branches
3. **Write Tests**: Ensure code coverage
4. **Submit PR**: Pull request with description
5. **Code Review**: Address feedback
6. **Merge**: After approval

### Coding Standards

- Follow Odoo development guidelines
- Use meaningful variable names
- Write comprehensive tests
- Document complex logic
- Maintain backward compatibility

This developer guide provides comprehensive information for extending and maintaining the Driver Portal module. For specific implementation questions, refer to the Odoo documentation or contact the development team.

