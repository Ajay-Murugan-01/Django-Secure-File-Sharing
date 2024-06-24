from rest_framework import serializers
from django.contrib import auth
from django.db.models import Q
import uuid

# import models 
from django.contrib.auth.models import User
from .models import File


# User serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        many = True
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'is_active', 'date_joined', 'last_login']


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id' ,'file', 'uploaded_by', 'uploaded_at']


# signup serializer
class SignupSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        required=True,
        min_length=1,
        max_length=80,)
       
    last_name = serializers.CharField(
        required=False,
        min_length=1,
        max_length=80,
    )
    # email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    email = serializers.EmailField(
        required=True,
    )
    password = serializers.CharField(required=True, min_length=8)
  
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email' ,'password')

  
    def create(self, validated_data):
        # return "Done"
        # self.clean()
        email = validated_data.get("email")
        # if email:
        username = email.split("@")[0]
        # Check if the username already exists
        count = User.objects.filter(username__startswith=username).count()
        
        if count > 0:
            # If it exists, append "-1" to the username and try again
            # username = f"{username}-{count}"
            username = f"{username}{count + 1}"
        else:
            myuuid = uuid.uuid4()
            validated_data["username"] = str(myuuid)
        
        validated_data["username"] = username
        
        user_data = {
            "username": username,
            "password": validated_data["password"],
            "email": validated_data["email"],
            # "is_email_verified":True
        }

        auth_user = User.objects.create_user(**user_data)

        return auth_user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=250, write_only=True, required=True)
    password = serializers.CharField(min_length=4, max_length=64, write_only=True, required=True)
    remember_me = serializers.BooleanField(required=False)

    def login(self, **kwargs):
        username = self.validated_data['username']
        password = self.validated_data['password']

        user = User.objects.filter(Q(username=username) | Q(email=username)).first()

        print("user:", user.id)

        if not user:
            raise serializers.ValidationError({"message": ["Wrong credentials"]})
                
        user = auth.authenticate(username=user.username, password=password)
        if not user:
            raise serializers.ValidationError({"message": ["Wrong credentials"]})
        
        return user        