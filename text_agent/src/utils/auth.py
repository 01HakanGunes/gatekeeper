import json

def authenticate(employee_name):
    """
    Authenticate employee by checking if the name exists in the employees database.
    """
    try:
        with open("./data/db/employees.json", "r") as f:
            employees = json.load(f)

        # Check if an employee with the given name exists
        return any(emp["name"] == employee_name for emp in employees)
    except FileNotFoundError:
        return False

def _find_employee(employee_name):
    """
    A helper function to find an employee's data by name.
    """
    try:
        with open("./data/db/employees.json", "r") as f:
            employees = json.load(f)

        # Find the employee and return their data
        for employee in employees:
            if employee["name"] == employee_name:
                return employee
        return None  # Return None if the employee is not found
    except FileNotFoundError:
        return None

def get_permissions(employee_name):
    """
    Get the permissions for a specific employee.
    """
    employee = _find_employee(employee_name)
    if employee:
        return employee.get("permissions")
    return None

def get_greeting(employee_name):
    """
    Get the personalized greeting for a specific employee.
    """
    employee = _find_employee(employee_name)
    if employee:
        return employee.get("greeting")
    return None

def authorize_door_access(employee_name, sid, camera_sid_map):
    """
    Check if authenticated employee has permission for the door associated with their session.

    Args:
        employee_name (str): Name of the authenticated employee
        sid (str): Socket.IO session identifier
        camera_sid_map (dict): Mapping of sid -> camera_id (restructured format)

    Returns:
        bool: True if employee has access to the session's door, False otherwise
    """
    employee = _find_employee(employee_name)
    if not employee:
        return False

    # Get employee's allowed camera IDs
    permissions = employee.get("permissions", {})
    allowed_cameras = permissions.get("doors", [])

    # Get camera_id for this session
    session_camera_id = camera_sid_map.get(sid)
    if not session_camera_id:
        return False

    # Check if employee has permission for this camera
    return session_camera_id in allowed_cameras
