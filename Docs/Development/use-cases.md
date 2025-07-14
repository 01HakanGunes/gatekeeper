# Security Gate System - Use Cases

## Core Visitor Scenarios

### **Delivery Personnel**
- **Profile**: Name, delivery company affiliation, package recipient contact
- **Decision**: Allow access after contact notification
- **Action**: Email notification sent to recipient contact person

### **Business Visitor**
- **Profile**: Name, meeting purpose, employee contact, company affiliation
- **Decision**: Allow access with low threat level and valid contact
- **Action**: Email notification to employee about visitor arrival

### **Personal/Family Visit**
- **Profile**: Name, relationship to employee, visiting purpose
- **Decision**: Allow access after employee confirmation
- **Action**: Notify employee contact via email

### **Maintenance/Service Worker**
- **Profile**: Name, service company, work purpose, maintenance contact
- **Decision**: Allow access during business hours with valid work order
- **Action**: Notify facility management and work requestor

### **Job Candidate/Interview**
- **Profile**: Name, interview purpose, HR contact, scheduled time
- **Decision**: Allow access if contact person confirms appointment
- **Action**: Email notification to HR and interviewer

## Security Threat Scenarios

### **Suspicious/Unknown Individual**
- **Profile**: Incomplete information, no valid contact, evasive responses
- **Decision**: Deny access or call security based on threat assessment
- **Action**: Security alert with visitor details and conversation log

### **Aggressive/Hostile Behavior**
- **Profile**: High threat level detected through conversation analysis
- **Decision**: Immediate security call
- **Action**: Security dispatch with priority alert

### **Unauthorized Access Attempt**
- **Profile**: No valid business purpose, invalid contact claims
- **Decision**: Deny access
- **Action**: Log incident for security review

## Advanced Use Cases

### **Employee Arrival Logging**
- **Profile**: Employee ID verification, arrival time tracking
- **Decision**: Automatic access grant for verified employees  
- **Action**: Log entry time, update office presence dashboard

### **Emergency Personnel (Police/Fire/Medical)**
- **Profile**: Official credentials, emergency nature, urgency level
- **Decision**: Immediate access grant with security notification
- **Action**: Alert security and management about emergency response

### **After-Hours Access Request**
- **Profile**: Employee or contractor, valid after-hours work justification
- **Decision**: Conditional access based on pre-authorization
- **Action**: Security monitoring activation and supervisor notification
