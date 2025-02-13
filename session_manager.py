# session_manager.py
import uuid
from datetime import datetime, timedelta
from db_config import get_connection
from mysql.connector import Error

class SessionManager:
    def __init__(self):
        self.current_user = None
        self.session_token = None

    def create_session(self, login):
        """Crée une nouvelle session pour l'utilisateur"""
        conn = get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            
            # Supprimer les anciennes sessions
            cursor.execute("DELETE FROM sessions WHERE login = %s", (login,))
            
            # Créer une nouvelle session
            session_token = str(uuid.uuid4())
            expiration = datetime.now() + timedelta(hours=8)
            
            cursor.execute("""
                INSERT INTO sessions (login, session_token, expiration)
                VALUES (%s, %s, %s)
            """, (login, session_token, expiration))
            
            conn.commit()
            self.current_user = login
            self.session_token = session_token
            return session_token
            
        except Error as e:
            print(f"❌ Erreur lors de la création de session: {e}")
            return None
            
        finally:
            conn.close()

    def end_session(self):
        """Termine la session courante"""
        if not self.current_user or not self.session_token:
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM sessions 
                WHERE login = %s AND session_token = %s
            """, (self.current_user, self.session_token))
            
            conn.commit()
            self.current_user = None
            self.session_token = None
            
        except Error as e:
            print(f"❌ Erreur lors de la fermeture de session: {e}")
            
        finally:
            conn.close()

    def is_session_valid(self):
        """Vérifie si la session courante est valide"""
        if not self.current_user or not self.session_token:
            return False

        conn = get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sessions 
                WHERE login = %s AND session_token = %s 
                AND expiration > NOW()
            """, (self.current_user, self.session_token))
            
            return cursor.fetchone()[0] > 0
            
        except Error as e:
            print(f"❌ Erreur lors de la vérification de session: {e}")
            return False
            
        finally:
            conn.close()

    def get_current_user_role(self):
        """Retourne le rôle de l'utilisateur courant"""
        if not self.current_user:
            return None

        conn = get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT role, region 
                FROM utilisateurs 
                WHERE login = %s
            """, (self.current_user,))
            
            user_info = cursor.fetchone()
            return user_info if user_info else None
            
        except Error as e:
            print(f"❌ Erreur lors de la récupération du rôle: {e}")
            return None
            
        finally:
            conn.close()