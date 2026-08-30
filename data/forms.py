from django import forms

from .models import Article, In, Out, StockEntry


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ('name', 'reference', 'description', 'price', 'quantity', 'reorder_level')
        labels = {
            'name': 'Nom de l’article', 'reference': 'Référence interne', 'description': 'Description',
            'price': 'Coût unitaire', 'quantity': 'Stock initial', 'reorder_level': 'Seuil de réapprovisionnement',
        }
        help_texts = {
            'name': 'Ex. Haricots Mecka 1 kg.',
            'reference': 'Code facultatif pour retrouver rapidement l’article.',
            'description': 'Précisez le format, la couleur ou toute information utile.',
            'price': 'Montant payé pour une unité en stock.',
            'quantity': 'Nombre d’unités disponibles au départ.',
            'reorder_level': 'Une alerte apparaît lorsque le stock atteint ce nombre.',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Description facultative'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'quantity': forms.NumberInput(attrs={'min': '1'}),
            'reorder_level': forms.NumberInput(attrs={'min': '0'}),
        }


class IncomeForm(forms.ModelForm):
    class Meta:
        model = In
        fields = ('article', 'quantity', 'unit_price', 'date')
        labels = {'article': 'Article vendu', 'quantity': 'Quantité vendue', 'unit_price': 'Prix de vente unitaire', 'date': 'Date de la vente'}
        help_texts = {
            'article': 'Choisissez l’article sorti du stock.',
            'quantity': 'Le stock est réduit automatiquement après validation.',
            'unit_price': 'Montant payé par le client pour une unité.',
            'date': 'Le mois de la vente est déterminé automatiquement par cette date.',
        }
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'inputmode': 'decimal'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'inputmode': 'decimal'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Out
        fields = ('description', 'amount', 'date')
        labels = {'description': 'Motif de la dépense', 'amount': 'Montant dépensé', 'date': 'Date de la dépense'}
        help_texts = {
            'description': 'Ex. transport, loyer, emballage ou salaire.',
            'amount': 'La somme sera prélevée sur les recettes disponibles.',
            'date': 'Le mois est déterminé automatiquement par cette date.',
        }
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Ex. transport, loyer…'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class StockEntryForm(forms.ModelForm):
    class Meta:
        model = StockEntry
        fields = ('article', 'quantity', 'unit_cost', 'date', 'note')
        labels = {'article': 'Article à réapprovisionner', 'quantity': 'Quantité ajoutée', 'unit_cost': 'Nouveau coût unitaire', 'date': 'Date de réception', 'note': 'Note / fournisseur'}
        help_texts = {
            'article': 'Choisissez l’article dont le stock doit augmenter.',
            'quantity': 'Nombre d’unités reçues dans ce nouvel arrivage.',
            'unit_cost': 'Coût d’achat d’une unité de cet arrivage.',
            'date': 'Date à laquelle la marchandise est entrée en boutique.',
            'note': 'Facultatif : fournisseur, numéro de bon ou remarque.',
        }
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.TextInput(attrs={'placeholder': 'Bon de livraison, fournisseur…'}),
        }
