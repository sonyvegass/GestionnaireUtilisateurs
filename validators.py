import re
from datetime import datetime

class DataValidator:
    NOM_MIN_LENGTH = 2
    NOM_MAX_LENGTH = 50
    ROLES_VALIDES = ['super_admin', 'admin', 'utilisateur']
    REGIONS_VALIDES = ['Paris', 'Rennes', 'Strasbourg', 'Grenoble', 'Nantes']
    
    @staticmethod
    def valider_nom(nom):
        """Valide un nom ou prénom"""
        if not isinstance(nom, str):
            return False, "Le nom doit être une chaîne de caractères"
            
        nom = nom.strip()
        if len(nom) < DataValidator.NOM_MIN_LENGTH:
            return False, f"Le nom doit contenir au moins {DataValidator.NOM_MIN_LENGTH} caractères"
            
        if len(nom) > DataValidator.NOM_MAX_LENGTH:
            return False, f"Le nom doit contenir au maximum {DataValidator.NOM_MAX_LENGTH} caractères"
            
        if not re.match(r'^[A-Za-zÀ-ÿ\-\s]+$', nom):
            return False, "Le nom ne doit contenir que des lettres, tirets et espaces"
            
        return True, "Nom valide"
        
    @staticmethod
    def valider_role(role):
        """Valide un rôle utilisateur"""
        if not isinstance(role, str):
            return False, "Le rôle doit être une chaîne de caractères"
            
        role = role.lower()
        if role not in DataValidator.ROLES_VALIDES:
            return False, f"Le rôle doit être l'un des suivants : {', '.join(DataValidator.ROLES_VALIDES)}"
            
        return True, "Rôle valide"
        
    @staticmethod
    def valider_region(region):
        """Valide une région"""
        if not isinstance(region, str):
            return False, "La région doit être une chaîne de caractères"
            
        if region not in DataValidator.REGIONS_VALIDES:
            return False, f"La région doit être l'une des suivantes : {', '.join(DataValidator.REGIONS_VALIDES)}"
            
        return True, "Région valide"
        
    @staticmethod
    def valider_date(date_str):
        """Valide une date au format YYYY-MM-DD"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True, "Date valide"
        except ValueError:
            return False, "Format de date invalide. Utilisez YYYY-MM-DD"
            
    @classmethod
    def valider_utilisateur(cls, data):
        """Valide toutes les données d'un utilisateur"""
        erreurs = []
        
        valide, message = cls.valider_nom(data.get('nom', ''))
        if not valide:
            erreurs.append(f"Nom invalide: {message}")
            
        valide, message = cls.valider_nom(data.get('prenom', ''))
        if not valide:
            erreurs.append(f"Prénom invalide: {message}")
            
        valide, message = cls.valider_role(data.get('role', ''))
        if not valide:
            erreurs.append(f"Rôle invalide: {message}")
            
        if 'region' in data and data['region']:
            valide, message = cls.valider_region(data['region'])
            if not valide:
                erreurs.append(f"Région invalide: {message}")
                
        return not bool(erreurs), erreurs