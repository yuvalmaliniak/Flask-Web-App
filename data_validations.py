def validate_register_data(data):
    if not isinstance(data, dict):
        return False, "Invalid data format. Expected a JSON object."

    if 'username' not in data or 'password' not in data:
        return False, "Missing required fields: username and password."

    if not isinstance(data['username'], str) or not isinstance(data['password'], str):
        return False, "Username and password must be strings."

    if len(data['username']) < 3 or len(data['password']) < 6:
        return False, "Username must be at least 3 characters and password at least 6 characters long."

    return True, "Data is valid."