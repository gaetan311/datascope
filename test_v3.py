import os
import tempfile
from pathlib import Path
from streamlit.testing.v1 import AppTest

with tempfile.TemporaryDirectory() as folder:
    os.environ['DATASCOPE_AUTH_DB'] = str(Path(folder)/'users.sqlite3')
    from auth import create_user, authenticate, set_theme, connect
    create_user('testuser','UnePhrase-Test-2026!')
    assert authenticate('testuser','incorrect') is None
    assert authenticate('testuser','UnePhrase-Test-2026!')['theme']=='Light'
    set_theme('testuser','Dark')
    assert authenticate('testuser','UnePhrase-Test-2026!')['theme']=='Dark'
    create_user('blockeduser','UnePhrase-Test-2026!')
    for _ in range(5): assert authenticate('blockeduser','incorrect') is None
    assert authenticate('blockeduser','UnePhrase-Test-2026!') is None
    at=AppTest.from_file('app.py').run(timeout=60)
    assert not at.exception
    assert not at.file_uploader if hasattr(at,'file_uploader') else True
    at.text_input[0].set_value('testuser');at.text_input[1].set_value('UnePhrase-Test-2026!')
    at.button[0].click().run(timeout=60)
    assert not at.exception, str(at.exception)
    assert at.session_state['auth_user']=='testuser'
    assert at.session_state['display_theme']=='Dark'
    for group in ['Tableaux de bord','Prédiction','Studio code','Analyse']:
        next(b for b in at.button if b.key=='nav_'+group).click().run(timeout=60)
        assert not at.exception, str(at.exception)
        print('Navigation OK',group)
    next(s for s in at.selectbox if s.key=='display_theme').set_value('Light').run(timeout=60)
    assert authenticate('testuser','UnePhrase-Test-2026!')['theme']=='Light'
    at.session_state['secret_data']='donnée de test'
    next(b for b in at.button if b.key=='logout').click().run(timeout=60)
    assert not at.exception
    assert 'auth_user' not in at.session_state
    assert 'secret_data' not in at.session_state
    print('Connexion, limitation, thème persistant, navigation et déconnexion OK')
