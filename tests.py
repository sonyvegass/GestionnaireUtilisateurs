import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from auth import Auth
from users import UserManager
from session_manager import SessionManager
from region_manager import RegionManager
from validators import DataValidator
from main import Application

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.auth = Auth()
        
    def test_generer_mot_de_passe(self):
        """Test de la génération de mot de passe"""
        password = self.auth.generer_mot_de_passe()
        # Vérifier la longueur
        self.assertEqual(len(password), 12)
        # Vérifier la présence des différents types de caractères
        self.assertTrue(any(c.islower() for c in password))
        self.assertTrue(any(c.isupper() for c in password))
        self.assertTrue(any(c.isdigit() for c in password))
        self.assertTrue(any(c in "!@#$%^&*" for c in password))
        
    def test_hasher_mot_de_passe(self):
        """Test du hashage de mot de passe"""
        password = "Test123!"
        hashed = self.auth.hasher_mot_de_passe(password)
        # Vérifier que le hash est toujours le même pour le même mot de passe
        self.assertEqual(hashed, self.auth.hasher_mot_de_passe(password))
        # Vérifier la longueur du hash SHA-256
        self.assertEqual(len(hashed), 64)
        
    @patch('auth.get_connection')
    def test_creer_super_admin(self, mock_get_connection):
        """Test de création du super admin"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Pas de super admin existant
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        password = self.auth.creer_super_admin()
        self.assertIsNotNone(password)
        mock_cursor.execute.assert_called()
        
    @patch('auth.get_connection')
    def test_connexion(self, mock_get_connection):
        """Test de la connexion utilisateur"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock the login attempts check
        mock_cursor.fetchone.side_effect = [
            # First fetchone call for tentatives_connexion
            {
                'tentatives': 0,
                'derniere_tentative': datetime.now()
            },
            # Second fetchone call for user credentials
            {
                'login': 'test_user',
                'password': self.auth.hasher_mot_de_passe('test_password'),
                'role': 'utilisateur',
                'region': 'Paris',
                'prenom': 'Test',
                'nom': 'User',
                'expiration': datetime.now() + timedelta(days=1)
            }
        ]
        
        with patch('builtins.input', side_effect=['test_user', 'test_password']):
            self.assertTrue(self.auth.connexion())
            
        # Verify the correct SQL queries were executed
        mock_cursor.execute.assert_any_call(
            """
                SELECT tentatives, derniere_tentative 
                FROM tentatives_connexion 
                WHERE login = %s
            """, 
            ('test_user',)
        )
        
        mock_cursor.execute.assert_any_call(
            """
                SELECT * FROM utilisateurs 
                WHERE login = %s AND expiration > NOW()
            """,
            ('test_user',)
        )

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.session_manager = SessionManager()
        
    @patch('session_manager.get_connection')
    def test_create_session(self, mock_get_connection):
        """Test de création de session"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        session = self.session_manager.create_session("test_user")
        self.assertIsNotNone(session)
        self.assertEqual(self.session_manager.current_user, "test_user")
        
    def test_is_session_valid(self):
        """Test de validité de session"""
        self.assertFalse(self.session_manager.is_session_valid())
        
    @patch('session_manager.get_connection')
    def test_end_session(self, mock_get_connection):
        """Test de fin de session"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        self.session_manager.current_user = "test_user"
        self.session_manager.session_token = "test_token"
        self.session_manager.end_session()
        
        self.assertIsNone(self.session_manager.current_user)
        self.assertIsNone(self.session_manager.session_token)

class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.auth = Auth()
        self.user_manager = UserManager(self.auth)
        
    @patch('users.get_connection')
    def test_afficher_utilisateurs(self, mock_get_connection):
        """Test d'affichage des utilisateurs"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simuler des données de test
        mock_cursor.fetchall.return_value = [{
            'nom': 'Test',
            'prenom': 'User',
            'login': 'tuser',
            'role': 'utilisateur',
            'region': 'Paris',
            'expiration': datetime.now() + timedelta(days=90)
        }]
        
        with patch.object(self.auth.session_manager, 'is_session_valid', return_value=True):
            with patch.object(self.auth.session_manager, 'get_current_user_role', 
                            return_value={'role': 'admin', 'region': 'Paris'}):
                self.user_manager.afficher_utilisateurs()
                
    @patch('users.get_connection')
    def test_ajouter_utilisateur(self, mock_get_connection):
        """Test d'ajout d'utilisateur"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # Login n'existe pas
        
        with patch.object(self.auth.session_manager, 'is_session_valid', return_value=True):
            with patch.object(self.auth.session_manager, 'get_current_user_role', 
                            return_value={'role': 'admin', 'region': 'Paris'}):
                with patch('builtins.input', side_effect=['Doe', 'John', 'utilisateur', 'Paris']):
                    result = self.user_manager.ajouter_utilisateur()
                    self.assertIsNotNone(result)

class TestRegionManager(unittest.TestCase):
    def setUp(self):
        self.auth = Auth()
        self.region_manager = RegionManager(self.auth)
        
    @patch('region_manager.get_connection')
    def test_ajouter_region(self, mock_get_connection):
        """Test d'ajout de région"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        with patch.object(self.auth.session_manager, 'is_session_valid', return_value=True):
            with patch.object(self.auth.session_manager, 'get_current_user_role', 
                            return_value={'role': 'super_admin', 'region': None}):
                self.assertTrue(self.region_manager.ajouter_region("Toulouse"))
                
    @patch('region_manager.get_connection')
    def test_lister_regions(self, mock_get_connection):
        """Test de listage des régions"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            ('Paris', 10, 2, 8),
            ('Rennes', 5, 1, 4)
        ]
        
        with patch.object(self.auth.session_manager, 'is_session_valid', return_value=True):
            self.region_manager.lister_regions()

class TestDataValidator(unittest.TestCase):
    def setUp(self):
        self.validator = DataValidator()
        
    def test_valider_nom(self):
        """Test de validation des noms"""
        self.assertTrue(self.validator.valider_nom("Jean")[0])
        self.assertTrue(self.validator.valider_nom("Jean-Pierre")[0])
        self.assertFalse(self.validator.valider_nom("J")[0])
        self.assertFalse(self.validator.valider_nom("123")[0])
        
    def test_valider_role(self):
        """Test de validation des rôles"""
        self.assertTrue(self.validator.valider_role("admin")[0])
        self.assertTrue(self.validator.valider_role("utilisateur")[0])
        self.assertFalse(self.validator.valider_role("invalid_role")[0])
        
    def test_valider_region(self):
        """Test de validation des régions"""
        self.assertTrue(self.validator.valider_region("Paris")[0])
        self.assertTrue(self.validator.valider_region("Rennes")[0])
        self.assertFalse(self.validator.valider_region("Invalid")[0])

class TestApplication(unittest.TestCase):
    def setUp(self):
        self.app = Application()
        
    @patch('builtins.input', side_effect=['1', 'D', 'Q'])
    def test_menu_navigation(self, mock_input):
        """Test de navigation dans le menu"""
        with patch('main.init_database', return_value=True):
            with patch.object(self.app.auth, 'connexion', return_value=True):
                with patch.object(self.app.auth.session_manager, 'get_current_user_role', 
                                return_value={'role': 'admin', 'region': 'Paris'}):
                    self.app.executer()
                    
    @patch('builtins.input', return_value='Q')
    def test_quit_menu(self, mock_input):
        """Test quitter le menu"""
        with patch('main.init_database', return_value=True):
            self.app.executer()
            
    @patch('builtins.input', side_effect=['7', 'R'])
    def test_gerer_regions_menu(self, mock_input):
        """Test du menu de gestion des régions"""
        with patch.object(self.app.auth.session_manager, 'get_current_user_role', 
                        return_value={'role': 'super_admin', 'region': None}):
            with patch.object(self.app.auth.session_manager, 'is_session_valid', return_value=True):
                self.app.gerer_regions()

if __name__ == '__main__':
    unittest.main()