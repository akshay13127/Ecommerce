from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import Customer
from django.shortcuts import redirect
from django.contrib.auth import logout, login
from .serializers import CustomerSignupSerializer, UserSerializer


class CustomerSignupView(APIView):
    def get(self, request):
        # Render the signup.html template
        return render(request, 'signup.html')

    def post(self, request):
        serializer = CustomerSignupSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            # token, _ = Token.objects.get_or_create(user=customer.user)
            # return Response({
            #     'token': token.key,
            #     'user': UserSerializer(customer.user).data
            # }, status=status.HTTP_201_CREATED)
            return redirect('product_listing') 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerLoginView(APIView):
    def get(self, request):
        # Render the signup.html template
        return render(request, 'signin.html')
    
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if user:
            # token, _ = Token.objects.get_or_create(user=user)
            login(request, user)
            return redirect('semantic_search') 
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class CustomerLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # request.user.auth_token.delete()
        logout(request)
        return redirect('customer-login')
