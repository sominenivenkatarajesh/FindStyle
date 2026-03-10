from .models import Cart, Profile

def cart_processor(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(username=request.user.username)
            return {'cart': cart}
        except Cart.DoesNotExist:
            return {'cart': None}
    return {'cart': None}

def profile_processor(request):
    if request.user.is_authenticated:
        profile = Profile.objects.filter(username=request.user.username).first()
        return {'profile': profile}
    return {'profile': None}
