import argparse
import getpass
from auth import create_user

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Créer un compte local ou réinitialiser son mot de passe.')
    parser.add_argument('username')
    parser.add_argument('--reset-password', action='store_true')
    args = parser.parse_args()
    password = getpass.getpass('Mot de passe (12 caractères minimum) : ')
    if password != getpass.getpass('Confirmer : '): raise SystemExit('Les mots de passe diffèrent.')
    try: create_user(args.username, password, args.reset_password)
    except Exception as e: raise SystemExit(str(e))
    print('Compte mis à jour.' if args.reset_password else 'Compte créé.')
