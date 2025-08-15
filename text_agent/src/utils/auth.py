import json

def authenticate(employee_name):
    """
    Authenticate employee by checking if the name exists in the employees database.
    """
    try:
        with open("./data/db/employees.json", "r") as f:
            employees = json.load(f)

        # Check if an employee with the given name exists (case-insensitive)
        return any(emp["name"].lower() == employee_name.lower() for emp in employees)
    except FileNotFoundError:
        return False

def _find_employee(employee_name):
    """
    A helper function to find an employee's data by name.
    """
    try:
        with open("./data/db/employees.json", "r") as f:
            employees = json.load(f)

        # Find the employee and return their data (case-insensitive)
        for employee in employees:
            if employee["name"].lower() == employee_name.lower():
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

def get_authorized_doors(employee_name):
    """
    Get the list of doors/cameras that the authenticated employee has access to.

    Args:
        employee_name (str): Name of the authenticated employee

    Returns:
        list: List of camera IDs that the employee has access to, or empty list if no access
    """
    employee = _find_employee(employee_name)
    if not employee:
        return []

    # Get employee's allowed camera IDs
    permissions = employee.get("permissions", {})
    allowed_cameras = permissions.get("doors", [])

    return allowed_cameras
