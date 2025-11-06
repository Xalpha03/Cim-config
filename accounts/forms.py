# forms.py
import re
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profil


class UserProfilForm(forms.ModelForm):
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    # email = forms.EmailField(
    #     label="Adresse email",
    #     widget=forms.EmailInput(attrs={'class': 'form-control'})
    # )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirm_password = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Profil
        fields = ['poste', 'site',]
        widgets = {
           
            'poste': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'site': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            
        }
    
    def clean_site(self):
        site = self.cleaned_data.get('site')
        if not site:
            raise ValidationError("Le site est obligatoire.")
        return site

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')

        # Vérifie la longueur minimale
        if len(password) < 8:
            raise ValidationError("Le mot de passe doit contenir au moins 8 caractères.")

        # Vérifie la présence d'une majuscule
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Le mot de passe doit contenir au moins une lettre majuscule.")

        # Vérifie la présence d'une minuscule
        if not re.search(r"[a-z]", password):
            raise ValidationError("Le mot de passe doit contenir au moins une lettre minuscule.")

        # Vérifie la présence d'un chiffre
        if not re.search(r"[0-9]", password):
            raise ValidationError("Le mot de passe doit contenir au moins un chiffre.")

        # Vérifie la présence d’un caractère spécial
        if not re.search(r"[@$!%*#?&]", password):
            raise ValidationError("Le mot de passe doit contenir au moins un caractère spécial (@, $, !, %, *, #, ?, &).")

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        # Création du User
        username = self.cleaned_data['username']
        username = username[0].upper() + username[1:]
        user = User.objects.create_user(
            username=username,
            password=self.cleaned_data['password'],
        )
        
        # profil = Profil(
        #     user=user,
        #     poste=self.cleaned_data['poste'],
        #     site=self.cleaned_data['site'],
        #     role=self.cleaned_data['role']
        # )
    

        # Création du Profil lié
        profil = super().save(commit=False)
        profil.user = user
        if commit:
            profil.save()
        return profil
