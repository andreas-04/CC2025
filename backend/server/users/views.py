from rest_framework import viewsets
from .models import UserProfile
from .serializers import UserProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import UserRegistrationSerializer, LoginSerializer
from canvas.serializers import DailyPuzzleSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth import logout
from canvas.models import DailyPuzzle
from rest_framework.decorators import action

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def get_puzzle(self, request, pk=None):
        user = self.get_object()
        puzzles = DailyPuzzle.objects.filter(user=user)
        serializer = DailyPuzzleSerializer(puzzles, many=True)
        return Response(serializer.data)

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Auto-login after registration
            from django.contrib.auth import login
            login(request, user)
            
            token = Token.objects.create(user=user)

            # Create response
            response = Response({
                "message": "User registered successfully.",
                "token": token.key,
                "sessionid": request.session.session_key,

            }, status=status.HTTP_201_CREATED)



            return response
    
class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(request, username=username, password=password)

            if user:
                # For browser sessions
                from django.contrib.auth import login
                login(request, user)
                
                # For API token authentication
                token, created = Token.objects.get_or_create(user=user)
                response = Response({
                            "message": "Login successful",
                            "token": token.key,
                            "sessionid": request.session.session_key,
                            "user_id": user.id
                        }, status=status.HTTP_200_OK)

                # # Set user_id as a cookie
                # response.set_cookie(
                #     key="user_id",
                #     value=user.id,
                #     httponly=False, 
                #     samesite="None",  # Modify as needed
                #     max_age=60*60*24*7 ,
                #     secure=False, # 1 week expiration
                # )

                return response

            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class LogoutView(APIView):
    def post(self, request):
        # Delete the token
        request.user.auth_token.delete()
        
        # Clear session
        logout(request)
        
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)