from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User
from .forms import UserProfilForm
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect

class UserCreate(CreateView):
    model = User
    form_class = UserProfilForm
    template_name = "account/register.html"
    success_url = reverse_lazy("account:login")  # redirection après succès

    def form_valid(self, form):
        response = super().form_valid(form)
        self.created_user = form.instance.user  # récupère le user lié au profil
        return response
    
    
    
class UserLoginView(LoginView):
    template_name = 'account/login.html'
    redirect_authenticated_user = True  # évite de reconnecter un utilisateur déjà connecté
    def get_success_url(self):
        user=self.request.user
        section = user.profil.poste
        print(section)
        
        if not user.is_authenticated:
            return reverse_lazy('account:login')
        
        if not hasattr(user, 'profil'):
            messages.warning(self.request, "Votre compte n'a pas encore de profil associé.")
            return reverse_lazy('home-view')
        
        messages.success(self.request, "Vous avez été connecté.")
        
        if section == 'broyage':
            return reverse_lazy('broyage:broyage-home')  # ou dashboard selon le rôle
        elif section == 'packing':
            return reverse_lazy('packing:packing-home')
        else:
            return reverse_lazy('home-view')
    
    
def custom_logout(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('account:login')
