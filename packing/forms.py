from django import forms
from . models import *

class PackingForm(forms.ModelForm):
    class Meta:
        model = Packing
        exclude = ('slug', 'title', 'user', 'site')
        fields = ('post', 'livraison', 'casse', 'vrack', 'date')
        
        widgets = {
            'post':forms.Select(attrs={
                'class': 'form-select',
            }),
            
            'livraison': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
            
            'casse': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
            
            'vrack': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
            
            'date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                },
                format='%Y-%m-%d'  # ✅ format ISO compatible avec HTML5
            ),
        }


class PanneForm(forms.ModelForm):
    class Meta:
        model = Pannes
        fields = ('departement', 'start_panne', 'end_panne', 'description', 'solution')
        exclude = ('packing', 'date', 'duree', 'slug')
        
        widgets = {
            'departement': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            
            'start_panne': forms.TimeInput(attrs={
                'class': 'form-control',
            }),
            'end_panne': forms.TimeInput(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Décrivez la panne brièvement...',
            }), 
            'solution': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Décrivez la panne brièvement...',
            }), 
        }