from getpass import getpass
from werkzeug.security import generate_password_hash

password = getpass('New shopkeeper password (5+ characters): ')
if len(password) < 5:
    raise SystemExit('Password must have at least 5 characters.')
print(generate_password_hash(password, method='scrypt'))
