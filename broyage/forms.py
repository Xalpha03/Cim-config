from django import forms
from .models import *


class totaliForm(forms.ModelForm):
        
    class Meta:
        model = Totaliseur
        fields = ['post', 'compt_debut', 'clinker_debut', 'gypse_debut', 'dolomite_debut', 'date']
        widgets = {
            'post': forms.Select(attrs={
                'class': 'form-select'
            }),
            'site': forms.Select(attrs={
                'class': 'form-select'
            }),
            'compt_debut': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Entrez le compteur broyeur pour commencer'
            }),
            'clinker_debut': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Entrez le totaliseur clinker pour commencer'
            }),
            'gypse_debut': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Entrez le totaliseur gypse pour commencer'
            }),
            'dolomite_debut': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Entrez le totaliseur dolomite pour commencer'
            }),
            'date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                },
                format='%Y-%m-%d'  # ✅ format ISO compatible avec HTML5
            ),
        }
        
        
class broyageForm(forms.ModelForm):

    class Meta:
        model = Broyage
        fields = ('compt_fin', 'clinker_fin', 'gypse_fin', 'dolomite_fin')
        widgets = {
            
            'compt_fin': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'clinker_fin': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'gypse_fin': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'dolomite_fin': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
        }