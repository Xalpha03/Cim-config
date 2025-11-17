from django import forms
from .models import *
from datetime import timedelta
from django.apps import apps

Post = apps.get_model('packing', 'Post')


class totaliForm(forms.ModelForm):
    long_shift = forms.BooleanField(
        required=False,
        label="Cocher uniquement si c'est post de 12h"
    )    
    class Meta:
        model = Totaliseur
        fields = ['post', 'compt_debut', 'clinker_debut', 'gypse_debut', 'dolomite_debut', 'date', 'long_shift']
        widgets = {
            'long_shift': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            
            'post':forms.Select(attrs={
                'class': 'form-select',
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
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Vérifie si la case est cochée dans les données POST
        long_shift_checked = False
        if self.data:
            long_shift_checked = str(self.data.get("long_shift")).lower() in ("on", "true", "1")

        # Filtrer le queryset du champ "post"
        if long_shift_checked:
            self.fields["post"].queryset = Post.objects.filter(duree_post=timedelta(hours=12))
        else:
            self.fields["post"].queryset = Post.objects.filter(duree_post=timedelta(hours=8))
        
        
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
        
        
        
        
        
