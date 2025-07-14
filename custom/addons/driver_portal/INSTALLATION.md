
# Driver Portal Module - Installation Guide

## System Requirements

### Odoo Version
- Odoo 18.0 or later
- Community or Enterprise edition

### Dependencies
- Base module (pre-installed)
- Fleet module (install if not already present)

### Server Requirements
- Python 3.8 or later
- PostgreSQL 12 or later
- Minimum 2GB RAM
- 1GB free disk space

## Pre-Installation Steps

### 1. Backup Your Database
```bash
pg_dump your_database_name > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Install Fleet Module (if not installed)
1. Go to Apps menu in Odoo
2. Search for "Fleet"
3. Click Install on the Fleet module
4. Wait for installation to complete

### 3. Prepare Addons Directory
Ensure you have write access to your Odoo addons directory:
```bash
# For standard installation
/opt/odoo/addons/

# For development
./addons/
```

## Installation Methods

### Method 1: Manual Installation

1. **Copy Module Files**
   ```bash
   # Extract the driver_portal folder to your addons directory
   cp -r driver_portal /opt/odoo/addons/
   
   # Set proper permissions
   chown -R odoo:odoo /opt/odoo/addons/driver_portal
   chmod -R 755 /opt/odoo/addons/driver_portal
   ```

2. **Update Addons List**
   - Restart Odoo service
   - Go to Apps menu
   - Click "Update Apps List"
   - Search for "Driver Portal"

3. **Install Module**
   - Click Install on the Driver Portal module
   - Wait for installation to complete

### Method 2: Odoo.sh Installation

1. **Upload Module**
   - Compress the driver_portal folder into a ZIP file
   - Go to your Odoo.sh project
   - Upload the ZIP file to the addons directory

2. **Deploy Changes**
   - Commit and push changes
   - Deploy to your staging/production environment

3. **Install Module**
   - Access your Odoo instance
   - Go to Apps menu
   - Install the Driver Portal module

### Method 3: Development Installation

1. **Clone/Copy to Development Environment**
   ```bash
   # If using Git
   git clone <repository_url>
   
   # Or copy manually
   cp -r driver_portal /path/to/your/odoo/addons/
   ```

2. **Start Odoo with Module Path**
   ```bash
   ./odoo-bin -d your_database -i driver_portal --addons-path=./addons
   ```

## Post-Installation Configuration

### 1. Verify Installation
1. Go to Apps menu
2. Filter by "Installed"
3. Confirm "Driver Portal" appears in the list

### 2. Configure User Groups
1. Navigate to Settings > Users & Companies > Groups
2. Verify these groups exist:
   - Driver Portal User
   - Driver Portal Manager

### 3. Assign Users to Groups
1. Go to Settings > Users & Companies > Users
2. Edit user records
3. Add users to appropriate groups:
   - Drivers: "Driver Portal User"
   - Managers: "Driver Portal Manager"

### 4. Set Up Fleet Data
1. Go to Fleet > Configuration > Vehicle Models
2. Create vehicle models if needed
3. Go to Fleet > Vehicles
4. Create vehicle records
5. Assign vehicles to drivers

### 5. Configure Menu Access
1. Go to Settings > Technical > User Interface > Menu Items
2. Verify "Driver Portal" menu is visible
3. Adjust menu permissions if needed

## Testing Installation

### 1. Basic Functionality Test
1. Log in as a driver user
2. Navigate to Driver Portal menu
3. Verify dashboard loads correctly
4. Create a test trip
5. Upload a test document

### 2. Manager Functionality Test
1. Log in as a manager user
2. Access all Driver Portal menus
3. Create trips for drivers
4. Generate reports
5. Verify security rules work

### 3. API Testing (Optional)
```bash
# Test API endpoints
curl -X GET "http://your-odoo-url/api/driver/trips" \
     -H "Authorization: Bearer your-api-key"
```

## Troubleshooting

### Common Installation Issues

#### Module Not Found
**Problem**: Module doesn't appear in Apps list
**Solution**:
1. Check addons path configuration
2. Restart Odoo service
3. Update Apps list
4. Verify file permissions

#### Permission Errors
**Problem**: Access denied errors
**Solution**:
1. Check user group assignments
2. Verify security rules
3. Update module if needed

#### Database Errors
**Problem**: Installation fails with database errors
**Solution**:
1. Check PostgreSQL logs
2. Verify database permissions
3. Ensure no conflicting modules

#### Fleet Module Missing
**Problem**: Error about missing fleet dependency
**Solution**:
1. Install Fleet module first
2. Restart Odoo
3. Try installing Driver Portal again

### Performance Issues

#### Slow Loading
**Problem**: Dashboard or views load slowly
**Solution**:
1. Check database indexes
2. Optimize queries if needed
3. Increase server resources

#### Memory Issues
**Problem**: Out of memory errors
**Solution**:
1. Increase server RAM
2. Optimize database
3. Check for memory leaks

## Uninstallation

### 1. Backup Data
Export any important data before uninstalling:
```sql
-- Export trip data
COPY driver_trip TO '/tmp/driver_trips.csv' DELIMITER ',' CSV HEADER;

-- Export document data
COPY driver_document TO '/tmp/driver_documents.csv' DELIMITER ',' CSV HEADER;
```

### 2. Uninstall Module
1. Go to Apps menu
2. Find "Driver Portal" module
3. Click Uninstall
4. Confirm uninstallation

### 3. Clean Up Files
```bash
# Remove module files
rm -rf /opt/odoo/addons/driver_portal
```

## Support

### Getting Help
- Check the README.md file for usage instructions
- Review Odoo logs for error messages
- Contact system administrator for server issues

### Reporting Issues
When reporting issues, include:
- Odoo version
- Module version
- Error messages
- Steps to reproduce
- System configuration

### Contact Information
For technical support:
- Email: support@example.com
- Documentation: See README.md
- Issue Tracker: [Project Repository]

## Maintenance

### Regular Tasks
1. **Weekly**: Check for expired documents
2. **Monthly**: Review trip reports
3. **Quarterly**: Update user permissions
4. **Annually**: Archive old data

### Updates
1. Backup database before updates
2. Test updates in staging environment
3. Deploy to production during maintenance window
4. Verify functionality after update

### Monitoring
- Monitor system logs for errors
- Check database performance
- Review user feedback
- Track module usage statistics

